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

    # 6. Price Returns (Target untuk ML)
    # Berapa peratus harga berubah pada candle seterusnya?
    df['next_close'] = df['close'].shift(-1)
    df['target_return'] = (df['next_close'] - df['close']) / df['close'] * 100
    
    # Label: 1 (BUY) if return > 0.05%, -1 (SELL) if return < -0.05%, 0 (HOLD)
    def classify_signal(ret):
        if pd.isna(ret):
            return 0
        if ret > 0.05:
            return 1
        elif ret < -0.05:
            return -1
        return 0
        
    df['target'] = df['target_return'].apply(classify_signal)

    # Buang baris yang ada NaN disebabkan oleh calculation indicator
    df = df.dropna()

    return df
