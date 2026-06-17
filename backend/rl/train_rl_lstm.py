import os
import sys
import pandas as pd
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import logging

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from features.indicators import calculate_features
from rl.env import CryptoTradingEnv
from rl.lstm_policy import LSTMExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_COINS = ["BTC", "ETH", "SOL", "XRP", "LTC"]

def train_coin(coin_name):
    data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', f'{coin_name}_USDT_1m.csv')
    model_save_path = os.path.join(os.path.dirname(__file__), '..', 'models', f'ppo_lstm_{coin_name}.zip')
    
    if not os.path.exists(data_path):
        logger.error(f"Data for {coin_name} not found at {data_path}. Skipping.")
        return
        
    logger.info(f"--- Training RL+LSTM for {coin_name} ---")
    df = pd.read_csv(data_path)
    
    # Use only last 2 months for training to keep it fast but sufficient (approx 86400 mins)
    df = df.tail(86400).reset_index(drop=True)
    
    logger.info("Calculating technical indicators...")
    df_features = calculate_features(df)
    
    # Drop rows with NaN (from indicators)
    df_features.dropna(inplace=True)
    df_features.reset_index(drop=True, inplace=True)
    
    # Dynamically select features exactly like ai_model.py
    bb_cols = [c for c in df_features.columns if c.startswith('BB')]
    macd_cols = [c for c in df_features.columns if c.startswith('MACD')]
    stoch_cols = [c for c in df_features.columns if c.startswith('STOCH')]
    atr_cols = [c for c in df_features.columns if c.startswith('ATR')]
    
    feature_cols = [
        'open', 'high', 'low', 'close', 'volume', 
        'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 
        'Volume_ROC'
    ] + bb_cols + macd_cols + stoch_cols + atr_cols
    
    # Ensure VWAP is present
    vwap_col = 'VWAP_D' if 'VWAP_D' in df_features.columns else 'VWAP'
    if vwap_col in df_features.columns:
        feature_cols.append(vwap_col)
        
    logger.info(f"Using {len(feature_cols)} features for RL environment.")
    
    # Create Environment
    env = CryptoTradingEnv(df_features, feature_cols)
    # Wrap it for stable-baselines
    vec_env = DummyVecEnv([lambda: env])
    
    logger.info("Initializing PPO Model with Custom PyTorch LSTM Extractor...")
    
    policy_kwargs = dict(
        features_extractor_class=LSTMExtractor,
        features_extractor_kwargs=dict(features_dim=128, hidden_size=64, num_layers=2),
    )
    
    model = PPO(
        "MlpPolicy", # We use MlpPolicy but replace the feature extractor with LSTM
        vec_env, 
        verbose=1,
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        ent_coef=0.01, # Encourage exploration
        policy_kwargs=policy_kwargs,
        tensorboard_log=f"./ppo_lstm_tensorboard_{coin_name}/"
    )
    
    logger.info("Starting Trial-and-Error Training (This may take a while)...")
    # Train for 500,000 timesteps
    model.learn(total_timesteps=500000)
    
    logger.info(f"Training complete! Saving model to {model_save_path}")
    model.save(model_save_path)

def main():
    for coin in SUPPORTED_COINS:
        train_coin(coin)
        
    logger.info("All coins trained successfully!")

if __name__ == "__main__":
    main()
