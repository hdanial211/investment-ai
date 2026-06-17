import torch
import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
import gymnasium as gym

class LSTMExtractor(BaseFeaturesExtractor):
    """
    Custom Feature Extractor using LSTM.
    Takes 2D observations of shape (window_size, num_features)
    and extracts a fixed size feature vector for the PPO MLPs.
    """
    def __init__(self, observation_space: gym.spaces.Box, features_dim: int = 128, hidden_size: int = 128, num_layers: int = 2):
        super(LSTMExtractor, self).__init__(observation_space, features_dim)
        
        # Observation space shape is (window_size, num_features)
        self.window_size = observation_space.shape[0]
        self.num_features = observation_space.shape[1]
        
        self.lstm = nn.LSTM(
            input_size=self.num_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0
        )
        
        self.linear = nn.Linear(hidden_size, features_dim)
        self.relu = nn.ReLU()

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        # stable-baselines3 may flatten the Box if we are not careful, 
        # but if we pass it correctly it should be (batch_size, window_size, num_features)
        # If it comes flattened, we must reshape it
        if len(observations.shape) == 2:
            batch_size = observations.shape[0]
            observations = observations.view(batch_size, self.window_size, self.num_features)
            
        lstm_out, _ = self.lstm(observations)
        
        # Extract output of the last time step
        last_out = lstm_out[:, -1, :] # shape: (batch_size, hidden_size)
        
        # Pass to linear layer
        features = self.linear(last_out)
        return self.relu(features)
