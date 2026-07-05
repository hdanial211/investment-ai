import log_config
import asyncio
import websockets
import json
import logging
import math
import pandas as pd
import numpy as np
import joblib
import os
import sys
import time
from datetime import datetime

# Import shared state
import shared

# ML Pipeline imports
import ml_logger
import ml_adaptive

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

# ── Create ML tables on startup ──
try:
    from database.ml_models import create_ml_tables
    create_ml_tables()
    logger.info("ML tables initialized.")
except Exception as e:
    logger.error(f"Failed to create ML tables: {e}")

# Hata MYR prices cache
hata_prices = {
    "ETH": 0.0,
    "BTC": 0.0,
    "SOL": 0.0,
    "LTC": 0.0,
    "XRP": 0.0
}


def truncate_float(val: float, decimals: int) -> float:
    """Truncate float to N decimal places without rounding up.
    Uses 1e-12 epsilon to fix IEEE754 representation errors
    (e.g. 6.27 * 100 = 626.999...) without over-rounding real boundary values."""
    factor = 10 ** decimals
    return math.floor(val * factor + 1e-12) / factor


# ─────────────────────────────────────────────
# Helper: Get strategy settings by risk level
# TP% now comes from per-coin state (set via frontend)
# ─────────────────────────────────────────────
def _get_strategy(coin_id: str, risk_level: int) -> dict:
    tp_pct = shared.engine_state[coin_id].get("tp_pct", 0.005)
    # Per-coin max_layers — each coin set individually via frontend (/api/set-max-layers)
    # Default 5 if never explicitly set (matches frontend fallback: coinData.max_layers || 5)
    custom_max = shared.engine_state[coin_id].get("max_layers", 0)
    max_layers = int(custom_max) if custom_max and custom_max > 0 else 5
    return {"max_layers": max_layers, "tp_pct": tp_pct}


# ─────────────────────────────────────────────
# Helper: Extract exec data from Hata order response
# ─────────────────────────────────────────────
def _extract_hata_exec_data(coin_id: str, order_data: dict, fallback_qty: float = 0.0) -> dict:
    """Extract actual executed quantity, fees, and cost from Hata API order data.
    Returns dict with: exec_qty, fee_qty, net_qty, actual_cost_myr, fee_role"""
    exec_qty = float(order_data.get("exec_qty", fallback_qty))
    cummul_quote = float(order_data.get("cummul_quote_qty", 0.0))
    
    # Extract fees from trades array (actual from Hata API)
    trades = order_data.get("trades", [])
    fee_qty = 0.0
    fee_role = None  # will be resolved below
    for t in trades:
        if t.get("fee_asset") == coin_id:
            fee_qty += float(t.get("fee", 0.0))
        # Detect role from trade data (is_maker field from Hata)
        if t.get("is_maker") is True:
            fee_role = "maker"
        elif t.get("is_maker") is False:
            fee_role = "taker"

    # Net quantity = what's actually in wallet after fees
    if trades:
        net_qty = exec_qty - fee_qty
        # ★ Kalau fee_role masih None (is_maker field tiada dalam trades)
        # → infer dari fee_qty: 0 fee = maker (0%), ada fee = taker (0.25%)
        if fee_role is None:
            fee_role = "maker" if fee_qty == 0 else "taker"
            logger.info(f"[{coin_id}] fee_role inferred from fee_qty: {fee_role} (fee={fee_qty})")
        if fee_qty > 0:
            logger.info(f"[{coin_id}] Fee detected: {fee_qty} {coin_id} ({fee_role}) | exec: {exec_qty} -> net: {net_qty}")
        else:
            logger.info(f"[{coin_id}] No fee ({fee_role}) | exec: {exec_qty} = net: {net_qty}")
    else:
        # Fallback: tiada trades data → assume TAKER worst case (0.25% fee)
        fee_qty = exec_qty * 0.0025
        net_qty = exec_qty * 0.9975
        fee_role = "taker"
        logger.warning(f"[{coin_id}] No trades data — using 0.25% taker fallback fee")
    
    # Actual MYR cost
    if cummul_quote > 0:
        actual_cost_myr = cummul_quote
    else:
        # Fallback: use orig price × exec_qty
        price = float(order_data.get("price", 0))
        actual_cost_myr = price * exec_qty if price > 0 else 0.0
    
    # Calculate fee in MYR terms for display
    price = float(order_data.get("price", 0))
    fee_myr = fee_qty * price if price > 0 else 0.0
    
    return {
        "exec_qty": exec_qty,
        "fee_qty": fee_qty,
        "net_qty": net_qty,
        "actual_cost_myr": actual_cost_myr,
        "fee_myr": fee_myr,
        "fee_role": fee_role
    }


# ─────────────────────────────────────────────
# LEGACY DCA: Place consolidated sell order
# ⚠ DEPRECATED — Only used when system_mode == "dca" or startup_recovery legacy path
# Grid mode uses _grid_place_layer_sell() instead
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
    total_fee_qty = 0.0  # Total fees paid in coin
    total_fee_myr = 0.0  # Total fees paid in MYR
    
    for l in holding_layers:
        cost = l.get("actual_cost_myr", l.get("amount_myr", 0))
        net = l.get("net_qty", 0)
        fee = l.get("fee_qty", 0)
        fee_m = l.get("fee_myr", 0)
        total_cost += cost
        total_net_qty += net
        total_fee_qty += fee
        total_fee_myr += fee_m
    
    if total_net_qty <= 0 or total_cost <= 0:
        logger.error(f"[{coin_id}] Cannot consolidate: total_net_qty={total_net_qty}, total_cost={total_cost}")
        return
    
    # 3. Weighted average entry price (INCLUDES fee recovery automatically)
    # Because net_qty < exec_qty when fees exist, avg_entry is higher
    # This means sell price naturally covers the fee loss
    avg_entry = total_cost / total_net_qty
    
    # 4. Calculate sell price: avg_entry × (1 + tp_pct)
    # Fee recovery is BUILT INTO avg_entry because we divide by net_qty (after fees)
    # Example: Paid RM10 for 0.00003984 BTC (after 0.4% taker fee)
    #   avg_entry = 10 / 0.00003984 = RM250,999 (higher than buy price RM256,446)
    #   sell_price = 250,999 * 1.005 = RM252,254 → recovers fee + TP profit
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
    fee_info = f"Total Buy Fee: RM{total_fee_myr:.4f} ({total_fee_qty} {coin_id})" if total_fee_qty > 0 else "No buy fees (Maker)"
    logger.info(f"[{coin_id}] CONSOLIDATED SELL: {len(holding_layers)} layers combined | "
                f"Avg Entry: RM{avg_entry:.4f} | TP: RM{sell_price:.4f} (+{tp_pct*100:.2f}%) | "
                f"Qty: {sell_qty} | Cost: RM{total_cost:.2f} | {fee_info}")
    
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
    
    # Store fee summary for frontend
    shared.engine_state[coin_id]["total_buy_fees_myr"] = total_fee_myr
    shared.engine_state[coin_id]["total_buy_fees_qty"] = total_fee_qty
    
    shared.save_state()
    logger.info(f"[{coin_id}] CONSOLIDATED SELL SUCCESS: Order {sell_order_id} at RM{sell_price:.4f}")


# ─────────────────────────────────────────────
# LEGACY DCA: Place next DCA BUY layer at 1% below entry
# ⚠ DEPRECATED — Only used when system_mode == "dca"
# Grid mode uses _grid_update_standby_buy() instead
# ─────────────────────────────────────────────
def _place_next_dca_buy(coin_id: str, last_entry_price: float):
    """After a consolidated SELL fills, place Limit BUY at 1% below last entry.
    Uses min(limit_price, current_price) to ensure full RM deployment."""
    import hata_api

    layers = shared.engine_state[coin_id].get("layers", [])
    risk_level = shared.engine_state[coin_id].get("risk_level", 1)
    strategy = _get_strategy(coin_id, risk_level)

    if len(layers) >= strategy["max_layers"]:
        logger.info(f"[{coin_id}] Max layers ({strategy['max_layers']}) reached. Skipping auto-DCA.")
        return

    # 1% below last entry price (intended limit level)
    next_entry = round(last_entry_price * 0.99, 6)

    # ★ FIX: Use the LOWER of limit price or current price for qty calc & order
    # If market already dropped below limit, order fills at market price instantly
    # So qty must be based on actual fill price to deploy full RM amount
    current_price = shared.engine_state[coin_id].get("current_price", 0)
    if current_price > 0 and current_price < next_entry:
        buy_price = current_price
        logger.info(f"[{coin_id}] AUTO-DCA: Market RM{current_price:.4f} already < limit RM{next_entry:.4f} → using market price for accurate RM deployment")
    else:
        buy_price = next_entry

    trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
    qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
    price_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("price", 2)
    buy_price = round(buy_price, price_scale)
    quantity = round(trade_amount / buy_price, qty_scale)

    logger.info(f"[{coin_id}] AUTO-DCA: Placing Limit BUY at RM{buy_price:.{price_scale}f} | qty: {quantity} | target spend: RM{trade_amount:.2f}")
    hata_res = hata_api.place_limit_order(f"{coin_id}_MYR", "BUY", buy_price, quantity)

    if hata_res.get("status") == "error":
        logger.error(f"[{coin_id}] Auto-DCA BUY failed: {hata_res.get('message')}")
        return

    order_id = hata_res.get("data", {}).get("id")
    layer = {
        "id": len(layers) + 1,
        "entry_price": buy_price,
        "amount_myr": trade_amount,
        "quantity": quantity,
        "status": "PENDING_BUY",
        "buy_order_id": str(order_id),
        "hata_buy_res": hata_res,
        "created_at": time.time()
    }
    shared.engine_state[coin_id]["layers"].append(layer)
    shared.save_state()
    logger.info(f"[{coin_id}] AUTO-DCA SUCCESS: BUY order {order_id} at RM{buy_price:.{price_scale}f} (target: RM{trade_amount:.2f})")


