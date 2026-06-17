import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest.dca_engine import run_dca_backtest

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, 'data', 'ETH_USDT_1m.csv')
model_path = os.path.join(base_dir, 'models', 'xgboost_scalping_ETH_1y.pkl')

def my_progress(msg):
    print(f"PROGRESS: {msg}")

import json
print("Starting backtest...")
metrics = run_dca_backtest(
    csv_path=data_path,
    model_path=model_path,
    initial_cash=10000.0,
    trade_size_fiat=50.0,
    take_profit_pct=0.006, # 0.6% Hard TP
    trailing_activation_pct=0.006,
    progress_callback=None
)
print("Done")
print(json.dumps(metrics, indent=4))
