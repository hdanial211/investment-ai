"""Test multi-pair imports and live prices"""
import sys; sys.path.insert(0, '.')

from database.models import GridState, Trade
from exchange.luno_client import luno_client
from strategy.decision_maker import DecisionMaker
from scheduler.daily_job import run_rebalance_job, _execute_grid_trade
print("All imports OK")

prices = luno_client.get_all_prices(["XBTMYR", "ETHMYR", "XRPMYR", "SOLMYR"])
for pair, p in prices.items():
    if p:
        print(f"{pair}: RM {p['last_trade']:,.4f}")
    else:
        print(f"{pair}: ERROR")
