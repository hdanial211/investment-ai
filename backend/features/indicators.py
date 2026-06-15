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

    # 7. Price Returns (Target untuk ML)
    # Kita melihat 10 lilin (minit) ke hadapan
    lookahead = 10
    
    # Cari paras tertinggi dan terendah dalam 10 minit ke hadapan
    df['future_max'] = df['high'].rolling(window=lookahead, min_periods=1).max().shift(-lookahead)
    df['future_min'] = df['low'].rolling(window=lookahead, min_periods=1).min().shift(-lookahead)
    
    df['max_return'] = (df['future_max'] - df['close']) / df['close'] * 100
    df['min_return'] = (df['close'] - df['future_min']) / df['close'] * 100
    
    # Label: 
    # Yuran pertukaran (Fee) Hata = 0.1% * 2 (buy & sell) = 0.2%.
    # Kita nak untung sekurang-kurangnya 0.6% dan mengelak drawdown lebih 0.4% dalam 10 minit tersebut
    def classify_signal(row):
        if pd.isna(row['max_return']) or pd.isna(row['min_return']):
            return 0
            
        if row['max_return'] >= 0.4 and row['min_return'] <= 0.25:
            return 1 # Strong BUY
        elif row['min_return'] >= 0.4 and row['max_return'] <= 0.25:
            return -1 # Strong SELL
        return 0
        
    df['target'] = df.apply(classify_signal, axis=1)
    df.drop(columns=['future_max', 'future_min', 'max_return', 'min_return'], inplace=True)

    # Buang baris yang ada NaN disebabkan oleh calculation indicator
    df = df.dropna()

    return df
