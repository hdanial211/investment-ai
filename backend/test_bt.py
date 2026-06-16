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

print("Starting backtest...")
run_dca_backtest(
    csv_path=data_path,
    model_path=model_path,
    progress_callback=my_progress
)
print("Done")
