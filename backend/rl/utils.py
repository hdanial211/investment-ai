"""
Shared utilities for RL training scripts.
Extracts common logic to avoid copy-paste across train files.
"""
import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Dynamically select feature columns from a DataFrame that has
    already had calculate_features() applied. Mirrors the same logic
    used by ai_model.py and the backtest engines.
    """
    bb_cols = [c for c in df.columns if c.startswith('BB')]
    macd_cols = [c for c in df.columns if c.startswith('MACD')]
    stoch_cols = [c for c in df.columns if c.startswith('STOCH')]
    atr_cols = [c for c in df.columns if c.startswith('ATR')]

    feature_cols = [
        'open', 'high', 'low', 'close', 'volume',
        'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14',
        'Volume_ROC'
    ] + bb_cols + macd_cols + stoch_cols + atr_cols

    # Ensure VWAP is present
    vwap_col = 'VWAP_D' if 'VWAP_D' in df.columns else 'VWAP'
    if vwap_col in df.columns:
        feature_cols.append(vwap_col)

    return feature_cols


def load_and_prepare_data(coin_name: str, tail_rows: int = 86400) -> tuple[pd.DataFrame, list[str]]:
    """
    Load CSV data for a coin, calculate features, and return
    the prepared DataFrame with its feature columns.

    Args:
        coin_name: e.g. "BTC", "ETH"
        tail_rows: Number of most recent rows to use (default ~60 days of 1min data)

    Returns:
        (df_features, feature_cols) tuple
    """
    # Import here to avoid circular imports
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from features.indicators import calculate_features

    data_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'data', f'{coin_name}_USDT_1m.csv'
    )

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data for {coin_name} not found at {data_path}")

    logger.info(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)

    # Use only last N rows for training
    df = df.tail(tail_rows).reset_index(drop=True)

    logger.info("Calculating technical indicators...")
    df_features = calculate_features(df)

    # Drop rows with NaN (from indicators)
    df_features.dropna(inplace=True)
    df_features.reset_index(drop=True, inplace=True)

    feature_cols = get_feature_columns(df_features)
    logger.info(f"Using {len(feature_cols)} features for RL environment.")

    return df_features, feature_cols


# Project root for absolute paths (tensorboard logs, models, etc.)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MODELS_DIR = os.path.join(PROJECT_ROOT, 'backend', 'models')