# ─────────────────────────────────────────────
# GRID SYSTEM: Place individual sell for one layer
# Each layer has its own SELL order (MAKER = 0% fee)
# ─────────────────────────────────────────────
def _grid_place_layer_sell(coin_id: str, layer: dict) -> str:
    """Place SELL limit order for one layer. Returns sell_order_id or empty string."""
    import hata_api

    gap_pct = shared.engine_state[coin_id].get("grid_gap_pct", 0.01)
    qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
    price_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("price", 0)

    net_qty = layer.get("net_qty", 0) or layer.get("quantity", 0)
    actual_cost = layer.get("actual_cost_myr", 0) or layer.get("amount_myr", 0)
    fee_role = layer.get("fee_role", "unknown")
    fee_myr = layer.get("fee_myr", 0.0)

    if net_qty <= 0 or actual_cost <= 0:
        logger.error(f"[{coin_id}] GRID SELL: Cannot place sell — net_qty={net_qty}, cost={actual_cost}")
        return ""

    avg_entry = actual_cost / net_qty
    sell_price = round(avg_entry * (1.0 + gap_pct), price_scale)
    sell_qty = truncate_float(net_qty, qty_scale)

    avail_bal, _ = hata_api.get_token_balance(coin_id)
    if avail_bal < sell_qty:
        # ★ Race condition: mungkin layer lain baru letak sell guna balance yang sama
        # Tunggu 1 saat dan cuba semula sekali
        logger.warning(f"[{coin_id}] GRID SELL: Wallet ({avail_bal:.6f}) < planned ({sell_qty}). "
                       f"Retrying after 1s (kemungkinan race condition multiple layers)...")
        time.sleep(1)
        avail_bal, _ = hata_api.get_token_balance(coin_id)
        if avail_bal < sell_qty:
            logger.warning(f"[{coin_id}] GRID SELL: After retry, wallet ({avail_bal:.6f}) < planned ({sell_qty}). Capping.")
            sell_qty = truncate_float(avail_bal, qty_scale)

    if sell_qty <= 0:
        logger.error(f"[{coin_id}] GRID SELL: sell_qty is 0 after balance check. Skipping (will retry next cycle).")
        return ""

    logger.info(f"[{coin_id}] GRID SELL Layer {layer['id']}: avg_entry=RM{avg_entry:.4f} "
                f"| sell=RM{sell_price:.{price_scale}f} | qty={sell_qty} "
                f"| gap={gap_pct*100:.2f}% | fee={fee_role} RM{fee_myr:.4f}")

    sell_res = hata_api.place_limit_order(f"{coin_id}_MYR", "SELL", sell_price, sell_qty)
    if sell_res.get("status") == "error":
        logger.error(f"[{coin_id}] GRID SELL failed: {sell_res.get('message')}")
        return ""

    sell_order_id = str(sell_res.get("data", {}).get("id", ""))
    layer["sell_order_id"] = sell_order_id
    layer["sell_target_price"] = sell_price
    logger.info(f"[{coin_id}] GRID SELL OK: Order {sell_order_id} @ RM{sell_price:.{price_scale}f}")
    return sell_order_id


# ─────────────────────────────────────────────
# GRID SYSTEM: Update standby BUY for ONE group
# ─────────────────────────────────────────────
def _grid_update_standby_buy(coin_id: str, group: dict, from_price: float):
    """Cancel existing standby BUY for this group and place new one at from_price*(1-gap)."""
    import hata_api

    gap_pct = shared.engine_state[coin_id].get("grid_gap_pct", 0.01)
    qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
    price_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("price", 0)
    trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
    risk_level = shared.engine_state[coin_id].get("risk_level", 1)
    strategy = _get_strategy(coin_id, risk_level)

    group_layers = group.get("layers", [])
    holding = [l for l in group_layers if l.get("status") == "HOLDING"]

    if len(holding) >= strategy["max_layers"]:
        logger.info(f"[{coin_id}] Group {group['id']}: Max layers ({strategy['max_layers']}) reached. No standby buy.")
        old_standby_id = group.get("standby_buy_order_id")
        if old_standby_id:
            logger.info(f"[{coin_id}] Group {group['id']}: Cancelling old standby {old_standby_id} due to max layers")
            hata_api.cancel_order(f"{coin_id}_MYR", old_standby_id)
            group["standby_buy_order_id"] = None
            group["standby_buy_price"] = 0.0
        return

    # Cancel old standby buy for this group
    old_standby_id = group.get("standby_buy_order_id")
    if old_standby_id:
        logger.info(f"[{coin_id}] Group {group['id']}: Cancelling old standby {old_standby_id}")
        hata_api.cancel_order(f"{coin_id}_MYR", old_standby_id)
        group["standby_buy_order_id"] = None
        group["standby_buy_price"] = 0.0

    standby_price = round(from_price * (1.0 - gap_pct), price_scale)

    # ★ CAP: standby BUY mesti sentiasa DI BAWAH harga semasa
    # Elak TAKER fee (0.25%) kalau harga dah jatuh lebih jauh dari grid level
    # Contoh: grid standby = 333.10 tapi market dah = 332.50 → cap ke 332.34 (0.05% bawah)
    current_mkt_price = shared.engine_state[coin_id].get("current_price", 0)
    if current_mkt_price > 0 and standby_price >= current_mkt_price:
        capped_price = round(current_mkt_price * 0.9995, price_scale)
        logger.info(f"[{coin_id}] Group {group['id']}: Standby grid price RM{standby_price:.{price_scale}f} ≥ market RM{current_mkt_price:.{price_scale}f} "
                    f"→ CAP ke RM{capped_price:.{price_scale}f} (0.05% bawah market, MAKER 0%)")
        standby_price = capped_price

    quantity = round(trade_amount / standby_price, qty_scale)

    min_notional = hata_api.COIN_SCALES.get(coin_id, {}).get("min_notional", 10.0)
    if standby_price * quantity < min_notional:
        logger.warning(f"[{coin_id}] Group {group['id']}: Notional too small. Skipping standby.")
        return

    logger.info(f"[{coin_id}] Group {group['id']}: Placing standby BUY @ RM{standby_price:.{price_scale}f} "
                f"({gap_pct*100:.2f}% below RM{from_price:.{price_scale}f})")

    buy_res = hata_api.place_limit_order(f"{coin_id}_MYR", "BUY", standby_price, quantity)
    if buy_res.get("status") == "error":
        logger.error(f"[{coin_id}] Group {group['id']}: Standby BUY failed: {buy_res.get('message')}")
        return

    standby_id = str(buy_res.get("data", {}).get("id", ""))
    group["standby_buy_order_id"] = standby_id
    group["standby_buy_price"] = standby_price
    logger.info(f"[{coin_id}] Group {group['id']}: Standby BUY OK — {standby_id} @ RM{standby_price:.{price_scale}f}")
    shared.save_state()


