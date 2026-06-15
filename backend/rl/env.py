import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class CryptoTradingEnv(gym.Env):
    """
    A custom Bitcoin/Crypto trading environment for OpenAI Gymnasium.
    """
    metadata = {'render_modes': ['human']}

    def __init__(self, df, feature_cols, initial_balance=1000.0, fee=0.001):
        super(CryptoTradingEnv, self).__init__()
        
        self.df = df.reset_index(drop=True)
        self.feature_cols = feature_cols
        self.initial_balance = initial_balance
        self.fee = fee
        
        # Actions: 0 = Hold, 1 = Buy, 2 = Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation space: all features + current position (0 or 1) + unrealized profit
        # We need to find min/max to define the space correctly, but using -inf/inf is easier for tabular data
        self.obs_shape = len(self.feature_cols) + 2
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.obs_shape,), dtype=np.float32
        )
        
        self.current_step = 0
        self.position = 0 # 0 = Flat, 1 = Long
        self.entry_price = 0.0
        self.balance = self.initial_balance
        self.crypto_held = 0.0
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Start at a random point in the first 20% of data to ensure variety, 
        # or just start at 0 if we want deterministic
        self.current_step = 0
        self.position = 0
        self.entry_price = 0.0
        self.balance = self.initial_balance
        self.crypto_held = 0.0
        
        return self._get_obs(), {}

    def _get_obs(self):
        # Current features
        row = self.df.iloc[self.current_step]
        features = row[self.feature_cols].values.astype(np.float32)
        
        # Unrealized profit calculation
        current_price = row['close']
        unrealized_profit = 0.0
        if self.position == 1:
            unrealized_profit = (current_price - self.entry_price) / self.entry_price
            
        # Append state info
        obs = np.append(features, [self.position, unrealized_profit])
        return np.nan_to_num(obs, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    def step(self, action):
        row = self.df.iloc[self.current_step]
        current_price = row['close']
        
        reward = 0.0
        done = False
        
        # Calculate dense reward (change in portfolio value)
        # Before taking action, what was our portfolio value?
        prev_portfolio_value = self.balance + (self.crypto_held * current_price)
        
        # Execute Action
        if action == 1 and self.position == 0: # BUY
            # Calculate how much crypto we can buy
            trade_amount = self.balance * 0.99 # Keep 1% as buffer
            fee_paid = trade_amount * self.fee
            self.crypto_held = (trade_amount - fee_paid) / current_price
            self.balance -= trade_amount
            self.position = 1
            self.entry_price = current_price
            
        elif action == 2 and self.position == 1: # SELL
            # Sell all crypto
            gross_revenue = self.crypto_held * current_price
            fee_paid = gross_revenue * self.fee
            self.balance += (gross_revenue - fee_paid)
            self.crypto_held = 0.0
            self.position = 0
            
        elif action == 0: # HOLD
            pass
            
        # Move to next step
        self.current_step += 1
        if self.current_step >= len(self.df) - 1:
            done = True
            
        # New portfolio value
        next_row = self.df.iloc[self.current_step] if not done else row
        next_price = next_row['close']
        new_portfolio_value = self.balance + (self.crypto_held * next_price)
        
        # Reward is the percentage change in portfolio value
        # This gives the AI immediate feedback on every step!
        reward = (new_portfolio_value - prev_portfolio_value) / prev_portfolio_value
        
        # Multiplier to make rewards bigger for neural network learning
        reward *= 100.0 
        
        # If the bot goes bankrupt
        if new_portfolio_value < self.initial_balance * 0.1:
            done = True
            reward = -100.0

        obs = self._get_obs()
        info = {
            'portfolio_value': new_portfolio_value,
            'position': self.position
        }
        
        return obs, reward, done, False, info
