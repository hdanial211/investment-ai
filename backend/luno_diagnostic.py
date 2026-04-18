"""
Full Luno API diagnostic - semak semua data yang ada
"""
import sys; sys.path.insert(0, '.')
import requests, json
from dotenv import dotenv_values
import os

cfg = dotenv_values(os.path.join('..', '.env'))
auth = (cfg.get('LUNO_API_KEY','').strip(), cfg.get('LUNO_API_SECRET','').strip())
BASE  = "https://api.luno.com/api/1"
BASE2 = "https://api.luno.com/api/exchange/2"

def call(url, params=None):
    r = requests.get(url, auth=auth, params=params, timeout=10)
    return r.json() if r.ok else {"ERROR": r.status_code, "msg": r.text[:200]}

pairs = ["XBTMYR", "ETHMYR", "XRPMYR", "SOLMYR"]
prices = {}

print("\n" + "="*60)
print("1. LIVE PRICES (Ticker)")
print("="*60)
for pair in pairs:
    d = call(f"{BASE}/ticker", {"pair": pair})
    price = float(d.get("last_trade", 0))
    prices[pair] = price
    print(f"  {pair}: RM {price:,.4f}")

print("\n" + "="*60)
print("2. BALANCES")
print("="*60)
bal = call(f"{BASE}/balance")
total_bal_myr = 0
for b in bal.get("balance", []):
    asset = b["asset"]
    total = float(b.get("balance", 0))
    reserved = float(b.get("reserved", 0))
    avail = total - reserved
    price = prices.get(f"XBT{asset}" if asset != "MYR" else "", 0)
    # Find correct pair for each asset
    pair_map = {"XBT": "XBTMYR", "ETH": "ETHMYR", "XRP": "XRPMYR", "SOL": "SOLMYR"}
    myr_val = avail * prices.get(pair_map.get(asset, ""), 1 if asset == "MYR" else 0)
    total_bal_myr += myr_val
    print(f"  {asset}: {avail:.6f} | ~RM{myr_val:.2f}")
print(f"  TOTAL VALUE: ~RM{total_bal_myr:.2f}")

print("\n" + "="*60)
print("3. COMPLETED ORDERS (listorders)")
print("="*60)
for pair in pairs:
    d = call(f"{BASE}/listorders", {"pair": pair, "state": "COMPLETE"})
    orders = d.get("orders") or []
    orders = [o for o in orders if float(o.get("counter",0) or 0) > 0]
    if orders:
        print(f"\n  {pair} ({len(orders)} orders):")
        total_buy = total_sell = 0
        for o in orders:
            otype = o.get("type","")
            base = float(o.get("base",0) or 0)
            counter = float(o.get("counter",0) or 0)
            fee_b = float(o.get("fee_base",0) or 0)
            price = counter/base if base>0 else 0
            label = "BUY " if otype in ("BID","BUY") else "SELL"
            if otype in ("BID","BUY"): total_buy += counter
            else: total_sell += counter
            print(f"    {label} | {base:.6f} | RM{counter:.4f} | @RM{price:,.2f} | fee={fee_b:.8f}")
        print(f"    >> Total Beli: RM{total_buy:.4f} | Total Jual: RM{total_sell:.4f}")
    else:
        print(f"\n  {pair}: No completed orders")

print("\n" + "="*60)
print("4. MY TRADES (listtrades) - includes all trades")
print("="*60)
for pair in pairs:
    d = call(f"{BASE}/listtrades", {"pair": pair})
    trades = d.get("trades") or []
    if trades:
        print(f"\n  {pair} ({len(trades)} trades):")
        for t in trades[:5]:
            side = "BUY " if t.get("is_buy") else "SELL"
            price = float(t.get("price",0))
            base = float(t.get("base",0))
            counter = float(t.get("counter",0))
            fee_b = float(t.get("fee_base",0) or 0)
            fee_c = float(t.get("fee_counter",0) or 0)
            print(f"    {side} | {base:.6f} | RM{counter:.4f} | @RM{price:,.2f} | fee_base={fee_b:.8f} fee_counter={fee_c:.8f}")
    else:
        print(f"\n  {pair}: No trades")

print("\n" + "="*60)
print("5. ACCOUNTS (for transaction history)")
print("="*60)
accs = call(f"{BASE}/accounts")
if "accounts" in accs:
    for a in accs["accounts"]:
        print(f"  {a.get('id')} | {a.get('currency')} | balance={a.get('balance')} | name={a.get('name','')}")
else:
    print("  ERROR:", accs)
