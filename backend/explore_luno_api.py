"""
Explore Luno API endpoints for profit/trade data
"""
import sys; sys.path.insert(0, '.')
import requests
from dotenv import dotenv_values
import os, json

cfg = dotenv_values(os.path.join('..', '.env'))
auth = (cfg.get('LUNO_API_KEY','').strip(), cfg.get('LUNO_API_SECRET','').strip())
BASE = "https://api.luno.com/api/1"

pairs = ["XBTMYR", "ETHMYR", "XRPMYR"]

print("=" * 60)
print("EXPLORING LUNO TRADE API")
print("=" * 60)

for pair in pairs:
    print(f"\n--- {pair} listorders ---")
    r = requests.get(f"{BASE}/listorders", auth=auth, params={"pair": pair, "state": "COMPLETE"})
    if r.ok:
        orders = r.json().get("orders", [])
        for o in orders[:5]:
            oid    = o.get("order_id")
            side   = o.get("type")
            base   = float(o.get("base", 0))       # crypto amount
            counter= float(o.get("counter", 0))    # MYR amount
            fee_b  = float(o.get("fee_base", 0) or 0)
            fee_c  = float(o.get("fee_counter", 0) or 0)
            ts     = o.get("creation_timestamp", "")
            price  = counter / base if base > 0 else 0
            print(f"  {side} | {base:.6f} crypto | RM{counter:.4f} | price=RM{price:.4f} | fee_base={fee_b} fee_counter={fee_c}")
    else:
        print(f"  Error: {r.status_code}")

# Also try listtrades endpoint
print("\n--- listtrades (XBTMYR) ---")
r2 = requests.get(f"{BASE}/listtrades", auth=auth, params={"pair": "XBTMYR"})
if r2.ok:
    print(json.dumps(r2.json(), indent=2)[:1000])
else:
    print(f"Error {r2.status_code}: {r2.text[:200]}")

# Try transactions for MYR account
print("\n--- transactions (MYR) ---")
r3 = requests.get(f"https://api.luno.com/api/1/accounts", auth=auth)
if r3.ok:
    accounts = r3.json().get("accounts", [])
    for acc in accounts:
        print(f"  Account: {acc.get('id')} | {acc.get('currency')} | Balance: {acc.get('balance')}")
else:
    print(f"Error {r3.status_code}: {r3.text[:200]}")
