import asyncio
import websockets
import json
import logging
import pandas as pd
import numpy as np
import joblib
import os
import sys
import time
from datetime import datetime

# Import shared state
import shared

# Features calculation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from backend.features.indicators import calculate_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "xrpusdt", "ltcusdt"]
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
MAX_KLINES = 150


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


def truncate_float(val: float, decimals: int) -> float:
    """Truncate float value to a specific number of decimal places without rounding up."""
    eps = 1e-9
    factor = 10 ** decimals
    return int((val + eps) * factor) / factor


# ─────────────────────────────────────────────
# Helper: Get strategy settings by risk level
# ─────────────────────────────────────────────
def _get_strategy(coin_id: str, risk_level: int) -> dict:
    if risk_level == 3:
        return {"max_layers": 3, "tp_pct": 0.005}
    elif risk_level == 2:
        return {"max_layers": 5, "tp_pct": 0.004}
    else:
        return {"max_layers": 6, "tp_pct": 0.015}


# ─────────────────────────────────────────────
# Helper: Place next DCA layer at 1% below entry
# (Called after a SELL fills for any coin)
# ─────────────────────────────────────────────
def _place_next_layer(coin_id: str, last_entry_price: float):
    """After a SELL fills, place Limit BUY at 1% below last entry. Works for all 5 coins."""
    import hata_api

    layers = shared.engine_state[coin_id].get("layers", [])
    risk_level = shared.engine_state[coin_id].get("risk_level", 1)
    strategy = _get_strategy(coin_id, risk_level)

    if len(layers) >= strategy["max_layers"]:
        logger.info(f"[{coin_id}] Max layers ({strategy['max_layers']}) reached. Skipping auto-layer.")
        return

    # 1% below last entry price
    next_entry = round(last_entry_price * 0.99, 6)
    trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
    qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
    quantity = round(trade_amount / next_entry, qty_scale)
    take_profit = round(next_entry * (1.0 + strategy["tp_pct"]), 6)

    logger.info(f"[{coin_id}] AUTO-LAYER: Placing Limit BUY at RM{next_entry:.4f} (1% below RM{last_entry_price:.4f})")
    hata_res = hata_api.place_limit_order(f"{coin_id}_MYR", "BUY", next_entry, quantity)

    if hata_res.get("status") == "error":
        logger.error(f"[{coin_id}] Auto-layer BUY failed: {hata_res.get('message')}")
        return

    order_id = hata_res.get("data", {}).get("id")
    layer = {
        "id": len(layers) + 1,
        "entry_price": next_entry,
        "amount_myr": trade_amount,
        "quantity": quantity,
        "take_profit": take_profit,
        "status": "PENDING_BUY",
        "buy_order_id": str(order_id),
        "hata_buy_res": hata_res,
        "created_at": time.time()
    }
    shared.engine_state[coin_id]["layers"].append(layer)
    shared.save_state()
    logger.info(f"[{coin_id}] AUTO-LAYER SUCCESS: BUY order {order_id} at RM{next_entry:.4f}, TP: RM{take_profit:.4f}")