# ─────────────────────────────────────────────
# GRID SYSTEM: Check ONE group's orders
# ─────────────────────────────────────────────
def _check_grid_group(coin_id: str, group: dict) -> bool:
    """Check all orders in one group. Returns True if state changed."""
    import hata_api

    state_changed = False
    layers = group.get("layers", [])

    # ── Check PENDING_BUY layers (first entry waiting to fill) ──
    layers_to_delete_pending = []
    for l in layers:
        if l.get("status") != "PENDING_BUY":
            continue
        buy_id = l.get("buy_order_id")
        if not buy_id:
            l["status"] = "HOLDING"
            state_changed = True
            continue
        res = hata_api.get_order_status(buy_id)
        order_data = res.get("data")
        if not order_data:
            continue
        order_status = order_data.get("status")

        if order_status == "fulfilled":
            exec_info = _extract_hata_exec_data(coin_id, order_data, l.get("quantity", 0))
            l["exec_qty"] = exec_info["exec_qty"]
            l["fee_qty"] = exec_info["fee_qty"]
            l["net_qty"] = exec_info["net_qty"]
            l["actual_cost_myr"] = exec_info["actual_cost_myr"]
            l["fee_myr"] = exec_info["fee_myr"]
            l["fee_role"] = exec_info["fee_role"]
            l["status"] = "HOLDING"
            state_changed = True
            # ★ UNFREEZE: balance sebenar dah jadi coin dalam wallet, bukan MYR lagi
            amt = l.get("amount_myr", 0.0)
            shared.global_state["frozen_myr"] = max(0.0, shared.global_state.get("frozen_myr", 0.0) - amt)
            logger.info(f"[{coin_id}] Unfroze RM{amt:.2f} (filled). Frozen now: RM{shared.global_state['frozen_myr']:.2f}")
            logger.info(f"[{coin_id}] Group {group['id']} Layer {l['id']} PENDING_BUY filled → HOLDING "
                        f"| net={exec_info['net_qty']:.6f} fee={exec_info['fee_role']} RM{exec_info['fee_myr']:.4f}")
            # Place sell immediately
            _grid_place_layer_sell(coin_id, l)
            # Place standby buy for this group
            _grid_update_standby_buy(coin_id, group, l["entry_price"])

        elif order_status in ["cancelled", "rejected"]:
            # ★ Manual cancel dari luar (Hata dashboard) → remove layer sahaja
            logger.info(f"[{coin_id}] Group {group['id']} Layer {l['id']} buy {order_status} (external cancel). Removing.")
            layers_to_delete_pending.append(l["id"])
            # ★ UNFREEZE: release reserved balance bila order cancel
            amt = l.get("amount_myr", 0.0)
            shared.global_state["frozen_myr"] = max(0.0, shared.global_state.get("frozen_myr", 0.0) - amt)
            logger.info(f"[{coin_id}] Unfroze RM{amt:.2f} (cancel). Frozen now: RM{shared.global_state['frozen_myr']:.2f}")
            state_changed = True

        else:
            # ── Order masih OPEN — smart price tracking ──
            #
            # LOGIK:
            #   Harga TURUN (≤ entry_price)  → BIARKAN selama mana pun (akan fill)
            #   Harga NAIK  (> entry_price) + 5 min → CANCEL
            #     └─ Signal masih BUY → RE-PLACE @ -0.1% dari current price baru
            #     └─ Signal dah habis → remove layer, tunggu signal baru
            #
            entry_price = l.get("entry_price", 0)
            current_price_now = shared.engine_state[coin_id].get("current_price", 0)
            age_sec = time.time() - l.get("created_at", time.time())

            # Harga NAIK above entry → limit BUY tak akan fill sampai harga turun balik
            price_above_entry = (current_price_now > 0 and entry_price > 0
                                 and current_price_now > entry_price)

            if price_above_entry and age_sec >= 300:
                # ★ Harga dah naik, pending 5+ minit → cancel dan re-evaluate
                logger.info(f"[{coin_id}] Group {group['id']} PENDING_BUY {buy_id}: "
                            f"Harga NAIK RM{current_price_now:.4f} > entry RM{entry_price:.4f} "
                            f"| pending {age_sec/60:.1f} min → CANCEL + re-evaluate")
                hata_api.cancel_order(f"{coin_id}_MYR", buy_id)

                last_signal = shared.engine_state[coin_id].get("last_signal", 0)
                if last_signal == 1 and current_price_now > 0:
                    # ★ Signal masih BUY → letak semula -0.1% dari current price baru
                    price_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("price", 0)
                    qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
                    trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
                    min_notional = hata_api.COIN_SCALES.get(coin_id, {}).get("min_notional", 10.0)

                    new_entry = round(current_price_now * 0.999, price_scale)
                    new_qty = round(trade_amount / new_entry, qty_scale)

                    if new_entry * new_qty >= min_notional:
                        logger.info(f"[{coin_id}] Signal masih BUY → RE-PLACE @ RM{new_entry:.{price_scale}f} "
                                    f"(-0.1% dari RM{current_price_now:.{price_scale}f})")
                        new_res = hata_api.place_limit_order(f"{coin_id}_MYR", "BUY", new_entry, new_qty)
                        if new_res.get("status") != "error":
                            new_order_id = str(new_res.get("data", {}).get("id", ""))
                            l["entry_price"] = new_entry
                            l["quantity"] = new_qty
                            l["buy_order_id"] = new_order_id
                            l["created_at"] = time.time()
                            l.pop("hata_buy_res", None)
                            shared.engine_state[coin_id]["last_cycle_entry"] = new_entry
                            logger.info(f"[{coin_id}] RE-PLACED PENDING_BUY {new_order_id} @ RM{new_entry:.{price_scale}f} ✓")
                        else:
                            logger.error(f"[{coin_id}] Re-place gagal: {new_res.get('message')} → remove layer")
                            amt = l.get("amount_myr", 0.0)
                            shared.global_state["frozen_myr"] = max(0.0, shared.global_state.get("frozen_myr", 0.0) - amt)
                            logger.info(f"[{coin_id}] Unfroze RM{amt:.2f} (re-place failed). Frozen now: RM{shared.global_state['frozen_myr']:.2f}")
                            layers_to_delete_pending.append(l["id"])
                    else:
                        logger.warning(f"[{coin_id}] Re-place notional terlalu kecil → remove layer")
                        amt = l.get("amount_myr", 0.0)
                        shared.global_state["frozen_myr"] = max(0.0, shared.global_state.get("frozen_myr", 0.0) - amt)
                        logger.info(f"[{coin_id}] Unfroze RM{amt:.2f} (notional too small). Frozen now: RM{shared.global_state['frozen_myr']:.2f}")
                        layers_to_delete_pending.append(l["id"])
                else:
                    # ★ Signal dah habis → remove layer, tunggu setup baru
                    logger.info(f"[{coin_id}] Signal TIDAK BUY lagi → remove pending layer, tunggu setup baru")
                    amt = l.get("amount_myr", 0.0)
                    shared.global_state["frozen_myr"] = max(0.0, shared.global_state.get("frozen_myr", 0.0) - amt)
                    logger.info(f"[{coin_id}] Unfroze RM{amt:.2f} (signal expired). Frozen now: RM{shared.global_state['frozen_myr']:.2f}")
                    layers_to_delete_pending.append(l["id"])
                state_changed = True

            elif price_above_entry:
                # Harga atas entry tapi < 5 minit lagi → tunggu
                remaining = 300 - age_sec
                logger.info(f"[{coin_id}] Group {group['id']} PENDING_BUY {buy_id}: "
                            f"Harga RM{current_price_now:.4f} > entry RM{entry_price:.4f} "
                            f"| Will cancel in {remaining/60:.1f} min lagi kalau tak fill")
            else:
                # ★ Harga TURUN atau dekat entry → BIARKAN selama mana pun
                direction = "TURUN ↓" if current_price_now < entry_price else "≈ DEKAT"
                logger.info(f"[{coin_id}] Group {group['id']} PENDING_BUY {buy_id}: "
                            f"Harga {direction} RM{current_price_now:.4f} ≤ entry RM{entry_price:.4f} "
                            f"| Biarkan, akan fill bila harga sampai level ini (age={age_sec/60:.1f}min)")

    # Remove cancelled / failed / signal-expired pending layers
    if layers_to_delete_pending:
        group["layers"] = [x for x in group.get("layers", []) if x.get("id") not in layers_to_delete_pending]
        state_changed = True

    # Refresh layers list after pending changes
    layers = group.get("layers", [])

    # ── Check HOLDING layers' individual sell orders ──
    layers_to_remove = []
    for l in layers:
        if l.get("status") != "HOLDING":
            continue

        sell_id = l.get("sell_order_id")
        if not sell_id:
            logger.info(f"[{coin_id}] Group {group['id']} Layer {l['id']}: HOLDING tapi tiada sell order. Placing...")
            placed_id = _grid_place_layer_sell(coin_id, l)
            if placed_id:
                logger.info(f"[{coin_id}] Group {group['id']} Layer {l['id']}: Sell placed OK ({placed_id})")
                shared.save_state()  # ★ Save immediately supaya sell_order_id persistent
            else:
                logger.error(f"[{coin_id}] Group {group['id']} Layer {l['id']}: Sell FAILED. Will retry next cycle (60s).")
            state_changed = True
            continue

        res = hata_api.get_order_status(sell_id)
        order_data = res.get("data")
        if not order_data:
            continue

        sell_status = order_data.get("status")

        if sell_status == "fulfilled":
            exec_info = _extract_hata_exec_data(coin_id, order_data)
            sell_received_myr = exec_info["actual_cost_myr"]
            sell_fee_myr = exec_info["fee_myr"]
            sell_fee_role = exec_info["fee_role"]
            buy_cost = l.get("actual_cost_myr", l.get("amount_myr", 0))
            buy_fee_myr = l.get("fee_myr", 0.0)
            real_pnl = sell_received_myr - buy_cost

            # P&L dikira dari Hata API sync (_sync_trade_history), bukan di sini
            logger.info(f"[{coin_id}] ★ Group {group['id']} Layer {l['id']} SELL FILLED! "
                        f"Buy RM{buy_cost:.2f} ({l.get('fee_role','?')} RM{buy_fee_myr:.4f}) "
                        f"| Sell RM{sell_received_myr:.2f} ({sell_fee_role} RM{sell_fee_myr:.4f}) "
                        f"| PnL RM{real_pnl:.4f}")
            try:
                ml_logger.log_trade_outcome(
                    coin_id=coin_id,
                    entry_price=l.get("entry_price", 0),
                    exit_price=float(order_data.get("price", 0)),
                    pnl_myr=real_pnl,
                    pnl_pct=real_pnl / buy_cost if buy_cost > 0 else 0,
                    hold_duration_min=int((time.time() - l.get("created_at", time.time())) / 60),
                    layers_used=1,
                    fee_total_myr=buy_fee_myr + sell_fee_myr
                )
            except Exception as ml_err:
                logger.error(f"[{coin_id}] ML log error: {ml_err}")

            layers_to_remove.append(l["id"])
            state_changed = True

        elif sell_status in ["cancelled", "rejected"]:
            logger.warning(f"[{coin_id}] Group {group['id']} Layer {l['id']} sell {sell_status}. Re-placing...")
            l["sell_order_id"] = None
            _grid_place_layer_sell(coin_id, l)
            state_changed = True

    # Remove completed layers
    if layers_to_remove:
        group["layers"] = [l for l in layers if l.get("id") not in layers_to_remove]
        layers = group["layers"]
        state_changed = True

        holding = [l for l in layers if l.get("status") == "HOLDING"]
        if holding:
            lowest_entry = min(l.get("entry_price", 0) for l in holding)
            _grid_update_standby_buy(coin_id, group, lowest_entry)
        else:
            # Group complete — cancel standby buy
            old_standby = group.get("standby_buy_order_id")
            if old_standby:
                hata_api.cancel_order(f"{coin_id}_MYR", old_standby)
                group["standby_buy_order_id"] = None
                group["standby_buy_price"] = 0.0
            logger.info(f"[{coin_id}] ★ Group {group['id']} COMPLETE. All layers sold.")

    # ── Check standby BUY fill ──
    standby_id = group.get("standby_buy_order_id")
    if standby_id:
        res = hata_api.get_order_status(standby_id)
        order_data = res.get("data")
        if order_data:
            buy_status = order_data.get("status")
            if buy_status == "fulfilled":
                exec_info = _extract_hata_exec_data(coin_id, order_data, 0)
                standby_price = group.get("standby_buy_price", 0)
                trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
                new_layer = {
                    "id": max((l.get("id", 0) for l in group.get("layers", [])), default=0) + 1,
                    "entry_price": standby_price,
                    "amount_myr": trade_amount,
                    "quantity": exec_info["exec_qty"],
                    "exec_qty": exec_info["exec_qty"],
                    "fee_qty": exec_info["fee_qty"],
                    "net_qty": exec_info["net_qty"],
                    "actual_cost_myr": exec_info["actual_cost_myr"],
                    "fee_myr": exec_info["fee_myr"],
                    "fee_role": exec_info["fee_role"],
                    "status": "HOLDING",
                    "buy_order_id": standby_id,
                    "sell_order_id": None,
                    "sell_target_price": 0.0,
                    "created_at": time.time()
                }
                group["layers"].append(new_layer)
                group["standby_buy_order_id"] = None
                group["standby_buy_price"] = 0.0
                logger.info(f"[{coin_id}] ★ Group {group['id']} CASCADE: Standby BUY filled @ RM{standby_price:.4f} "
                            f"net={exec_info['net_qty']} fee={exec_info['fee_role']} RM{exec_info['fee_myr']:.4f}")
                _grid_place_layer_sell(coin_id, new_layer)
                _grid_update_standby_buy(coin_id, group, standby_price)
                state_changed = True
            elif buy_status in ["cancelled", "rejected"]:
                logger.warning(f"[{coin_id}] Group {group['id']}: Standby BUY {standby_id} was {buy_status}. "
                               f"Will re-place below lowest holding layer.")
                group["standby_buy_order_id"] = None
                group["standby_buy_price"] = 0.0
                state_changed = True
                # ★ FIX: Auto re-place standby BUY if there are still HOLDING layers
                # Selagi ada layers HOLDING, standby BUY MESTI ada di bawah
                holding_now = [l for l in group.get("layers", []) if l.get("status") == "HOLDING"]
                if holding_now:
                    lowest = min(l.get("entry_price", 0) for l in holding_now)
                    logger.info(f"[{coin_id}] Group {group['id']}: Re-placing standby BUY below RM{lowest:.4f}...")
                    _grid_update_standby_buy(coin_id, group, lowest)

    # ★ SAFETY NET: Health check — group ada HOLDING layers tapi tiada standby BUY?
    # Ini boleh berlaku kalau API call gagal semasa letak standby.
    # Auto-repair: letak semula standby BUY di bawah lowest holding layer.
    holding_layers = [l for l in group.get("layers", []) if l.get("status") == "HOLDING"]
    has_standby = bool(group.get("standby_buy_order_id"))
    risk_level = shared.engine_state[coin_id].get("risk_level", 1)
    strategy = _get_strategy(coin_id, risk_level)
    if holding_layers and not has_standby and len(holding_layers) < strategy["max_layers"]:
        lowest_entry = min(l.get("entry_price", 0) for l in holding_layers)
        logger.warning(f"[{coin_id}] Group {group['id']}: ⚠ SAFETY NET — "
                       f"ada {len(holding_layers)} HOLDING layer(s) tapi tiada standby BUY! "
                       f"Auto-placing standby below RM{lowest_entry:.4f}...")
        _grid_update_standby_buy(coin_id, group, lowest_entry)
        state_changed = True

    return state_changed


