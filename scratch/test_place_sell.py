import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
import hata_api

print("--- Test 1: Placing 10.5 XRP at RM 4.75 (Value = RM 49.875) ---")
res1 = hata_api.place_limit_order("XRP_MYR", "SELL", 4.75, 10.5)
print("Res 1:", res1)
if res1.get("status") == "success":
    order_id = res1["data"]["id"]
    time.sleep(2)
    status_res = hata_api.get_order_status(order_id)
    print("Status 1 after 2s:", status_res)
    if status_res.get("data", {}).get("status") == "active":
        hata_api.cancel_order("XRP_MYR", order_id)

print("\n--- Test 2: Placing 10.8 XRP at RM 4.75 (Value = RM 51.30) ---")
res2 = hata_api.place_limit_order("XRP_MYR", "SELL", 4.75, 10.8)
print("Res 2:", res2)
if res2.get("status") == "success":
    order_id = res2["data"]["id"]
    time.sleep(2)
    status_res = hata_api.get_order_status(order_id)
    print("Status 2 after 2s:", status_res)
    if status_res.get("data", {}).get("status") == "active":
        hata_api.cancel_order("XRP_MYR", order_id)
