"""
Kira P&L TERUS dari Luno API (bukan dari DB bot)
fee_base = dalam crypto → convert ke MYR guna harga trade
"""
import sys; sys.path.insert(0, '.')
import requests
from dotenv import dotenv_values
import os

cfg = dotenv_values(os.path.join('..', '.env'))
auth = (cfg.get('LUNO_API_KEY','').strip(), cfg.get('LUNO_API_SECRET','').strip())
BASE = "https://api.luno.com/api/1"

pairs = ["XBTMYR", "ETHMYR", "XRPMYR", "SOLMYR"]

# Get live prices
def get_price(pair):
    r = requests.get(f"{BASE}/ticker", params={"pair": pair})
    return float(r.json().get("last_trade", 0)) if r.ok else 0

grand_cost = grand_sell = grand_fees = grand_pnl = 0.0

print(f"\n{'PAIR':<10} {'Beli':>12} {'Jual':>12} {'Fee MYR':>10} {'Tgn (nilai)':>13} {'P&L':>10}")
print("=" * 70)

for pair in pairs:
    r = requests.get(f"{BASE}/listorders", auth=auth, params={"pair": pair, "state": "COMPLETE"})
    if not r.ok:
        continue
    orders = r.json().get("orders", [])

    live_price = get_price(pair)
    total_cost = total_sell = total_fees = 0.0
    vol_bought = vol_sold = 0.0

    for o in orders:
        otype   = o.get("type", "")
        base    = float(o.get("base", 0) or 0)
        counter = float(o.get("counter", 0) or 0)
        fee_b   = float(o.get("fee_base", 0) or 0)
        price   = float(o.get("limit_price") or 0)
        if price == 0 and base > 0:
            price = counter / base

        fee_myr = fee_b * price  # convert crypto fee to MYR

        if otype in ("BID", "BUY") and base > 0:
            total_cost += counter
            total_fees += fee_myr
            vol_bought += base
        elif otype in ("ASK", "SELL") and base > 0:
            total_sell += counter
            total_fees += fee_myr
            vol_sold   += base

    remaining = max(0.0, vol_bought - vol_sold)
    curr_val  = remaining * live_price
    pnl       = total_sell + curr_val - total_cost - total_fees

    grand_cost += total_cost
    grand_sell += total_sell
    grand_fees += total_fees
    grand_pnl  += pnl

    sign = "+" if pnl >= 0 else ""
    print(f"{pair:<10} {'RM'+f'{total_cost:.2f}':>12} {'RM'+f'{total_sell:.2f}':>12} {'RM'+f'{total_fees:.4f}':>10} {'RM'+f'{curr_val:.2f}':>13} {sign+'RM'+f'{pnl:.2f}':>10}")

print("=" * 70)
pct = (grand_pnl / grand_cost * 100) if grand_cost > 0 else 0
print(f"{'TOTAL':<10} {'RM'+f'{grand_cost:.2f}':>12} {'RM'+f'{grand_sell:.2f}':>12} {'RM'+f'{grand_fees:.4f}':>10} {'':>13} {'+RM' if grand_pnl>=0 else 'RM'}{grand_pnl:.2f} ({pct:.2f}%)")
print(f"\nNote: P&L dikira dari Luno API secara langsung")
