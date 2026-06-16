import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class CryptoTradingEnv(gym.Env):
    """
    A custom Bitcoin/Crypto trading environment for OpenAI Gymnasium.
    Optimized for Expectancy: AI only decides WHEN to Enter. Exits are strictly managed by TP/SL.
    """
    metadata = {'render_modes': ['human']}

    def __init__(self, df, feature_cols, initial_balance=1000.0, fee=0.001):
        super(CryptoTradingEnv, self).__init__()
        
        self.df = df.reset_index(drop=True)
        self.feature_cols = feature_cols
        self.initial_balance = initial_balance
        self.fee = fee # 0.1% per side
        
        # Actions: 0 = Wait, 1 = Buy (Enter Long)
        # AI no longer controls the SELL. Sell is governed by strict TP/SL math.
        self.action_space = spaces.Discrete(2)
        
        # Observation space: all features + current position (0 or 1) + unrealized profit + time held
        self.obs_shape = len(self.feature_cols) + 3
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.obs_shape,), dtype=np.float32
        )
        
        # Hyperparameters for Scalping
        self.TAKE_PROFIT = 0.006  # 0.6% target (Net ~0.4% after 0.2% round-trip fees)
        self.STOP_LOSS = -0.004   # 0.4% stop loss
        self.MAX_HOLD_TIME = 120  # Max 120 minutes per trade
        
        self.current_step = 0
        self.position = 0 # 0 = Flat, 1 = Long
        self.entry_price = 0.0
        self.balance = self.initial_balance
        self.crypto_held = 0.0
        self.time_held = 0
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.position = 0
        self.entry_price = 0.0
        self.balance = self.initial_balance
        self.crypto_held = 0.0
        self.time_held = 0
        
        return self._get_obs(), {}

    def _get_obs(self):
        row = self.df.iloc[self.current_step]
        features = row[self.feature_cols].values.astype(np.float32)
        
        current_price = row['close']
        unrealized_profit = 0.0
        if self.position == 1:
            unrealized_profit = (current_price - self.entry_price) / self.entry_price
            
        obs = np.append(features, [self.position, unrealized_profit, self.time_held])
        return np.nan_to_num(obs, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    def step(self, action):
        row = self.df.iloc[self.current_step]
        current_price = row['close']
        
        reward = 0.0
        done = False
        
        # Step logic
        if self.position == 0:
            if action == 1:
                # Enter Trade
                trade_amount = self.balance * 0.99
                fee_paid = trade_amount * self.fee
                self.crypto_held = (trade_amount - fee_paid) / current_price
                self.balance -= trade_amount
                self.position = 1
                self.entry_price = current_price
                self.time_held = 0
                # Small penalty for entering to discourage random spamming
                reward = -0.1
            else:
                # Waiting safely
                reward = 0.0
                
        elif self.position == 1:
            self.time_held += 1
            unrealized_profit = (current_price - self.entry_price) / self.entry_price
            
            # Check TP / SL / Max Time
            close_trade = False
            trade_result = ""
            
            if unrealized_profit >= self.TAKE_PROFIT:
                close_trade = True
                trade_result = "TP"
            elif unrealized_profit <= self.STOP_LOSS:
                close_trade = True
                trade_result = "SL"
            elif self.time_held >= self.MAX_HOLD_TIME:
                close_trade = True
                trade_result = "TIME_LIMIT"
                
            if close_trade:
                gross_revenue = self.crypto_held * current_price
                fee_paid = gross_revenue * self.fee
                net_revenue = gross_revenue - fee_paid
                profit_pct = (net_revenue - (self.balance + self.crypto_held * self.entry_price)) / (self.balance + self.crypto_held * self.entry_price) # Approximate
                
                self.balance += net_revenue
                self.crypto_held = 0.0
                self.position = 0
                self.time_held = 0
                
                # Reward Shaping for Expectancy
                if trade_result == "TP":
                    reward = 10.0 # Huge reward for hitting TP cleanly
                elif trade_result == "SL":
                    reward = -10.0 # Huge penalty for hitting SL
                else:
                    # Time limit hit. Penalize based on how bad it is
                    if unrealized_profit < 0:
                        reward = -5.0
                    else:
                        reward = -1.0 # Didn't hit TP, wasted time
            else:
                # Still holding
                reward = -0.01 # Tiny holding penalty to encourage faster TP hits
                
        self.current_step += 1
        if self.current_step >= len(self.df) - 1:
            done = True
            
        # Total bankruptcy protection
        if self.balance + (self.crypto_held * current_price) < self.initial_balance * 0.1:
            done = True
            reward = -100.0

        obs = self._get_obs()
        info = {
            'portfolio_value': self.balance + (self.crypto_held * current_price),
            'position': self.position
        }
        
        return obs, reward, done, False, info
