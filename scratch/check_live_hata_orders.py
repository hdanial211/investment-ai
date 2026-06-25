import os
import sys
import json

# Add backend directory to path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(base_dir, "backend")
sys.path.append(backend_dir)

import shared
import hata_api

def check_live_orders():
    # Load bot state
    state_file = os.path.join(backend_dir, "bot_state.json")
    if not os.path.exists(state_file):
        print("bot_state.json not found!")
        return

    with open(state_file, "r") as f:
        state = json.load(f)

    print("=" * 60)
    print("CHECKING LIVE ORDERS FROM HATA EXCHANGE")
    print("=" * 60)

    for coin, info in state.items():
        layers = info.get("layers", [])
        if not layers:
            print(f"{coin}: No active layers.")
            continue
        
        for l in layers:
            layer_id = l.get("id")
            status = l.get("status")
            buy_order_id = l.get("buy_order_id")
            sell_order_id = l.get("sell_order_id")
            
            print(f"\n[{coin}] Layer {layer_id} - State Status: {status}")
            
            if buy_order_id:
                print(f"  Buy Order ID: {buy_order_id}")
                buy_res = hata_api.get_order_status(buy_order_id)
                buy_data = buy_res.get("data")
                if buy_data:
                    print(f"    Hata Status: {buy_data.get('status')} | orig_qty: {buy_data.get('orig_qty')} | exec_qty: {buy_data.get('exec_qty')}")
                else:
                    print(f"    Hata Error: {buy_res}")
                    
            if sell_order_id:
                print(f"  Sell Order ID: {sell_order_id}")
                sell_res = hata_api.get_order_status(sell_order_id)
                sell_data = sell_res.get("data")
                if sell_data:
                    print(f"    Hata Status: {sell_data.get('status')} | orig_qty: {sell_data.get('orig_qty')} | exec_qty: {sell_data.get('exec_qty')}")
                else:
                    print(f"    Hata Error: {sell_res}")

    print("=" * 60)

if __name__ == "__main__":
    check_live_orders()
