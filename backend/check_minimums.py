"""Check Luno minimum volumes"""
import sys; sys.path.insert(0, '.')
import requests
import os
from dotenv import dotenv_values

cfg = dotenv_values(os.path.join('..', '.env'))
auth = (cfg.get('LUNO_API_KEY','').strip(), cfg.get('LUNO_API_SECRET','').strip())

pairs = ["XBTMYR", "ETHMYR", "XRPMYR", "SOLMYR"]
MIN_VOL = {
    "XBTMYR": 0.0001,
    "ETHMYR": 0.001,
    "XRPMYR": 10.0,
    "SOLMYR": 0.01,
}

print(f"\n{'Pair':<10} {'Min Volume':>12} {'Live Price':>16} {'Min MYR':>12} {'RM35 OK?':>10}")
print("-" * 65)
for pair, min_vol in MIN_VOL.items():
    t = requests.get(f"https://api.luno.com/api/1/ticker?pair={pair}")
    price = float(t.json().get('last_trade', 0)) if t.ok else 0
    min_myr = min_vol * price
    ok = "YES" if 35 >= min_myr else "NO - too small"
    unit = "BTC" if pair == "XBTMYR" else pair[:3]
    print(f"{pair:<10} {str(min_vol)+' '+unit:>12} {'RM '+f'{price:,.4f}':>16} {'RM '+f'{min_myr:.4f}':>12} {ok:>10}")
