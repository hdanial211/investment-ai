import log_config
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
# TP% now comes from per-coin state (set via frontend)
# ─────────────────────────────────────────────
def _get_strategy(coin_id: str, risk_level: int) -> dict:
    tp_pct = shared.engine_state[coin_id].get("tp_pct", 0.005)
    if risk_level == 3:
        return {"max_layers": 3, "tp_pct": tp_pct}
    elif risk_level == 2:
        return {"max_layers": 5, "tp_pct": tp_pct}
    else:
        return {"max_layers": 6, "tp_pct": tp_pct}


# ─────────────────────────────────────────────
# Helper: Extract exec data from Hata order response
# ─────────────────────────────────────────────
def _extract_hata_exec_data(coin_id: str, order_data: dict, fallback_qty: float = 0.0) -> dict:
    """Extract actual executed quantity, fees, and cost from Hata API order data.
    Returns dict with: exec_qty, fee_qty, net_qty, actual_cost_myr"""
    exec_qty = float(order_data.get("exec_qty", fallback_qty))
    cummul_quote = float(order_data.get("cummul_quote_qty", 0.0))
    
    # Extract fees from trades array
    trades = order_data.get("trades", [])
    fee_qty = 0.0
    for t in trades:
        if t.get("fee_asset") == coin_id:
            fee_qty += float(t.get("fee", 0.0))
    
    # Net quantity = what's actually in wallet after buy
    if trades:
        net_qty = exec_qty - fee_qty
    else:
        # Fallback: Hata MAKER fee = 0% for limit orders (order book)
        # Taker fee = 0.25% only for market/IOC orders (we don't use those)
        net_qty = exec_qty
        fee_qty = 0.0
    
    # Actual MYR cost
    if cummul_quote > 0:
        actual_cost_myr = cummul_quote
    else:
        # Fallback: use orig price × exec_qty
        price = float(order_data.get("price", 0))
        actual_cost_myr = price * exec_qty if price > 0 else 0.0
    
    return {
        "exec_qty": exec_qty,
        "fee_qty": fee_qty,
        "net_qty": net_qty,
        "actual_cost_myr": actual_cost_myr
    }