# ─────────────────────────────────────────────
# GRID SYSTEM: Check ALL groups for one coin
# Called from check_orders() when system_mode == 'grid'
# ─────────────────────────────────────────────
def _check_grid_orders(coin_id: str) -> bool:
    """Check all groups for this coin. Returns True if any state changed."""
    groups = shared.engine_state[coin_id].get("groups", [])
    state_changed = False
    groups_to_remove = []

    for group in groups:
        changed = _check_grid_group(coin_id, group)
        if changed:
            state_changed = True
        # Mark group for removal if all layers sold
        if not group.get("layers"):
            groups_to_remove.append(group["id"])

    if groups_to_remove:
        shared.engine_state[coin_id]["groups"] = [
            g for g in groups if g["id"] not in groups_to_remove
        ]
        state_changed = True
        if not shared.engine_state[coin_id]["groups"]:
            # Reset last_cycle_entry so bot can seek new ML entry freely after group complete.
            # The user's concept: once ALL layers sold (group done), re-entry is unrestricted.
            # The 2% gap guard only applies when CREATING A NEW GROUP while existing group is active.
            shared.engine_state[coin_id]["last_cycle_entry"] = 0.0
            logger.info(f"[{coin_id}] ★ ALL GROUPS COMPLETE. last_cycle_entry reset. Seeking new ML entry freely...")

    return state_changed