# ─────────────────────────────────────────────
# Startup Recovery: Sync all layers with Hata API
# Runs once on bot start / laptop restart
# ─────────────────────────────────────────────
async def startup_recovery():
    """Reconcile all PENDING layers in bot_state.json with actual Hata API status.
    Handles: fills missed while bot was offline, stuck orders, missing created_at."""
    import hata_api
    loop = asyncio.get_running_loop()
    logger.info("=" * 60)
    logger.info("STARTUP RECOVERY: Syncing all 5 coin layers with Hata API...")
    logger.info("=" * 60)

    def _recover():
        state_changed = False
        for coin_id in shared.engine_state:
            layers = shared.engine_state[coin_id].get("layers", [])
            if not layers:
                continue

            active_layers = []
            coin_changed = False
            logger.info(f"[{coin_id}] Recovering {len(layers)} layer(s)...")

            for l in layers:
                status = l.get("status", "OPEN")

                # ── PENDING_BUY ──────────────────────────────────
                if status == "PENDING_BUY":
                    buy_id = l.get("buy_order_id")
                    if not buy_id:
                        l["status"] = "OPEN"
                        coin_changed = True
                        active_layers.append(l)
                        continue

                    res = hata_api.get_order_status(buy_id)
                    order_data = res.get("data")
                    if not order_data:
                        # Cannot reach Hata — keep layer, check next cycle
                        active_layers.append(l)
                        continue

                    order_status = order_data.get("status")

                    if order_status == "fulfilled":
                        # Missed fill while bot was offline → place SELL now
                        logger.info(f"[{coin_id}] RECOVERY: Buy {buy_id} was already filled! Placing SELL...")
                        exec_qty = float(order_data.get("exec_qty", l["quantity"]))
                        
                        trades = order_data.get("trades", [])
                        fee_total = 0.0
                        for t in trades:
                            if t.get("fee_asset") == coin_id:
                                fee_total += float(t.get("fee", 0.0))
                                
                        if trades:
                            actual_qty = exec_qty - fee_total
                        else:
                            actual_qty = exec_qty * 0.996
                            
                        qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
                        adj_qty = truncate_float(actual_qty, qty_scale)
                        l["sell_quantity"] = adj_qty
                        
                        sell_res = hata_api.place_limit_order(f"{coin_id}_MYR", "SELL", l["take_profit"], adj_qty)
                        if sell_res.get("status") == "success":
                            sell_id = sell_res.get("data", {}).get("id")
                            l["status"] = "PENDING_SELL"
                            l["sell_order_id"] = str(sell_id)
                            l["hata_sell_res"] = sell_res
                            logger.info(f"[{coin_id}] RECOVERY: SELL {sell_id} placed at RM{l['take_profit']:.4f} with quantity {adj_qty:.4f}")
                        else:
                            l["status"] = "OPEN"
                            logger.error(f"[{coin_id}] RECOVERY: Failed to place SELL: {sell_res}")
                        coin_changed = True
                        active_layers.append(l)

                    elif order_status in ["cancelled", "rejected"]:
                        logger.info(f"[{coin_id}] RECOVERY: Buy {buy_id} was {order_status}. Removing layer.")
                        coin_changed = True
                        # Do NOT append — layer is removed

                    else:
                        # Still active in Hata — patch created_at if missing, cancel if stuck
                        if "created_at" not in l:
                            l["created_at"] = time.time()
                            coin_changed = True
                            logger.info(f"[{coin_id}] RECOVERY: Patched created_at for buy {buy_id}. Countdown starts now.")

                        age_sec = time.time() - l["created_at"]
                        if age_sec > 300:
                            logger.info(f"[{coin_id}] RECOVERY: Buy {buy_id} stuck >{age_sec/60:.1f} min. Auto-cancelling...")
                            cancel_res = hata_api.cancel_order(f"{coin_id}_MYR", buy_id)
                            logger.info(f"[{coin_id}] RECOVERY: Cancel result: {cancel_res}")
                            coin_changed = True
                            # Do NOT append — layer is removed
                        else:
                            active_layers.append(l)

                # ── PENDING_SELL ─────────────────────────────────
                elif status == "PENDING_SELL":
                    sell_id = l.get("sell_order_id")
                    if not sell_id:
                        l["status"] = "OPEN"
                        coin_changed = True
                        active_layers.append(l)
                        continue

                    res = hata_api.get_order_status(sell_id)
                    order_data = res.get("data")
                    if not order_data:
                        active_layers.append(l)
                        continue

                    order_status = order_data.get("status")

                    if order_status == "fulfilled":
                        # Missed sell fill while bot was offline
                        profit_myr = l["amount_myr"] * (l["take_profit"] / l["entry_price"])
                        actual_pnl = profit_myr - l["amount_myr"]
                        shared.engine_state[coin_id]["total_pnl"] += actual_pnl
                        logger.info(f"[{coin_id}] RECOVERY: Sell {sell_id} was already filled! PnL: +RM{actual_pnl:.2f}")
                        coin_changed = True
                        # Place next DCA layer at 1% below this entry
                        _place_next_layer(coin_id, l["entry_price"])
                        # Do NOT append — layer is complete

                    elif order_status in ["cancelled", "rejected"]:
                        logger.warning(f"[{coin_id}] RECOVERY: Sell {sell_id} was {order_status}. Reverting to OPEN.")
                        l["status"] = "OPEN"
                        coin_changed = True
                        active_layers.append(l)

                    else:
                        # Still active — keep as is
                        active_layers.append(l)

                # ── OPEN (retry) ──────────────────────────────────
                else:
                    active_layers.append(l)

            if coin_changed:
                shared.engine_state[coin_id]["layers"] = active_layers
                state_changed = True

        if state_changed:
            shared.save_state()

        logger.info("=" * 60)
        logger.info("STARTUP RECOVERY: Complete. Bot is now live.")
        logger.info("=" * 60)

    await loop.run_in_executor(None, _recover)