# ─────────────────────────────────────────────
# CORE: Place consolidated sell order
# Cancel old sell → combine all HOLDING layers → 1 sell
# ─────────────────────────────────────────────
def _place_consolidated_sell(coin_id: str):
    """Cancel existing sell, combine all HOLDING layers, place 1 consolidated sell order."""
    import hata_api
    
    layers = shared.engine_state[coin_id].get("layers", [])
    holding_layers = [l for l in layers if l.get("status") == "HOLDING"]
    
    if not holding_layers:
        logger.info(f"[{coin_id}] No HOLDING layers to consolidate.")
        return
    
    # 1. Cancel existing consolidated sell if any
    old_sell_id = shared.engine_state[coin_id].get("consolidated_sell_order_id")
    if old_sell_id:
        logger.info(f"[{coin_id}] Cancelling old consolidated sell order {old_sell_id}...")
        cancel_res = hata_api.cancel_order(f"{coin_id}_MYR", old_sell_id)
        logger.info(f"[{coin_id}] Cancel result: {cancel_res}")
        shared.engine_state[coin_id]["consolidated_sell_order_id"] = None
    
    # 2. Calculate totals from all HOLDING layers
    total_cost = 0.0     # Total MYR spent (actual from Hata)
    total_net_qty = 0.0  # Total crypto received (net of fees)
    
    for l in holding_layers:
        cost = l.get("actual_cost_myr", l.get("amount_myr", 0))
        net = l.get("net_qty", 0)
        total_cost += cost
        total_net_qty += net
    
    if total_net_qty <= 0 or total_cost <= 0:
        logger.error(f"[{coin_id}] Cannot consolidate: total_net_qty={total_net_qty}, total_cost={total_cost}")
        return
    
    # 3. Weighted average entry price
    avg_entry = total_cost / total_net_qty
    
    # 4. Calculate sell price: avg_entry × (1 + tp_pct)
    # Hata Maker fee = 0% for limit orders that go to order book
    # Our sell is a LIMIT order placed above market price → always Maker → 0% fee
    # Taker fee (0.25%) only for market/IOC orders which we DON'T use
    tp_pct = shared.engine_state[coin_id].get("tp_pct", 0.005)
    sell_price = avg_entry * (1.0 + tp_pct)
    
    # 5. Verify actual wallet balance before placing sell
    qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
    price_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("price", 0)
    
    sell_qty = truncate_float(total_net_qty, qty_scale)
    sell_price = round(sell_price, price_scale)
    
    avail_bal, _ = hata_api.get_token_balance(coin_id)
    if avail_bal < sell_qty:
        logger.warning(f"[{coin_id}] Wallet balance ({avail_bal}) < planned sell qty ({sell_qty}). Capping to available.")
        sell_qty = truncate_float(avail_bal, qty_scale)
    
    if sell_qty <= 0:
        logger.error(f"[{coin_id}] Cannot place consolidated sell: sell_qty is 0.")
        return
    
    # 6. Place ONE consolidated sell order
    logger.info(f"[{coin_id}] CONSOLIDATED SELL: {len(holding_layers)} layers combined | "
                f"Avg Entry: RM{avg_entry:.4f} | TP: RM{sell_price:.4f} (+{tp_pct*100:.2f}%) | "
                f"Qty: {sell_qty} | Total Cost: RM{total_cost:.2f} | Maker Fee: 0%")
    
    sell_res = hata_api.place_limit_order(f"{coin_id}_MYR", "SELL", sell_price, sell_qty)
    
    if sell_res.get("status") == "error":
        logger.error(f"[{coin_id}] Consolidated SELL failed: {sell_res.get('message')}")
        return
    
    sell_order_id = str(sell_res.get("data", {}).get("id", ""))
    shared.engine_state[coin_id]["consolidated_sell_order_id"] = sell_order_id
    
    # Store consolidated sell metadata on each holding layer for reference
    for l in holding_layers:
        l["consolidated_sell_price"] = sell_price
        l["consolidated_sell_qty"] = sell_qty
    
    shared.save_state()
    logger.info(f"[{coin_id}] CONSOLIDATED SELL SUCCESS: Order {sell_order_id} at RM{sell_price:.4f}")


# ─────────────────────────────────────────────
# Helper: Place next DCA BUY layer at 1% below entry
# (Called after a consolidated SELL fills)
# NOTE: This only places a BUY — sell is handled by consolidated
# ─────────────────────────────────────────────
def _place_next_dca_buy(coin_id: str, last_entry_price: float):
    """After a consolidated SELL fills, place Limit BUY at 1% below last entry."""
    import hata_api

    layers = shared.engine_state[coin_id].get("layers", [])
    risk_level = shared.engine_state[coin_id].get("risk_level", 1)
    strategy = _get_strategy(coin_id, risk_level)

    if len(layers) >= strategy["max_layers"]:
        logger.info(f"[{coin_id}] Max layers ({strategy['max_layers']}) reached. Skipping auto-DCA.")
        return

    # 1% below last entry price
    next_entry = round(last_entry_price * 0.99, 6)
    trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
    qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
    quantity = round(trade_amount / next_entry, qty_scale)

    logger.info(f"[{coin_id}] AUTO-DCA: Placing Limit BUY at RM{next_entry:.4f} (1% below RM{last_entry_price:.4f})")
    hata_res = hata_api.place_limit_order(f"{coin_id}_MYR", "BUY", next_entry, quantity)

    if hata_res.get("status") == "error":
        logger.error(f"[{coin_id}] Auto-DCA BUY failed: {hata_res.get('message')}")
        return

    order_id = hata_res.get("data", {}).get("id")
    layer = {
        "id": len(layers) + 1,
        "entry_price": next_entry,
        "amount_myr": trade_amount,
        "quantity": quantity,
        "status": "PENDING_BUY",
        "buy_order_id": str(order_id),
        "hata_buy_res": hata_res,
        "created_at": time.time()
    }
    shared.engine_state[coin_id]["layers"].append(layer)
    shared.save_state()
    logger.info(f"[{coin_id}] AUTO-DCA SUCCESS: BUY order {order_id} at RM{next_entry:.4f}")