# ─────────────────────────────────────────────
# Startup Recovery: Sync all layers/groups with Hata API
# Runs once on bot start / laptop restart
# ★ v5.6.6: Grid-aware — routes to grid or legacy DCA path
# ─────────────────────────────────────────────
def _startup_recovery_grid(coin_id: str) -> bool:
    """★ GRID MODE recovery: iterate groups[] → reconcile each layer with Hata API.
    Returns True if any state changed."""
    import hata_api

    groups = shared.engine_state[coin_id].get("groups", [])
    if not groups:
        return False

    state_changed = False
    groups_to_remove = []

    logger.info(f"[{coin_id}] RECOVERY (GRID): {len(groups)} group(s) to check...")

    for group in groups:
        layers = group.get("layers", [])
        if not layers:
            groups_to_remove.append(group["id"])
            continue

        layers_to_remove = []
        group_changed = False

        for l in layers:
            status = l.get("status", "HOLDING")

            # ── PENDING_BUY: check if filled/cancelled while bot offline ──
            if status == "PENDING_BUY":
                buy_id = l.get("buy_order_id")
                if not buy_id:
                    l["status"] = "HOLDING"
                    group_changed = True
                    continue

                res = hata_api.get_order_status(buy_id)
                order_data = res.get("data")
                if not order_data:
                    # Cannot reach Hata — keep, check at next 60s cycle
                    continue

                order_status = order_data.get("status")
                if order_status == "fulfilled":
                    logger.info(f"[{coin_id}] RECOVERY (GRID): Group {group['id']} Buy {buy_id} filled while offline!")
                    exec_info = _extract_hata_exec_data(coin_id, order_data, l.get("quantity", 0))
                    l["exec_qty"] = exec_info["exec_qty"]
                    l["fee_qty"] = exec_info["fee_qty"]
                    l["net_qty"] = exec_info["net_qty"]
                    l["actual_cost_myr"] = exec_info["actual_cost_myr"]
                    l["fee_myr"] = exec_info["fee_myr"]
                    l["fee_role"] = exec_info["fee_role"]
                    l["status"] = "HOLDING"
                    group_changed = True
                    # Place sell for this layer
                    _grid_place_layer_sell(coin_id, l)

                elif order_status in ["cancelled", "rejected"]:
                    logger.info(f"[{coin_id}] RECOVERY (GRID): Group {group['id']} Buy {buy_id} was {order_status}. Removing layer.")
                    layers_to_remove.append(l["id"])
                    group_changed = True

                else:
                    # Still open — patch created_at if missing, cancel if stuck >5min
                    if "created_at" not in l:
                        l["created_at"] = time.time()
                        group_changed = True
                    age_sec = time.time() - l.get("created_at", time.time())
                    if age_sec > 300:
                        logger.info(f"[{coin_id}] RECOVERY (GRID): Group {group['id']} Buy {buy_id} stuck >{age_sec/60:.1f}min. Cancelling...")
                        hata_api.cancel_order(f"{coin_id}_MYR", buy_id)
                        layers_to_remove.append(l["id"])
                        group_changed = True

            # ── HOLDING: ensure fee data + sell order exist ──
            elif status == "HOLDING":
                # Re-fetch fee data if missing
                if "fee_role" not in l or "fee_myr" not in l:
                    buy_id = l.get("buy_order_id")
                    if buy_id:
                        logger.info(f"[{coin_id}] RECOVERY (GRID): Re-fetching fee data for Group {group['id']} Layer {l.get('id')}...")
                        buy_res = hata_api.get_order_status(buy_id)
                        buy_data = buy_res.get("data")
                        if buy_data and buy_data.get("status") == "fulfilled":
                            exec_info = _extract_hata_exec_data(coin_id, buy_data, l.get("quantity", 0))
                            l["exec_qty"] = exec_info["exec_qty"]
                            l["fee_qty"] = exec_info["fee_qty"]
                            l["net_qty"] = exec_info["net_qty"]
                            l["actual_cost_myr"] = exec_info["actual_cost_myr"]
                            l["fee_myr"] = exec_info["fee_myr"]
                            l["fee_role"] = exec_info["fee_role"]
                            group_changed = True
                        else:
                            l["fee_myr"] = 0.0
                            l["fee_role"] = "unknown"
                            group_changed = True
                    else:
                        l["fee_myr"] = 0.0
                        l["fee_role"] = "unknown"
                        group_changed = True

                # Ensure sell order exists for this HOLDING layer
                sell_id = l.get("sell_order_id")
                if sell_id:
                    # Verify sell is still active
                    res = hata_api.get_order_status(sell_id)
                    order_data = res.get("data")
                    if order_data:
                        sell_status = order_data.get("status")
                        if sell_status == "fulfilled":
                            # Sell filled while bot was offline!
                            exec_info = _extract_hata_exec_data(coin_id, order_data)
                            sell_received = exec_info["actual_cost_myr"]
                            buy_cost = l.get("actual_cost_myr", l.get("amount_myr", 0))
                            pnl = sell_received - buy_cost
                            logger.info(f"[{coin_id}] RECOVERY (GRID): Group {group['id']} Layer {l['id']} sell filled while offline! PnL: RM{pnl:.2f}")
                            layers_to_remove.append(l["id"])
                            group_changed = True
                        elif sell_status in ["cancelled", "rejected"]:
                            # Sell was cancelled — clear and re-place
                            logger.info(f"[{coin_id}] RECOVERY (GRID): Group {group['id']} Layer {l['id']} sell was {sell_status}. Re-placing...")
                            l["sell_order_id"] = None
                            _grid_place_layer_sell(coin_id, l)
                            group_changed = True
                else:
                    # No sell order — place one
                    logger.info(f"[{coin_id}] RECOVERY (GRID): Group {group['id']} Layer {l['id']} HOLDING but no sell. Placing...")
                    _grid_place_layer_sell(coin_id, l)
                    group_changed = True

            # ── OPEN / PENDING_SELL: legacy statuses → convert to HOLDING ──
            elif status in ["OPEN", "PENDING_SELL"]:
                if status == "PENDING_SELL":
                    old_sell = l.get("sell_order_id")
                    if old_sell:
                        hata_api.cancel_order(f"{coin_id}_MYR", old_sell)
                        logger.info(f"[{coin_id}] RECOVERY (GRID): Cancelled old per-layer sell {old_sell}")
                if "net_qty" not in l:
                    sell_qty = l.get("sell_quantity", l.get("quantity", 0))
                    l["net_qty"] = sell_qty
                    l["exec_qty"] = l.get("quantity", 0)
                    l["fee_qty"] = l.get("quantity", 0) - sell_qty if sell_qty < l.get("quantity", 0) else 0
                    l["actual_cost_myr"] = l.get("amount_myr", 0)
                l["status"] = "HOLDING"
                _grid_place_layer_sell(coin_id, l)
                group_changed = True

        # Remove completed/cancelled layers
        if layers_to_remove:
            group["layers"] = [x for x in group.get("layers", []) if x.get("id") not in layers_to_remove]
            group_changed = True

        if group_changed:
            state_changed = True

        # Ensure standby BUY exists for group with HOLDING layers
        holding_layers = [x for x in group.get("layers", []) if x.get("status") == "HOLDING"]
        if holding_layers:
            standby_id = group.get("standby_buy_order_id")
            if standby_id:
                # Verify standby is still active
                res = hata_api.get_order_status(standby_id)
                order_data = res.get("data")
                if order_data:
                    sb_status = order_data.get("status")
                    if sb_status == "fulfilled":
                        # Standby filled while offline — create new layer
                        exec_info = _extract_hata_exec_data(coin_id, order_data, 0)
                        standby_price = group.get("standby_buy_price", 0)
                        trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
                        new_layer = {
                            "id": max((x.get("id", 0) for x in group.get("layers", [])), default=0) + 1,
                            "entry_price": standby_price,
                            "amount_myr": trade_amount,
                            "quantity": exec_info["exec_qty"],
                            "exec_qty": exec_info["exec_qty"],
                            "fee_qty": exec_info["fee_qty"],
                            "net_qty": exec_info["net_qty"],
                            "actual_cost_myr": exec_info["actual_cost_myr"],
                            "fee_myr": exec_info["fee_myr"],
                            "fee_role": exec_info["fee_role"],
                            "status": "HOLDING",
                            "buy_order_id": standby_id,
                            "sell_order_id": None,
                            "sell_target_price": 0.0,
                            "created_at": time.time()
                        }
                        group["layers"].append(new_layer)
                        logger.info(f"[{coin_id}] RECOVERY (GRID): Group {group['id']} standby BUY filled @ RM{standby_price:.4f}!")
                        _grid_place_layer_sell(coin_id, new_layer)
                        group["standby_buy_order_id"] = None
                        group["standby_buy_price"] = 0.0
                        holding_layers = [x for x in group.get("layers", []) if x.get("status") == "HOLDING"]
                        state_changed = True
                    elif sb_status in ["cancelled", "rejected"]:
                        group["standby_buy_order_id"] = None
                        group["standby_buy_price"] = 0.0
                        state_changed = True

            # After all layer recovery, ensure standby exists
            holding_now = [x for x in group.get("layers", []) if x.get("status") == "HOLDING"]
            has_standby = bool(group.get("standby_buy_order_id"))
            strategy = _get_strategy(coin_id, shared.engine_state[coin_id].get("risk_level", 1))
            if holding_now and not has_standby and len(holding_now) < strategy["max_layers"]:
                lowest = min(x.get("entry_price", 0) for x in holding_now)
                logger.info(f"[{coin_id}] RECOVERY (GRID): Group {group['id']} has {len(holding_now)} HOLDING but no standby. Placing below RM{lowest:.4f}...")
                _grid_update_standby_buy(coin_id, group, lowest)
                state_changed = True
        else:
            # No holding layers left — mark group for removal
            if not [x for x in group.get("layers", []) if x.get("status") == "PENDING_BUY"]:
                groups_to_remove.append(group["id"])

    # Remove empty/complete groups
    if groups_to_remove:
        shared.engine_state[coin_id]["groups"] = [
            g for g in shared.engine_state[coin_id].get("groups", [])
            if g["id"] not in groups_to_remove
        ]
        state_changed = True
        if not shared.engine_state[coin_id]["groups"]:
            shared.engine_state[coin_id]["last_cycle_entry"] = 0.0
            logger.info(f"[{coin_id}] RECOVERY (GRID): All groups complete. last_cycle_entry reset.")

    return state_changed


