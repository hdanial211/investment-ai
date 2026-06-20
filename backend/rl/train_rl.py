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

import log_config
logger = logging.getLogger(__name__)

def main():
    data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ETH_USDT_1m.csv')
    model_save_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'ppo_scalping_ETH.zip')
    
    logger.info(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Use only last 2 months for training to keep it fast but sufficient
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
    
    logger.info("Initializing PPO Model (Reinforcement Learning)...")
    # PPO is great for this. We use MlpPolicy to let it learn from tabular feature data.
    model = PPO(
        "MlpPolicy", 
        vec_env, 
        verbose=1,
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        ent_coef=0.01, # Encourage exploration
        tensorboard_log="./ppo_crypto_tensorboard/"
    )
    
    logger.info("Starting Trial-and-Error Training (This may take a while)...")
    # Train for 500,000 timesteps (it will loop over the data multiple times)
    model.learn(total_timesteps=500000)
    
    logger.info(f"Training complete! Saving model to {model_save_path}")
    model.save(model_save_path)

if __name__ == "__main__":
    main()
