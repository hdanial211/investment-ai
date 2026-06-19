import asyncio
import websockets
import json
import logging
import pandas as pd
import numpy as np
import joblib
import os
import sys

# Import shared state
import shared

# Features calculation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from backend.features.indicators import calculate_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "xrpusdt", "ltcusdt"]
# Binance allows listening to multiple streams using a combined stream URL:
WS_URL = "wss://stream.binance.com:9443/stream?streams=" + "/".join([f"{s}@kline_1m" for s in SYMBOLS])

MODELS = {}
for sym in SYMBOLS:
    asset = sym.replace("usdt", "").upper()
    m_path = os.path.join(os.path.dirname(__file__), "..", "models", f"xgboost_scalping_{asset}_1y.pkl")
    if os.path.exists(m_path):
        MODELS[asset] = joblib.load(m_path)
        logger.info(f"AI Model loaded for {asset}")
    else:
        logger.warning(f"AI Model for {asset} not found yet.")

# Rolling data per coin
klines_dict = {sym.replace("usdt", "").upper(): [] for sym in SYMBOLS}
MAX_KLINES = 150 # Enough for EMA_21, VWAP, etc.

def prefetch_historical_data():
    import requests
    for sym in SYMBOLS:
        coin_id = sym.replace("usdt", "").upper()
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={sym.upper()}&interval=1m&limit={MAX_KLINES}"
            res = requests.get(url, timeout=10)
            data = res.json()
            for k in data:
                klines_dict[coin_id].append({
                    'timestamp': pd.to_datetime(k[0], unit='ms'),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            logger.info(f"[{coin_id}] Prefetched {len(data)} historical candles.")
        except Exception as e:
            logger.error(f"[{coin_id}] Failed to prefetch historical data: {e}")

prefetch_historical_data()

# Hata MYR prices cache
hata_prices = {
    "ETH": 0.0,
    "BTC": 0.0,
    "SOL": 0.0,
    "LTC": 0.0,
    "XRP": 0.0
}

async def update_hata_prices_loop():
    import hata_api
    import requests
    while True:
        try:
            # 1. Fetch Hata Prices
            def fetch_prices():
                res = requests.get("https://my-api.hata.io/orderbook/api/v2/exchange-info", timeout=5)
                res.raise_for_status()
                return res.json().get("data", [])
                
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, fetch_prices)
            
            for item in data:
                base = item.get("base")
                quote = item.get("quote")
                if quote == "MYR" and base in hata_prices:
                    hata_prices[base] = float(item.get("price", 0.0))
            
            # 2. Fetch Hata Balance (Available and Frozen) & Exchange Rate
            def fetch_balance_and_rate():
                bal_res = hata_api.get_myr_balance() # returns (avail, frozen)
                rate = 4.70
                try:
                    hata_eth = hata_prices.get("ETH", 0.0)
                    if hata_eth <= 0:
                        hata_eth = hata_api.get_ticker("ETH_MYR")
                    
                    bin_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=5).json()
                    bin_eth = float(bin_res.get("price", 0.0))
                    if hata_eth > 0 and bin_eth > 0:
                        rate = hata_eth / bin_eth
                except Exception as re:
                    logger.error(f"Error calculating exchange rate: {re}")
                return bal_res, rate
                
            bal_res, rate = await loop.run_in_executor(None, fetch_balance_and_rate)
            if bal_res:
                avail, froz = bal_res
                shared.global_state["balance_myr"] = avail
                shared.global_state["frozen_myr"] = froz
            shared.global_state["usdt_myr_rate"] = rate
            
            # 3. Check Pending Orders Status
            def check_orders():
                state_changed = False
                for coin_id in shared.engine_state:
                    layers = shared.engine_state[coin_id].get("layers", [])
                    active_layers = []
                    coin_changed = False
                    for l in layers:
                        status = l.get("status", "OPEN")
                        
                        if status == "PENDING_BUY":
                            buy_id = l.get("buy_order_id")
                            if buy_id:
                                res = hata_api.get_order_status(buy_id)
                                order_data = res.get("data")
                                if order_data:
                                    order_status = order_data.get("status")
                                    if order_status == "fulfilled":
                                        logger.info(f"[{coin_id}] Buy order {buy_id} fulfilled! Verifying balance before placing Limit SELL at {l['take_profit']:.4f}")
                                        exec_qty = float(order_data.get("exec_qty", l["quantity"]))
                                        adj_qty = exec_qty * 0.996
                                        
                                        # Check actual token balance
                                        avail_bal, froz_bal = hata_api.get_token_balance(coin_id)
                                        if avail_bal < adj_qty:
                                            logger.warning(f"[{coin_id}] Cannot place Limit SELL order of size {adj_qty:.4f}. Available balance ({avail_bal:.4f}) is insufficient. Keeping layer status as OPEN to retry later.")
                                            l["status"] = "OPEN"
                                        else:
                                            sell_res = hata_api.place_limit_order(f"{coin_id}_MYR", "SELL", l["take_profit"], adj_qty)
                                            if sell_res.get("status") == "success":
                                                sell_id = sell_res.get("data", {}).get("id")
                                                l["status"] = "PENDING_SELL"
                                                l["sell_order_id"] = str(sell_id)
                                                l["hata_sell_res"] = sell_res
                                                logger.info(f"[{coin_id}] Limit SELL order {sell_id} placed successfully.")
                                            else:
                                                l["status"] = "OPEN"
                                                logger.error(f"[{coin_id}] Failed to place Limit SELL for filled buy {buy_id}: {sell_res}")
                                        coin_changed = True
                                        active_layers.append(l)
                                    elif order_status in ["cancelled", "rejected"]:
                                        logger.info(f"[{coin_id}] Buy order {buy_id} was {order_status}. Removing layer.")
                                        coin_changed = True
                                    else:
                                        active_layers.append(l)
                                else:
                                    active_layers.append(l)
                            else:
                                l["status"] = "OPEN"
                                coin_changed = True
                                active_layers.append(l)
                                
                        elif status == "PENDING_SELL":
                            sell_id = l.get("sell_order_id")
                            if sell_id:
                                res = hata_api.get_order_status(sell_id)
                                order_data = res.get("data")
                                if order_data:
                                    order_status = order_data.get("status")
                                    if order_status == "fulfilled":
                                        profit_myr = l["amount_myr"] * (l["take_profit"] / l["entry_price"])
                                        actual_pnl = profit_myr - l["amount_myr"]
                                        shared.engine_state[coin_id]["total_pnl"] += actual_pnl
                                        logger.info(f"[{coin_id}] Sell order {sell_id} fulfilled! Profit: +RM {actual_pnl:.2f}. Removing layer.")
                                        coin_changed = True
                                    elif order_status in ["cancelled", "rejected"]:
                                        logger.warning(f"[{coin_id}] Sell order {sell_id} was {order_status}! Reverting status to OPEN to retry sell.")
                                        l["status"] = "OPEN"
                                        coin_changed = True
                                        active_layers.append(l)
                                    else:
                                        active_layers.append(l)
                                else:
                                    active_layers.append(l)
                            else:
                                l["status"] = "OPEN"
                                coin_changed = True
                                active_layers.append(l)
                                
                        elif status == "OPEN":
                            exec_qty = l.get("quantity")
                            adj_qty = exec_qty * 0.996
                            
                            # Check actual token balance
                            avail_bal, froz_bal = hata_api.get_token_balance(coin_id)
                            if avail_bal < adj_qty:
                                logger.warning(f"[{coin_id}] Retry: Cannot place Limit SELL of size {adj_qty:.4f}. Available balance ({avail_bal:.4f}) is insufficient. Is another order locking the assets?")
                                active_layers.append(l)
                            else:
                                logger.info(f"[{coin_id}] Retrying Limit SELL placement for layer {l['id']}.")
                                sell_res = hata_api.place_limit_order(f"{coin_id}_MYR", "SELL", l["take_profit"], adj_qty)
                                if sell_res.get("status") == "success":
                                    sell_id = sell_res.get("data", {}).get("id")
                                    l["status"] = "PENDING_SELL"
                                    l["sell_order_id"] = str(sell_id)
                                    l["hata_sell_res"] = sell_res
                                    logger.info(f"[{coin_id}] Limit SELL order {sell_id} placed successfully on retry.")
                                else:
                                    logger.error(f"[{coin_id}] Retry Limit SELL placement failed: {sell_res}")
                                coin_changed = True
                                active_layers.append(l)
                        else:
                            active_layers.append(l)
                    
                    if coin_changed:
                        shared.engine_state[coin_id]["layers"] = active_layers
                        state_changed = True
                
                if state_changed:
                    shared.save_state()
            
            await loop.run_in_executor(None, check_orders)
            
        except Exception as e:
            logger.error(f"Failed in update_hata_prices_loop: {e}")
        await asyncio.sleep(10)

