import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.binance_proxy import download_historical_data
from models.ai_model import AIScalpingModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TRAIN_ALL")

COINS = ['BTC/USDT', 'SOL/USDT', 'LTC/USDT', 'XRP/USDT']
DAYS_BACK = 180  # 6 months is a good balance between speed and accuracy

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    models_dir = os.path.join(base_dir, 'models')
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    for symbol in COINS:
        logger.info(f"--- Processing {symbol} ---")
        
        # 1. Download Data
        # symbol format is BTC/USDT, file name becomes BTC_USDT_1m.csv
        file_name = f"{symbol.replace('/', '_')}_1m.csv"
        csv_path = os.path.join(data_dir, file_name)
        
        if not os.path.exists(csv_path):
            logger.info(f"Dataset for {symbol} not found. Downloading {DAYS_BACK} days...")
            # Note: The download_historical_data function from binance_proxy saves into 'data' relative to cwd
            # Let's override it or just chdir
            os.chdir(base_dir)
            df = download_historical_data(symbol, timeframe='1m', limit=1000, days_back=DAYS_BACK)
        else:
            logger.info(f"Dataset {file_name} already exists. Skipping download.")
            
        # 2. Train AI
        asset_name = symbol.split('/')[0]
        model_name = f"xgboost_scalping_{asset_name}_1y.pkl" # keep naming consistent
        model_path = os.path.join(models_dir, model_name)
        
        if not os.path.exists(model_path):
            logger.info(f"Training AI Model for {symbol}...")
            ai = AIScalpingModel(model_path=model_path)
            ai.train(csv_path)
            logger.info(f"✅ AI Model for {symbol} successfully trained and saved!")
        else:
            logger.info(f"AI Model {model_name} already exists. Skipping.")

if __name__ == "__main__":
    main()