# ─────────────────────────────────────────────
# Main Loop: Hata prices + balance + order checks
# Runs every 60 seconds (1 minute system timer)
# ─────────────────────────────────────────────
async def update_hata_prices_loop():
    import hata_api
    import requests
    while True:
        try:
            # 1. Fetch Hata MYR Prices
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

            # 2. Fetch Balance & Exchange Rate
            def fetch_balance_and_rate():
                bal_res = hata_api.get_myr_balance()
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

            # 3. Check all pending orders for all 5 coins
            def check_orders():
                state_changed = False
                for coin_id in shared.engine_state:
                    layers = shared.engine_state[coin_id].get("layers", [])
                    active_layers = []
                    coin_changed = False

                    for l in layers:
                        status = l.get("status", "OPEN")

                        # ── PENDING_BUY ──────────────────────────
                        if status == "PENDING_BUY":
                            buy_id = l.get("buy_order_id")
                            if not buy_id:
                                l["status"] = "OPEN"
                                coin_changed = True
                                active_layers.append(l)
                                continue

                            res = hata_api.get_order_status(buy_id)
                            order_data = res.get("data")

                            if order_data:
                                order_status = order_data.get("status")

                                if order_status == "fulfilled":
                                    logger.info(f"[{coin_id}] Buy {buy_id} FILLED! Placing Limit SELL at RM{l['take_profit']:.4f}")
                                    exec_qty = float(order_data.get("exec_qty", l["quantity"]))
                                    trades = order_data.get("trades", [])
                                    fee_total = 0.0
                                    for t in trades:
                                        if t.get("fee_asset") == coin_id:
                                            fee_total += float(t.get("fee", 0.0))
                                    if trades:
                                        actual_qty = exec_qty - fee_total
                                    else:
                                        actual_qty = exec_qty * 0.996
                                    qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
                                    adj_qty = truncate_float(actual_qty, qty_scale)
                                    l["sell_quantity"] = adj_qty

                                    avail_bal, _ = hata_api.get_token_balance(coin_id)
                                    if avail_bal < adj_qty:
                                        logger.warning(f"[{coin_id}] Insufficient balance for SELL ({avail_bal:.4f} < {adj_qty:.4f}). Retry next cycle.")
                                        l["status"] = "OPEN"
                                    else:
                                        sell_res = hata_api.place_limit_order(f"{coin_id}_MYR", "SELL", l["take_profit"], adj_qty)
                                        if sell_res.get("status") == "success":
                                            sell_id = sell_res.get("data", {}).get("id")
                                            l["status"] = "PENDING_SELL"
                                            l["sell_order_id"] = str(sell_id)
                                            l["hata_sell_res"] = sell_res
                                            logger.info(f"[{coin_id}] SELL {sell_id} placed at RM{l['take_profit']:.4f}")
                                        else:
                                            l["status"] = "OPEN"
                                            logger.error(f"[{coin_id}] Failed to place SELL: {sell_res}")
                                    coin_changed = True
                                    active_layers.append(l)

                                elif order_status in ["cancelled", "rejected"]:
                                    logger.info(f"[{coin_id}] Buy {buy_id} was {order_status}. Removing layer.")
                                    coin_changed = True
                                    # Do NOT append — layer removed

                                else:
                                    # Still active — ensure created_at exists, cancel if stuck
                                    if "created_at" not in l:
                                        l["created_at"] = time.time()
                                        coin_changed = True
                                        logger.info(f"[{coin_id}] Patched created_at for buy {buy_id}. Countdown starts now.")

                                    age_sec = time.time() - l["created_at"]
                                    if age_sec > 300:
                                        logger.info(f"[{coin_id}] Buy {buy_id} stuck >{age_sec/60:.1f} min. Auto-cancelling...")
                                        cancel_res = hata_api.cancel_order(f"{coin_id}_MYR", buy_id)
                                        logger.info(f"[{coin_id}] Cancel result: {cancel_res}")
                                        coin_changed = True
                                        # Do NOT append — layer removed after cancel
                                    else:
                                        remaining = 300 - age_sec
                                        logger.info(f"[{coin_id}] Buy {buy_id} active. Auto-cancel in {remaining/60:.1f} min if unfilled.")
                                        active_layers.append(l)
                            else:
                                active_layers.append(l)

                        # ── PENDING_SELL ──────────────────────────
                        elif status == "PENDING_SELL":
                            sell_id = l.get("sell_order_id")
                            if not sell_id:
                                l["status"] = "OPEN"
                                coin_changed = True
                                active_layers.append(l)
                                continue

                            res = hata_api.get_order_status(sell_id)
                            order_data = res.get("data")

                            if order_data:
                                order_status = order_data.get("status")

                                if order_status == "fulfilled":
                                    profit_myr = l["amount_myr"] * (l["take_profit"] / l["entry_price"])
                                    actual_pnl = profit_myr - l["amount_myr"]
                                    shared.engine_state[coin_id]["total_pnl"] += actual_pnl
                                    logger.info(f"[{coin_id}] SELL {sell_id} FILLED! PnL: +RM{actual_pnl:.2f} | Total PnL: RM{shared.engine_state[coin_id]['total_pnl']:.2f}")
                                    coin_changed = True
                                    # ★ Auto-place next DCA layer at 1% below this entry (all 5 coins)
                                    _place_next_layer(coin_id, l["entry_price"])
                                    # Do NOT append — this layer is complete

                                elif order_status in ["cancelled", "rejected"]:
                                    logger.warning(f"[{coin_id}] SELL {sell_id} was {order_status}. Reverting to OPEN for retry.")
                                    l["status"] = "OPEN"
                                    coin_changed = True
                                    active_layers.append(l)

                                else:
                                    active_layers.append(l)
                            else:
                                active_layers.append(l)

                        # ── OPEN (retry sell) ─────────────────────
                        elif status == "OPEN":
                            qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
                            adj_qty = l.get("sell_quantity")
                            if adj_qty is None:
                                exec_qty = l.get("quantity", 0)
                                adj_qty = truncate_float(exec_qty * 0.996, qty_scale)
                                l["sell_quantity"] = adj_qty
                                coin_changed = True
                                
                            avail_bal, _ = hata_api.get_token_balance(coin_id)
                            if avail_bal < adj_qty:
                                logger.warning(f"[{coin_id}] Available balance ({avail_bal:.4f}) is less than planned sell quantity ({adj_qty:.4f}). Capping sell quantity.")
                                adj_qty = truncate_float(avail_bal, qty_scale)
                                l["sell_quantity"] = adj_qty
                                coin_changed = True
                                
                            if adj_qty <= 0:
                                logger.error(f"[{coin_id}] Cannot place SELL order: truncated sell quantity is 0 (balance: {avail_bal:.4f}).")
                                active_layers.append(l)
                            else:
                                logger.info(f"[{coin_id}] Retrying Limit SELL for layer {l['id']} with quantity {adj_qty:.4f}...")
                                sell_res = hata_api.place_limit_order(f"{coin_id}_MYR", "SELL", l["take_profit"], adj_qty)
                                if sell_res.get("status") == "success":
                                    sell_id = sell_res.get("data", {}).get("id")
                                    l["status"] = "PENDING_SELL"
                                    l["sell_order_id"] = str(sell_id)
                                    l["hata_sell_res"] = sell_res
                                    logger.info(f"[{coin_id}] Retry SELL {sell_id} placed.")
                                else:
                                    logger.error(f"[{coin_id}] Retry SELL failed: {sell_res}")
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

            # 4. Update system status (computed locally — no external API)
            shared.global_state["guardian_status"] = shared.compute_system_status()
            shared.global_state["guardian_last_update"] = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            logger.error(f"Failed in update_hata_prices_loop: {e}")

        # ★ 1-minute system timer (uses laptop system clock)
        await asyncio.sleep(60)