# ─────────────────────────────────────────────
# Startup Recovery: Sync all layers with Hata API
# Runs once on bot start / laptop restart
# Migrates old per-layer sells to consolidated sell
# ─────────────────────────────────────────────
async def startup_recovery():
    """Reconcile all PENDING layers in bot_state.json with actual Hata API status.
    Handles: fills missed while bot was offline, stuck orders, missing created_at.
    Also migrates old per-layer sell orders to new consolidated sell system."""
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
            needs_consolidated_sell = False
            old_sell_ids_to_cancel = []
            logger.info(f"[{coin_id}] Recovering {len(layers)} layer(s)...")

            for l in layers:
                status = l.get("status", "OPEN")

                # ── MIGRATE: Old PENDING_SELL layers → HOLDING ──
                # Old system had per-layer sells. Cancel them and convert to HOLDING.
                if status == "PENDING_SELL":
                    sell_id = l.get("sell_order_id")
                    if sell_id:
                        # Check if sell already filled
                        res = hata_api.get_order_status(sell_id)
                        order_data = res.get("data")
                        if order_data and order_data.get("status") == "fulfilled":
                            # Old sell filled — count P&L and remove layer
                            exec_data = _extract_hata_exec_data(coin_id, order_data)
                            sell_received = exec_data.get("actual_cost_myr", 0)
                            buy_cost = l.get("actual_cost_myr", l.get("amount_myr", 0))
                            pnl = sell_received - buy_cost
                            shared.engine_state[coin_id]["total_pnl"] += pnl
                            logger.info(f"[{coin_id}] RECOVERY: Old sell {sell_id} was filled! PnL: RM{pnl:.2f}")
                            coin_changed = True
                            continue  # Don't append — layer complete
                        elif order_data and order_data.get("status") in ["cancelled", "rejected"]:
                            # Already cancelled — convert to HOLDING
                            logger.info(f"[{coin_id}] RECOVERY: Old sell {sell_id} already cancelled. Converting to HOLDING.")
                        else:
                            # Still active — need to cancel it
                            old_sell_ids_to_cancel.append(sell_id)
                            logger.info(f"[{coin_id}] RECOVERY: Will cancel old per-layer sell {sell_id}")
                    
                    # Convert to HOLDING — need exec data if not present
                    if "net_qty" not in l:
                        # Fetch buy order to get actual exec data
                        buy_id = l.get("buy_order_id")
                        if buy_id:
                            buy_res = hata_api.get_order_status(buy_id)
                            buy_data = buy_res.get("data")
                            if buy_data and buy_data.get("status") == "fulfilled":
                                exec_info = _extract_hata_exec_data(coin_id, buy_data, l.get("quantity", 0))
                                l["exec_qty"] = exec_info["exec_qty"]
                                l["fee_qty"] = exec_info["fee_qty"]
                                l["net_qty"] = exec_info["net_qty"]
                                l["actual_cost_myr"] = exec_info["actual_cost_myr"]
                            else:
                                # Fallback from stored data
                                sell_qty = l.get("sell_quantity", l.get("quantity", 0))
                                l["net_qty"] = sell_qty
                                l["exec_qty"] = l.get("quantity", 0)
                                l["fee_qty"] = l.get("quantity", 0) - sell_qty
                                l["actual_cost_myr"] = l.get("amount_myr", 0)
                        else:
                            sell_qty = l.get("sell_quantity", l.get("quantity", 0))
                            l["net_qty"] = sell_qty
                            l["exec_qty"] = l.get("quantity", 0)
                            l["fee_qty"] = l.get("quantity", 0) - sell_qty
                            l["actual_cost_myr"] = l.get("amount_myr", 0)
                    
                    l["status"] = "HOLDING"
                    coin_changed = True
                    needs_consolidated_sell = True
                    active_layers.append(l)

                # ── PENDING_BUY ──────────────────────────────────
                elif status == "PENDING_BUY":
                    buy_id = l.get("buy_order_id")
                    if not buy_id:
                        l["status"] = "HOLDING"
                        coin_changed = True
                        needs_consolidated_sell = True
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
                        # Missed fill while bot was offline → extract exec data, mark HOLDING
                        logger.info(f"[{coin_id}] RECOVERY: Buy {buy_id} was already filled!")
                        exec_info = _extract_hata_exec_data(coin_id, order_data, l.get("quantity", 0))
                        l["exec_qty"] = exec_info["exec_qty"]
                        l["fee_qty"] = exec_info["fee_qty"]
                        l["net_qty"] = exec_info["net_qty"]
                        l["actual_cost_myr"] = exec_info["actual_cost_myr"]
                        l["status"] = "HOLDING"
                        coin_changed = True
                        needs_consolidated_sell = True
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
                            logger.info(f"[{coin_id}] RECOVERY: Patched created_at for buy {buy_id}.")

                        age_sec = time.time() - l["created_at"]
                        if age_sec > 300:
                            logger.info(f"[{coin_id}] RECOVERY: Buy {buy_id} stuck >{age_sec/60:.1f} min. Auto-cancelling...")
                            cancel_res = hata_api.cancel_order(f"{coin_id}_MYR", buy_id)
                            logger.info(f"[{coin_id}] RECOVERY: Cancel result: {cancel_res}")
                            coin_changed = True
                            # Do NOT append — layer is removed
                        else:
                            active_layers.append(l)

                # ── HOLDING (already converted) ─────────────────
                elif status == "HOLDING":
                    active_layers.append(l)
                    needs_consolidated_sell = True

                # ── OPEN (legacy retry) ─────────────────────────
                elif status == "OPEN":
                    # Old OPEN layers = buy filled but sell failed
                    # Convert to HOLDING
                    if "net_qty" not in l:
                        sell_qty = l.get("sell_quantity", l.get("quantity", 0))
                        l["net_qty"] = sell_qty
                        l["exec_qty"] = l.get("quantity", 0)
                        l["fee_qty"] = l.get("quantity", 0) - sell_qty if sell_qty < l.get("quantity", 0) else 0
                        l["actual_cost_myr"] = l.get("amount_myr", 0)
                    l["status"] = "HOLDING"
                    coin_changed = True
                    needs_consolidated_sell = True
                    active_layers.append(l)

                else:
                    active_layers.append(l)

            # Cancel all old per-layer sells
            for sell_id in old_sell_ids_to_cancel:
                cancel_res = hata_api.cancel_order(f"{coin_id}_MYR", sell_id)
                logger.info(f"[{coin_id}] RECOVERY: Cancelled old sell {sell_id}: {cancel_res}")

            if coin_changed:
                shared.engine_state[coin_id]["layers"] = active_layers
                state_changed = True

            # Place consolidated sell if we have HOLDING layers
            if needs_consolidated_sell:
                holding_count = len([l for l in active_layers if l.get('status') == 'HOLDING'])
                logger.info(f"[{coin_id}] RECOVERY: Placing consolidated sell for {holding_count} HOLDING layers...")
                _place_consolidated_sell(coin_id)
                state_changed = True

            # Cascade: if HOLDING layers exist but no PENDING_BUY, place next cascade buy
            current_layers = shared.engine_state[coin_id].get("layers", [])
            has_pending = any(l.get("status") == "PENDING_BUY" for l in current_layers)
            holding_in_recovery = [l for l in current_layers if l.get("status") == "HOLDING"]
            if holding_in_recovery and not has_pending:
                risk_level = shared.engine_state[coin_id].get("risk_level", 1)
                strategy = _get_strategy(coin_id, risk_level)
                if len(current_layers) < strategy["max_layers"]:
                    last_holding = holding_in_recovery[-1]
                    last_entry = last_holding.get("entry_price", 0)
                    if last_entry > 0:
                        logger.info(f"[{coin_id}] RECOVERY CASCADE: Placing pending BUY for next layer below RM{last_entry:.4f}")
                        _place_next_dca_buy(coin_id, last_entry)
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

            # 3. Check all pending orders for all 5 coins (NEW CONSOLIDATED FLOW)
            def check_orders():
                state_changed = False
                for coin_id in shared.engine_state:
                    layers = shared.engine_state[coin_id].get("layers", [])
                    active_layers = []
                    coin_changed = False
                    needs_consolidated_sell = False

                    for l in layers:
                        status = l.get("status", "HOLDING")

                        # ── PENDING_BUY ──────────────────────────
                        if status == "PENDING_BUY":
                            buy_id = l.get("buy_order_id")
                            if not buy_id:
                                l["status"] = "HOLDING"
                                coin_changed = True
                                needs_consolidated_sell = True
                                active_layers.append(l)
                                continue

                            res = hata_api.get_order_status(buy_id)
                            order_data = res.get("data")

                            if order_data:
                                order_status = order_data.get("status")

                                if order_status == "fulfilled":
                                    logger.info(f"[{coin_id}] Buy {buy_id} FILLED!")
                                    # Extract actual exec data from Hata API
                                    exec_info = _extract_hata_exec_data(coin_id, order_data, l.get("quantity", 0))
                                    l["exec_qty"] = exec_info["exec_qty"]
                                    l["fee_qty"] = exec_info["fee_qty"]
                                    l["net_qty"] = exec_info["net_qty"]
                                    l["actual_cost_myr"] = exec_info["actual_cost_myr"]
                                    l["status"] = "HOLDING"
                                    coin_changed = True
                                    needs_consolidated_sell = True
                                    # ★ Track for cascade: remember this layer just filled
                                    l["_just_filled"] = True
                                    active_layers.append(l)
                                    logger.info(f"[{coin_id}] Layer {l['id']} → HOLDING | "
                                                f"exec_qty: {exec_info['exec_qty']}, "
                                                f"net_qty: {exec_info['net_qty']}, "
                                                f"cost: RM{exec_info['actual_cost_myr']:.2f}")

                                elif order_status in ["cancelled", "rejected"]:
                                    logger.info(f"[{coin_id}] Buy {buy_id} was {order_status}. Removing layer.")
                                    coin_changed = True
                                    # Do NOT append — layer removed

                                else:
                                    # Still active — ensure created_at exists, cancel if stuck
                                    if "created_at" not in l:
                                        l["created_at"] = time.time()
                                        coin_changed = True
                                        logger.info(f"[{coin_id}] Patched created_at for buy {buy_id}.")

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

                        # ── HOLDING (waiting for consolidated sell to fill) ──
                        elif status == "HOLDING":
                            active_layers.append(l)

                        else:
                            active_layers.append(l)

                    if coin_changed:
                        shared.engine_state[coin_id]["layers"] = active_layers
                        state_changed = True

                    # Check consolidated sell order status
                    consolidated_sell_id = shared.engine_state[coin_id].get("consolidated_sell_order_id")
                    holding_layers = [l for l in active_layers if l.get("status") == "HOLDING"]
                    
                    if consolidated_sell_id and holding_layers:
                        res = hata_api.get_order_status(consolidated_sell_id)
                        order_data = res.get("data")
                        
                        if order_data:
                            sell_status = order_data.get("status")
                            
                            if sell_status == "fulfilled":
                                # CONSOLIDATED SELL FILLED! Calculate real P&L from Hata
                                exec_info = _extract_hata_exec_data(coin_id, order_data)
                                sell_received_myr = exec_info["actual_cost_myr"]  # MYR received from sell
                                
                                # Total cost of all holding layers
                                total_buy_cost = sum(l.get("actual_cost_myr", l.get("amount_myr", 0)) for l in holding_layers)
                                
                                # Real P&L = what we received - what we spent
                                real_pnl = sell_received_myr - total_buy_cost
                                shared.engine_state[coin_id]["total_pnl"] += real_pnl
                                
                                logger.info(f"[{coin_id}] ★ CONSOLIDATED SELL FILLED! ★")
                                logger.info(f"[{coin_id}]   Sold: RM{sell_received_myr:.2f} | Cost: RM{total_buy_cost:.2f} | PnL: RM{real_pnl:.2f}")
                                logger.info(f"[{coin_id}]   Total PnL: RM{shared.engine_state[coin_id]['total_pnl']:.2f}")
                                
                                # Save last cycle entry for 2% gap enforcement
                                last_entry = holding_layers[-1].get("entry_price", 0)
                                shared.engine_state[coin_id]["last_cycle_entry"] = last_entry
                                
                                # Cancel any remaining PENDING_BUY (cascade buys not yet filled)
                                remaining_pending = [l for l in active_layers if l.get("status") == "PENDING_BUY"]
                                for rp in remaining_pending:
                                    rp_id = rp.get("buy_order_id")
                                    if rp_id:
                                        logger.info(f"[{coin_id}] Cancelling remaining cascade buy {rp_id}...")
                                        hata_api.cancel_order(f"{coin_id}_MYR", rp_id)
                                
                                # Clear ALL layers — cycle complete
                                shared.engine_state[coin_id]["layers"] = []
                                shared.engine_state[coin_id]["consolidated_sell_order_id"] = None
                                state_changed = True
                                shared.save_state()
                                
                                # ★ DON'T auto-place next DCA buy here
                                # New entry requires: AI signal + 2% gap from last_cycle_entry
                                logger.info(f"[{coin_id}] Cycle complete. Next entry requires AI signal + 2% gap below RM{last_entry:.4f} (min RM{last_entry * 0.98:.4f})")
                                    
                            elif sell_status in ["cancelled", "rejected"]:
                                logger.warning(f"[{coin_id}] Consolidated sell {consolidated_sell_id} was {sell_status}. Re-placing...")
                                shared.engine_state[coin_id]["consolidated_sell_order_id"] = None
                                state_changed = True
                                needs_consolidated_sell = True
                    
                    # Place new consolidated sell if needed + cascade next pending buy
                    if needs_consolidated_sell:
                        current_layers = shared.engine_state[coin_id].get("layers", [])
                        current_holding = [l for l in current_layers if l.get("status") == "HOLDING"]
                        if current_holding:
                            _place_consolidated_sell(coin_id)
                            state_changed = True

                        # ★ CASCADE: If a BUY just filled, auto-place pending buy for NEXT layer
                        just_filled = [l for l in current_layers if l.get("_just_filled")]
                        if just_filled:
                            # Clean up the _just_filled flag
                            for l in just_filled:
                                l.pop("_just_filled", None)

                            # Only cascade if no other PENDING_BUY exists and not at max
                            has_pending = any(l.get("status") == "PENDING_BUY" for l in current_layers)
                            risk_level = shared.engine_state[coin_id].get("risk_level", 1)
                            strategy = _get_strategy(coin_id, risk_level)

                            if not has_pending and len(current_layers) < strategy["max_layers"]:
                                # Use the lowest/latest filled layer's entry price
                                last_filled = just_filled[-1]
                                last_entry = last_filled.get("entry_price", 0)
                                if last_entry > 0:
                                    logger.info(f"[{coin_id}] ★ CASCADE: Layer {last_filled['id']} filled → auto-pending BUY for next layer below RM{last_entry:.4f}")
                                    _place_next_dca_buy(coin_id, last_entry)
                                    state_changed = True
                            elif has_pending:
                                logger.info(f"[{coin_id}] CASCADE: Skipping — already has a PENDING_BUY.")
                            elif len(current_layers) >= strategy["max_layers"]:
                                logger.info(f"[{coin_id}] CASCADE: Skipping — max layers ({strategy['max_layers']}) reached.")

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

                    # ★ BLOCK: Jika ada layers aktif (sedang dalam layering cycle)
                    # Cascade akan handle DCA secara automatik — AI signal hanya untuk ENTRY BARU
                    if len(layers) > 0:
                        can_buy = False
                        logger.info(f"[{coin_id}] Skipping: Active layering cycle ({len(layers)} layers). Cascade handles DCA.")

                    # ★ BLOCK: Selepas habis layering, kena tunggu 2% gap dari last cycle entry
                    if can_buy:
                        last_cycle = shared.engine_state[coin_id].get("last_cycle_entry", 0)
                        if last_cycle > 0 and current_price > last_cycle * 0.98:
                            can_buy = False
                            min_entry = last_cycle * 0.98
                            logger.info(f"[{coin_id}] Skipping: Price RM{current_price:.4f} not ≥2% below last cycle entry RM{last_cycle:.4f}. Need ≤RM{min_entry:.4f}.")

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
                            layer = {
                                "id": len(layers) + 1,
                                "entry_price": current_price,
                                "amount_myr": trade_amount,
                                "quantity": quantity,
                                "status": "PENDING_BUY",
                                "buy_order_id": str(order_id),
                                "hata_buy_res": hata_res,
                                "created_at": time.time()
                            }
                            shared.engine_state[coin_id]["layers"].append(layer)
                            shared.save_state()
                            logger.info(f"[{coin_id}] PENDING_BUY created. Order {order_id} at RM{current_price:.4f}")
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
