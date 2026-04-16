"""Fetch recent orders from Luno for ETH and XRP"""
import sys; sys.path.insert(0, '.')
from exchange.luno_client import luno_client

for pair in ["ETHMYR", "XRPMYR"]:
    print(f"\n=== {pair} Recent Orders ===")
    try:
        resp = luno_client._get("/listorders", params={"pair": pair, "state": "COMPLETE"})
        orders = resp.get("orders", [])[:5]
        if not orders:
            print("  No completed orders found")
        for o in orders:
            side = o.get("type", "?")
            price = float(o.get("limit_price", 0) or o.get("stop_price", 0) or 0)
            vol = float(o.get("base", 0))
            counter = float(o.get("counter", 0))
            fee = float(o.get("fee_base", 0) or 0)
            created = o.get("creation_timestamp", "")
            print(f"  {side} | Vol={vol} | Price=RM{price:,.4f} | MYR=RM{counter:.2f} | Fee={fee} | ID={o.get('order_id')}")
    except Exception as e:
        print(f"  Error: {e}")