async def process_kline(coin_id, kline):
    klines = klines_dict[coin_id]
    
    # Update current price in dashboard with Hata's actual MYR price, fallback to Binance
    hata_price = hata_prices.get(coin_id, 0.0)
    if hata_price > 0:
        shared.engine_state[coin_id]["current_price"] = hata_price
    else:
        # Fallback to Binance converted price
        rate = shared.global_state.get("usdt_myr_rate", 4.70)
        shared.engine_state[coin_id]["current_price"] = float(kline['c']) * rate
    
    # If candle is closed, append to history and predict
    if kline['x']:
        klines.append({
            'timestamp': pd.to_datetime(kline['t'], unit='ms'),
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c']),
            'volume': float(kline['v'])
        })
        
        if len(klines) > MAX_KLINES:
            klines.pop(0)
            
        model = MODELS.get(coin_id)
        if len(klines) >= 50 and model is not None:
            df = pd.DataFrame(klines)
            df_feat = calculate_features(df)
            
            # Extract latest row
            latest = df_feat.iloc[-1:]
            
            # Predict
            feature_cols = [c for c in latest.columns if c not in ['timestamp', 'target', 'ai_signal', 'future_close']]
            X = latest[['open', 'high', 'low', 'close', 'volume', 'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 'Volume_ROC'] + 
                       [c for c in feature_cols if c.startswith('BB')] + 
                       [c for c in feature_cols if c.startswith('MACD')] + 
                       [c for c in feature_cols if c.startswith('STOCH')] + 
                       [c for c in feature_cols if c.startswith('ATR')] + 
                       (['VWAP_D'] if 'VWAP_D' in feature_cols else (['VWAP'] if 'VWAP' in feature_cols else []))]
            
            probs = model.predict_proba(X)
            golden_prob = float(probs[0, 1])
            
            shared.engine_state[coin_id]["confidence"] = golden_prob * 100
            
            if golden_prob > 0.60:
                logger.info(f"[{coin_id}] GOLDEN ENTRY DETECTED! Confidence: {golden_prob*100:.2f}%")
                shared.engine_state[coin_id]["last_signal"] = 1
                
                # If Auto mode is ON, execute trade
                if shared.engine_state[coin_id]["is_auto"]:
                    logger.info(f"[{coin_id}] Auto Mode ON: Processing Signal...")
                    risk_level = shared.engine_state[coin_id].get("risk_level", 1)
                    balance = shared.global_state["balance_myr"]
                    trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
                    current_price = shared.engine_state[coin_id]["current_price"]
                    
                    # 1. Determine Dynamic Strategy Settings
                    if risk_level == 3:
                        if coin_id in ['ETH', 'SOL']:
                            # Whale Imitator
                            gap_pct = 0.05
                            tp_pct = 0.02
                            max_layers = 2
                        else:
                            # Heavy Scalping
                            gap_pct = 0.01
                            tp_pct = 0.005
                            max_layers = 3
                    elif risk_level == 2:
                        # Scalp & Run / Trailing
                        gap_pct = 0.005
                        tp_pct = 0.004
                        max_layers = 5
                    else:
                        # DCA Asas
                        gap_pct = 0.02
                        tp_pct = 0.015
                        max_layers = 6
                    
                    # 2. Check if we can buy (Max Layers & Gap)
                    layers = shared.engine_state[coin_id]["layers"]
                    can_buy = True
                    
                    if len(layers) >= max_layers:
                        can_buy = False
                        logger.info(f"[{coin_id}] Max layers reached ({max_layers}). Skipping.")
                    elif len(layers) > 0:
                        last_entry = layers[-1]["entry_price"]
                        # We only buy if price dropped by gap_pct from the last entry
                        if current_price > last_entry * (1.0 - gap_pct):
                            can_buy = False
                            logger.info(f"[{coin_id}] Gap not reached yet (needs -{gap_pct*100}%). Skipping.")
                    
                    if can_buy and trade_amount <= balance and current_price > 0:
                        # Limit Order Logic for 0% Fee
                        logger.info(f"[{coin_id}] Executing LIMIT ORDER BUY size: RM {trade_amount:.2f}")
                        quantity = trade_amount / current_price
                        # CALL HATA API
                        import hata_api
                        hata_res = hata_api.place_limit_order(f"{coin_id}_MYR", "BUY", current_price, quantity)
                        
                        if hata_res.get("status") == "error":
                            logger.error(f"[{coin_id}] Hata API Error! Skipping internal layer creation. Msg: {hata_res.get('message')}")
                        else:
                            order_id = hata_res.get("data", {}).get("id")
                            layer = {
                                "id": len(layers) + 1,
                                "entry_price": current_price,
                                "amount_myr": trade_amount,
                                "quantity": quantity,
                                "take_profit": current_price * (1.0 + tp_pct),
                                "status": "PENDING_BUY",
                                "buy_order_id": str(order_id),
                                "hata_buy_res": hata_res
                            }
                            shared.engine_state[coin_id]["layers"].append(layer)
                            shared.save_state()
                            
                            logger.info(f"[{coin_id}] Layer recorded with status PENDING_BUY (ID: {order_id}). Waiting for fill.")
                        
            else:
                shared.engine_state[coin_id]["last_signal"] = 0
                
        # Layers logic is now completely handled asynchronously by the background update_hata_prices_loop
        pass


async def start_ws():
    # Start Hata MYR price update loop in background
    asyncio.create_task(update_hata_prices_loop())
    
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                logger.info(f"Connected to Binance WebSocket for Multi-Coin: {SYMBOLS}")
                while True:
                    data = await ws.recv()
                    payload = json.loads(data)
                    
                    # Combined stream payload has a 'stream' and 'data' key
                    if 'stream' in payload and 'data' in payload:
                        stream_name = payload['stream']
                        kline_data = payload['data']['k']
                        coin_id = stream_name.split('@')[0].replace('usdt', '').upper()
                        await process_kline(coin_id, kline_data)
        except Exception as e:
            logger.error(f"WebSocket Error: {e}")
            await asyncio.sleep(5)

def run():
    asyncio.run(start_ws())

if __name__ == "__main__":
    run()
