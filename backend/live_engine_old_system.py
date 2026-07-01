# ═══════════════════════════════════════════════════════════
# OLD SYSTEM BACKUP — DCA Consolidated Sell (v5.4.x)
# ═══════════════════════════════════════════════════════════
# Sistem lama: 1 consolidated sell untuk semua layers
# Gantikan dengan: Grid Paired Orders (individual sell per layer)
# Simpan di sini sebagai rujukan / fallback
# ═══════════════════════════════════════════════════════════

import logging
import shared

logger = logging.getLogger(__name__)


def truncate_float(val: float, decimals: int) -> float:
    """Truncate float value to a specific number of decimal places without rounding up."""
    eps = 1e-9
    factor = 10 ** decimals
    return int((val + eps) * factor) / factor


def _extract_hata_exec_data(coin_id: str, order_data: dict, fallback_qty: float = 0.0) -> dict:
    """Extract actual executed quantity, fees, and cost from Hata API order data.
    Returns dict with: exec_qty, fee_qty, net_qty, actual_cost_myr, fee_role"""
    exec_qty = float(order_data.get("exec_qty", fallback_qty))
    cummul_quote = float(order_data.get("cummul_quote_qty", 0.0))

    trades = order_data.get("trades", [])
    fee_qty = 0.0
    fee_role = "unknown"
    for t in trades:
        if t.get("fee_asset") == coin_id:
            fee_qty += float(t.get("fee", 0.0))
        if t.get("is_maker") is True:
            fee_role = "maker"
        elif t.get("is_maker") is False:
            fee_role = "taker"

    if trades:
        net_qty = exec_qty - fee_qty
    else:
        fee_qty = exec_qty * 0.0025
        net_qty = exec_qty * 0.9975
        fee_role = "taker_fallback"

    if cummul_quote > 0:
        actual_cost_myr = cummul_quote
    else:
        price = float(order_data.get("price", 0))
        actual_cost_myr = price * exec_qty if price > 0 else 0.0

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
# OLD SYSTEM: Place consolidated sell order
# Cancel old sell → combine all HOLDING layers → 1 sell
# ─────────────────────────────────────────────
def _place_consolidated_sell_old_system(coin_id: str):
    """[OLD SYSTEM] Cancel existing sell, combine all HOLDING layers, place 1 consolidated sell order."""
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
    total_cost = 0.0
    total_net_qty = 0.0
    total_fee_qty = 0.0
    total_fee_myr = 0.0

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
    avg_entry = total_cost / total_net_qty

    # 4. Calculate sell price: avg_entry × (1 + tp_pct)
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

    for l in holding_layers:
        l["consolidated_sell_price"] = sell_price
        l["consolidated_sell_qty"] = sell_qty

    shared.engine_state[coin_id]["total_buy_fees_myr"] = total_fee_myr
    shared.engine_state[coin_id]["total_buy_fees_qty"] = total_fee_qty

    shared.save_state()
    logger.info(f"[{coin_id}] CONSOLIDATED SELL SUCCESS: Order {sell_order_id} at RM{sell_price:.4f}")


# ─────────────────────────────────────────────
# OLD SYSTEM: Place next DCA BUY layer at 1% below entry
# (Called after a consolidated SELL fills)
# ─────────────────────────────────────────────
def _place_next_dca_buy_old_system(coin_id: str, last_entry_price: float):
    """[OLD SYSTEM] After a consolidated SELL fills, place Limit BUY at 1% below last entry.
    Uses min(limit_price, current_price) to ensure full RM deployment."""
    import hata_api
    import time

    layers = shared.engine_state[coin_id].get("layers", [])
    risk_level = shared.engine_state[coin_id].get("risk_level", 1)

    def _get_strategy_local(coin_id: str, risk_level: int) -> dict:
        tp_pct = shared.engine_state[coin_id].get("tp_pct", 0.005)
        if risk_level == 3:
            return {"max_layers": 3, "tp_pct": tp_pct}
        elif risk_level == 2:
            return {"max_layers": 5, "tp_pct": tp_pct}
        else:
            return {"max_layers": 6, "tp_pct": tp_pct}

    strategy = _get_strategy_local(coin_id, risk_level)

    if len(layers) >= strategy["max_layers"]:
        logger.info(f"[{coin_id}] Max layers ({strategy['max_layers']}) reached. Skipping auto-DCA.")
        return

    # 1% below last entry price
    next_entry = round(last_entry_price * 0.99, 6)

    current_price = shared.engine_state[coin_id].get("current_price", 0)
    if current_price > 0 and current_price < next_entry:
        buy_price = current_price
        logger.info(f"[{coin_id}] AUTO-DCA: Market RM{current_price:.4f} already < limit RM{next_entry:.4f} → using market price")
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
