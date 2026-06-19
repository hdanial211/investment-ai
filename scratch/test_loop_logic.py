import sys
import os
import asyncio
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
import shared
import hata_api

hata_prices = {
    "ETH": 0.0,
    "BTC": 0.0,
    "SOL": 0.0,
    "LTC": 0.0,
    "XRP": 0.0
}

async def run_test():
    print("--- 1. Fetch Hata Prices ---")
    try:
        res = requests.get("https://my-api.hata.io/orderbook/api/v2/exchange-info", timeout=5)
        res.raise_for_status()
        data = res.json().get("data", [])
        for item in data:
            base = item.get("base")
            quote = item.get("quote")
            if quote == "MYR" and base in hata_prices:
                hata_prices[base] = float(item.get("price", 0.0))
        print("Hata Prices:", hata_prices)
    except Exception as e:
        print("Error fetching Hata prices:", e)

    print("\n--- 2. Fetch Hata Balance & Rate ---")
    try:
        bal_res = hata_api.get_myr_balance()
        print("Balance Result:", bal_res)
        if bal_res:
            avail, froz = bal_res
            shared.global_state["balance_myr"] = avail
            shared.global_state["frozen_myr"] = froz
            print(f"Updated global state balance: {avail}, frozen: {froz}")
    except Exception as e:
        print("Error fetching balance:", e)

    print("\n--- 3. Check Pending Orders Status ---")
    try:
        state_changed = False
        for coin_id in shared.engine_state:
            layers = shared.engine_state[coin_id].get("layers", [])
            active_layers = []
            coin_changed = False
            for l in layers:
                status = l.get("status", "OPEN")
                print(f"Checking {coin_id} layer #{l['id']} with status {status}...")
                
                if status == "PENDING_BUY":
                    print("Status is PENDING_BUY")
                    active_layers.append(l)
                elif status == "PENDING_SELL":
                    sell_id = l.get("sell_order_id")
                    print(f"Status is PENDING_SELL for sell_order_id {sell_id}")
                    if sell_id:
                        res = hata_api.get_order_status(sell_id)
                        print("Order status response:", res)
                        order_data = res.get("data")
                        if order_data:
                            order_status = order_data.get("status")
                            print(f"Order status on Hata: {order_status}")
                            if order_status == "fulfilled":
                                profit_myr = l["amount_myr"] * (l["take_profit"] / l["entry_price"])
                                actual_pnl = profit_myr - l["amount_myr"]
                                shared.engine_state[coin_id]["total_pnl"] += actual_pnl
                                print(f"Fulfilled! Profit: {actual_pnl}")
                                coin_changed = True
                            elif order_status in ["cancelled", "rejected"]:
                                print(f"Cancelled/Rejected! Reverting status to OPEN.")
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
                    print("Status is OPEN. Will attempt to place Limit SELL.")
                    exec_qty = l.get("quantity")
                    adj_qty = exec_qty * 0.996
                    avail_bal, froz_bal = hata_api.get_token_balance(coin_id)
                    print(f"Available balance: {avail_bal}, Adjusted qty needed: {adj_qty}")
                    if avail_bal < adj_qty:
                        print("Insufficient token balance. Keeping status as OPEN.")
                        active_layers.append(l)
                    else:
                        print("Sufficient balance. Placing Limit SELL...")
                        sell_res = hata_api.place_limit_order(f"{coin_id}_MYR", "SELL", l["take_profit"], adj_qty)
                        print("Place order response:", sell_res)
                        if sell_res.get("status") == "success":
                            sell_id = sell_res.get("data", {}).get("id")
                            l["status"] = "PENDING_SELL"
                            l["sell_order_id"] = str(sell_id)
                            l["hata_sell_res"] = sell_res
                        else:
                            print("Failed to place limit sell.")
                        coin_changed = True
                        active_layers.append(l)
                else:
                    active_layers.append(l)
            
            if coin_changed:
                print(f"Updating layers for {coin_id} to: {active_layers}")
                shared.engine_state[coin_id]["layers"] = active_layers
                state_changed = True
        
        if state_changed:
            print("Saving state to file...")
            shared.save_state()
            
    except Exception as e:
        print("Error in check_orders:", e)

asyncio.run(run_test())
