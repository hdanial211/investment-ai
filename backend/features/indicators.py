import pandas as pd
import pandas_ta as ta

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Kira indikator teknikal (features) untuk model AI menggunakan pandas_ta.
    Memerlukan DataFrame dengan lajur: open, high, low, close, volume.
    """
    df = df.copy()
    
    # Pastikan data diisih mengikut masa
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp')

    # 1. Moving Averages (EMA)
    df.ta.ema(length=9, append=True)
    df.ta.ema(length=21, append=True)
    
    # Trend signal (EMA9 > EMA21 = 1, else 0)
    df['EMA_Trend'] = (df['EMA_9'] > df['EMA_21']).astype(int)

    # 2. RSI
    df.ta.rsi(length=14, append=True)

    # 3. Bollinger Bands
    df.ta.bbands(length=20, append=True)

    # 4. VWAP (Volume Weighted Average Price)
    try:
        if 'timestamp' in df.columns:
            # Pastikan format datetime untuk index VWAP
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            temp_df = df.set_index('timestamp')
            temp_df.ta.vwap(append=True)
            df['VWAP_D'] = temp_df['VWAP_D'].values
        else:
            df.ta.vwap(append=True)
    except Exception as e:
        # Fallback manual calculation if VWAP fails
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['VWAP'] = (df['typical_price'] * df['volume']).cumsum() / df['volume'].cumsum()
        df.drop(columns=['typical_price'], inplace=True)

    # 5. Volume Delta (Rate of Change)
    df['Volume_ROC'] = df['volume'].pct_change() * 100

    # 6. MACD, ATR, Stochastic RSI
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.atr(length=14, append=True)
    df.ta.stochrsi(length=14, append=True)

    # NOTE: Target label (Triple Barrier) dikira BERASINGAN dalam:
    #   - ml_retrain.py (untuk retrain)
    #   - ai_model.py (untuk initial training)
    # Function ini HANYA return features, TANPA target column.

    # Buang baris yang ada NaN disebabkan oleh calculation indicator
    df = df.dropna()

    return df