def _startup_recovery_legacy(coin_id: str) -> bool:
    """Legacy DCA recovery path. Only used when system_mode == 'dca'.
    Returns True if any state changed."""
    import hata_api

    layers = shared.engine_state[coin_id].get("layers", [])
    if not layers:
        return False

    active_layers = []
    coin_changed = False
    needs_consolidated_sell = False
    old_sell_ids_to_cancel = []
    logger.info(f"[{coin_id}] RECOVERY (LEGACY DCA): {len(layers)} layer(s)...")

    for l in layers:
        status = l.get("status", "OPEN")

        if status == "PENDING_SELL":
            sell_id = l.get("sell_order_id")
            if sell_id:
                res = hata_api.get_order_status(sell_id)
                order_data = res.get("data")
                if order_data and order_data.get("status") == "fulfilled":
                    exec_data = _extract_hata_exec_data(coin_id, order_data)
                    sell_received = exec_data.get("actual_cost_myr", 0)
                    buy_cost = l.get("actual_cost_myr", l.get("amount_myr", 0))
                    pnl = sell_received - buy_cost
                    logger.info(f"[{coin_id}] RECOVERY: Old sell {sell_id} filled! PnL: RM{pnl:.2f}")
                    coin_changed = True
                    continue
                elif order_data and order_data.get("status") in ["cancelled", "rejected"]:
                    logger.info(f"[{coin_id}] RECOVERY: Old sell {sell_id} cancelled. → HOLDING.")
                else:
                    old_sell_ids_to_cancel.append(sell_id)

            if "net_qty" not in l:
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
                active_layers.append(l)
                continue

            order_status = order_data.get("status")
            if order_status == "fulfilled":
                logger.info(f"[{coin_id}] RECOVERY: Buy {buy_id} filled!")
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
                logger.info(f"[{coin_id}] RECOVERY: Buy {buy_id} {order_status}. Removing.")
                coin_changed = True
            else:
                if "created_at" not in l:
                    l["created_at"] = time.time()
                    coin_changed = True
                age_sec = time.time() - l["created_at"]
                if age_sec > 300:
                    logger.info(f"[{coin_id}] RECOVERY: Buy {buy_id} stuck >{age_sec/60:.1f}min. Cancelling...")
                    hata_api.cancel_order(f"{coin_id}_MYR", buy_id)
                    coin_changed = True
                else:
                    active_layers.append(l)

        elif status == "HOLDING":
            if "fee_role" not in l or "fee_myr" not in l:
                buy_id = l.get("buy_order_id")
                if buy_id:
                    buy_res = hata_api.get_order_status(buy_id)
                    buy_data = buy_res.get("data")
                    if buy_data and buy_data.get("status") == "fulfilled":
                        exec_info = _extract_hata_exec_data(coin_id, buy_data, l.get("quantity", 0))
                        l.update({k: exec_info[k] for k in ["exec_qty", "fee_qty", "net_qty", "actual_cost_myr", "fee_myr", "fee_role"]})
                        coin_changed = True
                    else:
                        l["fee_myr"] = 0.0
                        l["fee_role"] = "unknown"
                        coin_changed = True
                else:
                    l["fee_myr"] = 0.0
                    l["fee_role"] = "unknown"
                    coin_changed = True
            active_layers.append(l)
            needs_consolidated_sell = True

        elif status == "OPEN":
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

    for sell_id in old_sell_ids_to_cancel:
        hata_api.cancel_order(f"{coin_id}_MYR", sell_id)
        logger.info(f"[{coin_id}] RECOVERY: Cancelled old sell {sell_id}")

    if coin_changed:
        shared.engine_state[coin_id]["layers"] = active_layers

    if needs_consolidated_sell:
        holding_count = len([l for l in active_layers if l.get('status') == 'HOLDING'])
        logger.info(f"[{coin_id}] RECOVERY: Consolidated sell for {holding_count} HOLDING layers...")
        _place_consolidated_sell(coin_id)

    current_layers = shared.engine_state[coin_id].get("layers", [])
    has_pending = any(l.get("status") == "PENDING_BUY" for l in current_layers)
    holding_in_recovery = [l for l in current_layers if l.get("status") == "HOLDING"]
    if holding_in_recovery and not has_pending:
        strategy = _get_strategy(coin_id, shared.engine_state[coin_id].get("risk_level", 1))
        if len(current_layers) < strategy["max_layers"]:
            last_entry = holding_in_recovery[-1].get("entry_price", 0)
            if last_entry > 0:
                logger.info(f"[{coin_id}] RECOVERY CASCADE: DCA BUY below RM{last_entry:.4f}")
                _place_next_dca_buy(coin_id, last_entry)

    return coin_changed


async def startup_recovery():
    """Reconcile all layers/groups with actual Hata API status on bot start.
    ★ v5.6.6: Grid-aware — routes to _startup_recovery_grid or _startup_recovery_legacy
    based on each coin's system_mode setting."""
    loop = asyncio.get_running_loop()
    logger.info("=" * 60)
    logger.info("STARTUP RECOVERY: Syncing all 5 coin layers with Hata API...")
    logger.info("=" * 60)

    def _recover():
        state_changed = False

        # ★ Reset frozen_myr on startup — will be recalculated from active PENDING_BUY layers
        shared.global_state["frozen_myr"] = 0.0

        for coin_id in shared.engine_state:
            system_mode = shared.engine_state[coin_id].get("system_mode", "grid")
            if system_mode == "grid":
                changed = _startup_recovery_grid(coin_id)
            else:
                changed = _startup_recovery_legacy(coin_id)
            if changed:
                state_changed = True

        # ★ Recalculate frozen_myr from all active PENDING_BUY layers across all groups
        total_frozen = 0.0
        for coin_id in shared.engine_state:
            for group in shared.engine_state[coin_id].get("groups", []):
                for l in group.get("layers", []):
                    if l.get("status") == "PENDING_BUY":
                        total_frozen += l.get("amount_myr", 0.0)
            # Also check legacy layers
            for l in shared.engine_state[coin_id].get("layers", []):
                if l.get("status") == "PENDING_BUY":
                    total_frozen += l.get("amount_myr", 0.0)
        shared.global_state["frozen_myr"] = total_frozen
        logger.info(f"STARTUP RECOVERY: Recalculated frozen_myr = RM{total_frozen:.2f}")

        if state_changed:
            shared.save_state()

        # ★ Sync full trade history from Hata API for accurate P&L
        _sync_trade_history()

        logger.info("=" * 60)
        logger.info("STARTUP RECOVERY: Complete. Bot is now live.")
        logger.info("=" * 60)

    await loop.run_in_executor(None, _recover)


