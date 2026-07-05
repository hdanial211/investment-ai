import os
import sys
import logging
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rl.env import CryptoTradingEnv
from rl.lstm_policy import LSTMExtractor
from rl.utils import load_and_prepare_data, PROJECT_ROOT, MODELS_DIR

import log_config
logger = logging.getLogger(__name__)

SUPPORTED_COINS = ["BTC", "ETH", "SOL", "XRP", "LTC"]

def train_coin(coin_name):
    model_save_path = os.path.join(MODELS_DIR, f'ppo_lstm_{coin_name}.zip')
    tensorboard_dir = os.path.join(PROJECT_ROOT, f'ppo_lstm_tensorboard_{coin_name}')

    try:
        df_features, feature_cols = load_and_prepare_data(coin_name)
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    logger.info(f"--- Training RL+LSTM for {coin_name} ---")

    # Create Environment
    env = CryptoTradingEnv(df_features, feature_cols)
    # Wrap it for stable-baselines
    vec_env = DummyVecEnv([lambda: env])
    
    logger.info("Initializing PPO Model with Custom PyTorch LSTM Extractor...")
    
    policy_kwargs = dict(
        features_extractor_class=LSTMExtractor,
        features_extractor_kwargs=dict(features_dim=128, hidden_size=128, num_layers=2),
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
        tensorboard_log=tensorboard_dir
    )
    
    logger.info("Starting Trial-and-Error Training (This may take a while)...")
    # Train for 500,000 timesteps (it will loop over the data multiple times)
    model.learn(total_timesteps=500000)
    
    logger.info(f"Training complete! Saving model to {model_save_path}")
    model.save(model_save_path)

def main():
    for coin in SUPPORTED_COINS:
        train_coin(coin)
        
    logger.info("All coins trained successfully!")

if __name__ == "__main__":
    main()