# ─────────────────────────────────────────────
# Process each 1-minute candle from Binance WS
# ─────────────────────────────────────────────
async def process_kline(coin_id, kline):
    klines = klines_dict[coin_id]

    # Update current price (Hata MYR preferred, Binance as fallback)
    hata_price = hata_prices.get(coin_id, 0.0)
    if hata_price > 0:
        shared.engine_state[coin_id]["current_price"] = hata_price
    else:
        rate = shared.global_state.get("usdt_myr_rate", 4.70)
        shared.engine_state[coin_id]["current_price"] = float(kline['c']) * rate

    # Only act on closed candles
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
            latest = df_feat.iloc[-1:]

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
                logger.info(f"[{coin_id}] GOLDEN ENTRY SIGNAL! Confidence: {golden_prob*100:.2f}%")
                shared.engine_state[coin_id]["last_signal"] = 1

                if shared.engine_state[coin_id]["is_auto"]:
                    risk_level = shared.engine_state[coin_id].get("risk_level", 1)
                    balance = shared.global_state["balance_myr"]
                    trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
                    current_price = shared.engine_state[coin_id]["current_price"]
                    strategy = _get_strategy(coin_id, risk_level)
                    layers = shared.engine_state[coin_id]["layers"]

                    can_buy = True

                    # ★ Cegah double buy: jangan letak BUY baru jika ada PENDING_BUY aktif
                    has_pending_buy = any(l.get("status") == "PENDING_BUY" for l in layers)
                    if has_pending_buy:
                        can_buy = False
                        logger.info(f"[{coin_id}] Skipping: Already has a PENDING_BUY waiting to fill.")

                    if len(layers) >= strategy["max_layers"]:
                        can_buy = False
                        logger.info(f"[{coin_id}] Skipping: Max layers ({strategy['max_layers']}) reached.")

                    # For additional layers: require 1% gap from last entry
                    if can_buy and len(layers) > 0:
                        last_entry = layers[-1]["entry_price"]
                        if current_price > last_entry * 0.99:
                            can_buy = False
                            logger.info(f"[{coin_id}] Skipping: Price RM{current_price:.4f} not ≥1% below last entry RM{last_entry:.4f}.")

                    if can_buy and trade_amount <= balance and current_price > 0:
                        logger.info(f"[{coin_id}] Auto-executing LIMIT BUY RM{trade_amount:.2f} at RM{current_price:.4f}")
                        import hata_api
                        qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
                        quantity = round(trade_amount / current_price, qty_scale)
                        hata_res = hata_api.place_limit_order(f"{coin_id}_MYR", "BUY", current_price, quantity)

                        if hata_res.get("status") == "error":
                            logger.error(f"[{coin_id}] Hata API Error: {hata_res.get('message')}")
                        else:
                            order_id = hata_res.get("data", {}).get("id")
                            take_profit = current_price * (1.0 + strategy["tp_pct"])
                            layer = {
                                "id": len(layers) + 1,
                                "entry_price": current_price,
                                "amount_myr": trade_amount,
                                "quantity": quantity,
                                "take_profit": take_profit,
                                "status": "PENDING_BUY",
                                "buy_order_id": str(order_id),
                                "hata_buy_res": hata_res,
                                "created_at": time.time()
                            }
                            shared.engine_state[coin_id]["layers"].append(layer)
                            shared.save_state()
                            logger.info(f"[{coin_id}] PENDING_BUY created. Order {order_id} at RM{current_price:.4f}, TP: RM{take_profit:.4f}")
            else:
                shared.engine_state[coin_id]["last_signal"] = 0


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
async def start_ws():
    # ★ Step 1: Recover state from Hata API (handles laptop restart)
    await startup_recovery()

    # ★ Step 2: Start background loop (prices + balance + order checks every 60s)
    asyncio.create_task(update_hata_prices_loop())

    # ★ Step 3: Connect to Binance WebSocket for live candle data
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                logger.info(f"Connected to Binance WebSocket for {SYMBOLS}")
                while True:
                    data = await ws.recv()
                    payload = json.loads(data)
                    if 'stream' in payload and 'data' in payload:
                        stream_name = payload['stream']
                        kline_data = payload['data']['k']
                        coin_id = stream_name.split('@')[0].replace('usdt', '').upper()
                        await process_kline(coin_id, kline_data)
        except Exception as e:
            logger.error(f"WebSocket Error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)


def run():
    asyncio.run(start_ws())


if __name__ == "__main__":
    run()