# ─────────────────────────────────────────────
# Trade History Sync: Fetch ALL trades from Hata API
# Calculates accurate P&L from actual buy/sell records
# ─────────────────────────────────────────────
def _sync_trade_history():
    """Fetch trade history dari Hata API dan kira P&L.
    Simple: sell_revenue - buy_cost - fees. Data dari 2 July onwards."""
    import hata_api
    from datetime import datetime

    logger.info("=" * 60)
    logger.info("TRADE HISTORY SYNC: Fetching from Hata API (dari 2 July)...")
    logger.info("=" * 60)

    # Start dari 2 July 2026 00:00:00 MYT (UTC+8)
    start_timestamp = "1782921600"  # 2026-07-02 00:00:00 MYT

    coins = ["BTC", "ETH", "SOL", "XRP", "LTC"]

    for coin_id in coins:
        pair = f"{coin_id}_MYR"
        try:
            # Fetch SEMUA fulfilled trades dari 2 July (paginated)
            # Trade history API HANYA return executed/fulfilled trades
            trades = hata_api.get_all_trade_history(pair, start_time=start_timestamp)

            if not trades:
                logger.info(f"[{coin_id}] No fulfilled trades since July 2.")
                shared.engine_state[coin_id]["trade_history"] = {
                    "total_trades": 0, "buy_count": 0, "sell_count": 0,
                    "total_buy_cost": 0, "total_sell_revenue": 0,
                    "total_fees": 0, "pnl": 0,
                    "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                shared.engine_state[coin_id]["total_pnl"] = 0.0
                continue

            # Simple: kumpul semua buy cost, sell revenue, fees
            # Hata trade fields (from API docs): is_buy, price, qty, fee, is_maker, trade_id, created_at
            total_buy_cost = 0.0
            total_sell_revenue = 0.0
            total_fees_myr = 0.0
            buy_count = 0
            sell_count = 0

            for t in trades:
                is_buy = t.get("is_buy")          # boolean: True=BUY, False=SELL
                price = float(t.get("price", 0))
                qty = float(t.get("qty", 0))
                fee = float(t.get("fee", 0))
                myr_amount = price * qty           # Hata tak ada quote_qty dalam trade history

                # Fee conversion ke MYR:
                # BUY → fee dalam coin (e.g. ETH), convert: fee × price
                # SELL → fee dalam MYR, guna terus
                if is_buy:
                    fee_myr = fee * price
                else:
                    fee_myr = fee

                total_fees_myr += fee_myr

                if is_buy:
                    total_buy_cost += myr_amount
                    buy_count += 1
                else:
                    total_sell_revenue += myr_amount
                    sell_count += 1

            # ★ P&L = SELL - BUY - FEES. Simple. Direct dari Hata fulfilled trades.
            pnl = total_sell_revenue - total_buy_cost - total_fees_myr

            # Set terus — ini satu-satunya sumber kebenaran
            shared.engine_state[coin_id]["total_pnl"] = round(pnl, 4)

            shared.engine_state[coin_id]["trade_history"] = {
                "buy_count": buy_count,
                "sell_count": sell_count,
                "total_trades": len(trades),
                "total_buy_cost": round(total_buy_cost, 4),
                "total_sell_revenue": round(total_sell_revenue, 4),
                "total_fees": round(total_fees_myr, 4),
                "pnl": round(pnl, 4),
                "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "oldest_trade": trades[-1].get("created_at", "") if trades else "",
                "newest_trade": trades[0].get("created_at", "") if trades else ""
            }

            logger.info(f"[{coin_id}] SYNC: {len(trades)} fulfilled trades | "
                        f"Buy: RM{total_buy_cost:.2f} ({buy_count}) | "
                        f"Sell: RM{total_sell_revenue:.2f} ({sell_count}) | "
                        f"Fees: RM{total_fees_myr:.4f} | "
                        f"P&L: RM{pnl:.2f}")

        except Exception as e:
            logger.error(f"[{coin_id}] SYNC ERROR: {e}")

    shared.save_state()
    logger.info("TRADE HISTORY SYNC: Complete.")


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
                # ★ BUG FIX: Don't overwrite bot's internal frozen_myr with Hata's value.
                # frozen_myr is managed internally by the bot for pending orders:
                #   +amount when order placed (process_kline), -amount when fills/cancel (_check_grid_group)
                # Hata's frozen value is stored separately for display/debug only.
                shared.global_state["hata_frozen_myr"] = froz
            shared.global_state["usdt_myr_rate"] = rate

            # 3. Check all pending orders for all 5 coins (NEW CONSOLIDATED FLOW)
            def check_orders():
                state_changed = False
                for coin_id in shared.engine_state:
                    # ★ GRID MODE: Use new grid order system
                    system_mode = shared.engine_state[coin_id].get("system_mode", "grid")
                    if system_mode == "grid":
                        changed = _check_grid_orders(coin_id)
                        if changed:
                            shared.save_state()
                        # ★ BUG FIX: Skip legacy DCA code entirely when in grid mode.
                        # Old DCA code (below) operates on `layers[]` which is a legacy array.
                        # Grid mode uses `groups[]` exclusively — mixing them causes double-entry.
                        continue
                        
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
                                    l["fee_myr"] = exec_info["fee_myr"]
                                    l["fee_role"] = exec_info["fee_role"]
                                    l["status"] = "HOLDING"
                                    coin_changed = True
                                    needs_consolidated_sell = True
                                    # ★ Track for cascade: remember this layer just filled
                                    l["_just_filled"] = True
                                    active_layers.append(l)
                                    logger.info(f"[{coin_id}] Layer {l['id']} → HOLDING | "
                                                f"exec: {exec_info['exec_qty']}, net: {exec_info['net_qty']}, "
                                                f"fee: {exec_info['fee_qty']} ({exec_info['fee_role']}), "
                                                f"cost: RM{exec_info['actual_cost_myr']:.2f}")

                                elif order_status in ["cancelled", "rejected"]:
                                    logger.info(f"[{coin_id}] Buy {buy_id} was {order_status}. Removing layer.")
                                    coin_changed = True
                                    # Do NOT append — layer removed

                                else:
                                    # Still active — check if cascade or first-entry
                                    if "created_at" not in l:
                                        l["created_at"] = time.time()
                                        coin_changed = True
                                        logger.info(f"[{coin_id}] Patched created_at for buy {buy_id}.")

                                    age_sec = time.time() - l["created_at"]

                                    # ★ FIX: Cascade standby orders (HOLDING layers exist) → NO timeout
                                    # Must stay alive until sell fills or they fill themselves
                                    # Only first-entry (no HOLDING layers) gets auto-cancelled
                                    has_holding = any(
                                        ll.get("status") == "HOLDING"
                                        for ll in layers
                                    )

                                    if has_holding:
                                        logger.info(f"[{coin_id}] Buy {buy_id} is CASCADE standby "
                                                    f"(age {age_sec/60:.1f} min) — keeping alive until trigger.")
                                        active_layers.append(l)
                                    elif age_sec > 300:
                                        logger.info(f"[{coin_id}] Buy {buy_id} stuck >{age_sec/60:.1f} min "
                                                    f"(first-entry, no HOLDING). Auto-cancelling...")
                                        cancel_res = hata_api.cancel_order(f"{coin_id}_MYR", buy_id)
                                        logger.info(f"[{coin_id}] Cancel result: {cancel_res}")
                                        coin_changed = True
                                    else:
                                        remaining = 300 - age_sec
                                        logger.info(f"[{coin_id}] Buy {buy_id} active (first-entry). "
                                                    f"Auto-cancel in {remaining/60:.1f} min if unfilled.")
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
                                # P&L dikira dari Hata API sync, bukan di sini
                                
                                logger.info(f"[{coin_id}] ★ CONSOLIDATED SELL FILLED! ★")
                                logger.info(f"[{coin_id}]   Sold: RM{sell_received_myr:.2f} | Cost: RM{total_buy_cost:.2f} | PnL: RM{real_pnl:.2f}")
                                
                                # ★ ML PIPELINE: Log trade outcome for this coin's learning
                                try:
                                    # Calculate hold duration from earliest layer
                                    earliest_created = min(
                                        l.get("created_at", time.time()) for l in holding_layers
                                    )
                                    hold_duration = int((time.time() - earliest_created) / 60)
                                    total_fees = shared.engine_state[coin_id].get("total_buy_fees_myr", 0)
                                    avg_entry = total_buy_cost / sum(
                                        l.get("net_qty", l.get("quantity", 0)) for l in holding_layers
                                    ) if holding_layers else 0
                                    pnl_pct = (real_pnl / total_buy_cost) if total_buy_cost > 0 else 0
                                    
                                    ml_logger.log_trade_outcome(
                                        coin_id=coin_id,
                                        entry_price=avg_entry,
                                        exit_price=float(order_data.get("price", 0)),
                                        pnl_myr=real_pnl,
                                        pnl_pct=pnl_pct,
                                        hold_duration_min=hold_duration,
                                        layers_used=len(holding_layers),
                                        fee_total_myr=total_fees
                                    )
                                except Exception as ml_err:
                                    logger.error(f"[{coin_id}] ML log_trade_outcome error: {ml_err}")
                                
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

                    # ★ CASCADE: Run ALWAYS (not just when needs_consolidated_sell)
                    # Re-read layers AFTER consolidated sell to get accurate state
                    current_layers = shared.engine_state[coin_id].get("layers", [])
                    just_filled = [l for l in current_layers if l.get("_just_filled")]
                    if just_filled:
                        # Clean up the _just_filled flag first
                        for l in just_filled:
                            l.pop("_just_filled", None)

                        # Re-read AFTER cleanup to get accurate counts
                        has_pending = any(l.get("status") == "PENDING_BUY" for l in current_layers)
                        holding_count = len([l for l in current_layers if l.get("status") == "HOLDING"])
                        total_layers = len(current_layers)
                        risk_level = shared.engine_state[coin_id].get("risk_level", 1)
                        strategy = _get_strategy(coin_id, risk_level)

                        logger.info(f"[{coin_id}] CASCADE CHECK: total={total_layers}, holding={holding_count}, "
                                    f"has_pending={has_pending}, max={strategy['max_layers']}")

                        if has_pending:
                            logger.info(f"[{coin_id}] CASCADE: Skipping — already has a PENDING_BUY.")
                        elif total_layers >= strategy["max_layers"]:
                            logger.info(f"[{coin_id}] CASCADE: Skipping — max layers ({strategy['max_layers']}) reached.")
                        else:
                            # Use the lowest/latest filled layer's entry price
                            last_filled = just_filled[-1]
                            last_entry = last_filled.get("entry_price", 0)
                            if last_entry > 0:
                                logger.info(f"[{coin_id}] ★ CASCADE: Layer {last_filled['id']} filled → "
                                            f"auto-pending BUY for Layer {total_layers + 1} below RM{last_entry:.4f}")
                                _place_next_dca_buy(coin_id, last_entry)
                                state_changed = True
                            else:
                                logger.warning(f"[{coin_id}] CASCADE: Cannot cascade — last_entry is 0")

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
# Background: Check retrain triggers every hour
# ─────────────────────────────────────────────
async def retrain_check_loop():
    """Check every hour if any coin needs retraining."""
    await asyncio.sleep(120)  # Wait 2 minutes after startup before first check
    while True:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _run_retrain_check)
        except Exception as e:
            logger.error(f"Retrain check loop error: {e}")
        await asyncio.sleep(3600)  # Check every hour


def _run_retrain_check():
    """Run retrain check in executor (blocking)."""
    try:
        from ml_retrain import check_and_retrain_all
        check_and_retrain_all()
    except Exception as e:
        logger.error(f"Retrain check error: {e}")


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
            base_cols = ['open', 'high', 'low', 'close', 'volume', 'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 'Volume_ROC']
            extra_cols = (
                [c for c in feature_cols if c.startswith('BB')] +
                [c for c in feature_cols if c.startswith('MACD')] +
                [c for c in feature_cols if c.startswith('STOCH')] +
                [c for c in feature_cols if c.startswith('ATR')] +
                (['VWAP_D'] if 'VWAP_D' in feature_cols else (['VWAP'] if 'VWAP' in feature_cols else [])) +
                [c for c in ['Volatility_20', 'Trend_Strength', 'RSI_Slope', 'Volume_SMA_Ratio',
                             'Body_Size', 'Upper_Shadow', 'Lower_Shadow', 'Price_Position']
                 if c in feature_cols]
            )
            X = latest[base_cols + extra_cols]

            probs = model.predict_proba(X)
            golden_prob = float(probs[0, 1])

            shared.engine_state[coin_id]["confidence"] = golden_prob * 100

            # ★ ML PIPELINE: Use adaptive threshold per coin (not hardcoded 0.60)
            threshold = shared.engine_state[coin_id].get("adaptive_threshold", 0.60)
            
            # ★ ML PIPELINE: Log prediction for this coin's learning
            try:
                model_ver = shared.engine_state[coin_id].get("model_version", "v1")
                signal_val = 1 if golden_prob > threshold else 0
                ml_logger.log_prediction(
                    coin_id=coin_id,
                    features_dict=X.iloc[0].to_dict(),
                    confidence=golden_prob,
                    signal=signal_val,
                    current_price=float(shared.engine_state[coin_id]["current_price"]),
                    model_version=model_ver
                )
            except Exception as ml_err:
                logger.error(f"[{coin_id}] ML log_prediction error: {ml_err}")

            if golden_prob > threshold:
                logger.info(f"[{coin_id}] GOLDEN ENTRY SIGNAL! Confidence: {golden_prob*100:.2f}%")
                shared.engine_state[coin_id]["last_signal"] = 1

                if shared.engine_state[coin_id]["is_auto"]:
                    risk_level = shared.engine_state[coin_id].get("risk_level", 1)
                    balance = shared.global_state["balance_myr"]
                    trade_amount = shared.engine_state[coin_id].get("trade_amount_myr", 50.0)
                    current_price = shared.engine_state[coin_id]["current_price"]
                    strategy = _get_strategy(coin_id, risk_level)
                    can_buy = True

                    # ★ MULTI-GROUP ENTRY LOGIC
                    groups = shared.engine_state[coin_id].get("groups", [])
                    max_groups = shared.engine_state[coin_id].get("max_groups", 3)
                    new_group_gap = shared.engine_state[coin_id].get("new_group_gap_pct", 0.02)

                    if len(groups) >= max_groups:
                        can_buy = False
                        logger.info(f"[{coin_id}] Skipping: Max groups ({max_groups}) reached.")
                    elif len(groups) > 0:
                        # Check distance from lowest active entry
                        all_entries = [l.get("entry_price", 0) for g in groups for l in g.get("layers", [])]
                        if all_entries:
                            lowest_entry = min(all_entries)
                            min_required_price = lowest_entry * (1.0 - new_group_gap)
                            if current_price > min_required_price:
                                can_buy = False
                                logger.info(f"[{coin_id}] Skipping: Price RM{current_price:.4f} not >= {new_group_gap*100:.1f}% below lowest layer RM{lowest_entry:.4f}. Need <= RM{min_required_price:.4f}.")

                    # ★ NOTE: last_cycle_entry guard ONLY applies when there are ACTIVE groups.
                    # When groups=[], bot enters freely based on ML signal (cycle is complete, no cooldown).
                    # The 2% gap is ONLY to prevent adding a new group too close to existing active group.
                    # This check (above) already handles that in the elif len(groups) > 0 block.
                    # DO NOT add another guard here for groups=[] — it breaks scalping flow.

                    # ★ BALANCE CHECK: guna available = total - frozen
                    # frozen_myr dikira dari semua PENDING_BUY yang sedang menunggu fill
                    # Ini elak race condition bila 5 coins signal serentak
                    frozen = shared.global_state.get("frozen_myr", 0.0)
                    available_balance = balance - frozen

                    if can_buy and trade_amount <= available_balance and current_price > 0:
                        import hata_api
                        qty_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("qty", 4)
                        price_scale = hata_api.COIN_SCALES.get(coin_id, {}).get("price", 0)
                        min_notional = hata_api.COIN_SCALES.get(coin_id, {}).get("min_notional", 10.0)

                        # ★ First entry: limit 0.1% BAWAH current price
                        # Lebih cepat fill vs exact current_price, masih MAKER 0% fee
                        # (order masuk order book dulu, harga cuma perlu turun sikit je)
                        ENTRY_OFFSET_PCT = 0.001
                        entry_price = round(current_price * (1.0 - ENTRY_OFFSET_PCT), price_scale)

                        quantity = round(trade_amount / entry_price, qty_scale)
                        actual_notional = round(quantity * entry_price, 4)

                        # ★ Pre-check: warn if notional might be too small
                        if actual_notional < min_notional:
                            logger.warning(
                                f"[{coin_id}] Skipping BUY: Notional RM{actual_notional:.4f} < min RM{min_notional:.2f}. "
                                f"Increase trade_amount_myr (current: RM{trade_amount:.2f}) to at least RM{min_notional:.2f}."
                            )
                        else:
                            logger.info(f"[{coin_id}] FIRST ENTRY LIMIT BUY RM{trade_amount:.2f} "
                                        f"@ RM{entry_price:.{price_scale}f} (-0.1% dari RM{current_price:.{price_scale}f}) "
                                        f"| qty={quantity} | MAKER 0%")
                            hata_res = hata_api.place_limit_order(f"{coin_id}_MYR", "BUY", entry_price, quantity)

                            if hata_res.get("status") == "error":
                                err_code = hata_res.get("code", "")
                                if err_code == "min_notional":
                                    logger.warning(f"[{coin_id}] Order blocked (min notional): {hata_res.get('message')}")
                                else:
                                    logger.error(f"[{coin_id}] Hata API Error: {hata_res.get('message')}")
                            else:
                                order_id = hata_res.get("data", {}).get("id")
                                new_layer = {
                                    "id": 1,
                                    "entry_price": entry_price,
                                    "amount_myr": trade_amount,
                                    "quantity": quantity,
                                    "status": "PENDING_BUY",
                                    "buy_order_id": str(order_id),
                                    "hata_buy_res": hata_res,
                                    "created_at": time.time(),
                                    "sell_order_id": None,
                                    "sell_target_price": 0.0
                                }
                                
                                new_group = {
                                    "id": max([g.get("id", 0) for g in groups], default=0) + 1,
                                    "layers": [new_layer],
                                    "standby_buy_order_id": None,
                                    "standby_buy_price": 0.0,
                                    "created_at": time.time()
                                }
                                
                                shared.engine_state[coin_id]["groups"].append(new_group)
                                shared.engine_state[coin_id]["last_cycle_entry"] = entry_price
                                # ★ FREEZE balance segera supaya coin lain nampak balance berkurang
                                shared.global_state["frozen_myr"] = shared.global_state.get("frozen_myr", 0.0) + trade_amount
                                shared.save_state()
                                logger.info(f"[{coin_id}] NEW GROUP {new_group['id']} started! "
                                            f"PENDING_BUY Order {order_id} @ RM{entry_price:.{price_scale}f} "
                                            f"(-0.1% dari market RM{current_price:.{price_scale}f}) "
                                            f"| Frozen: RM{shared.global_state['frozen_myr']:.2f} "
                                            f"| Available: RM{available_balance - trade_amount:.2f}")

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

    # ★ Step 3: Start ML retrain check loop (every hour)
    asyncio.create_task(retrain_check_loop())

    # ★ Step 4: Connect to Binance WebSocket for live candle data
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
