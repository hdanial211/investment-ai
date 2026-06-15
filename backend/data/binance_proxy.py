import ccxt
import pandas as pd
import time
import os

def download_historical_data(symbol='BTC/USDT', timeframe='1m', limit=1000, days_back=30):
    """
    Downloads historical data from Binance as a proxy for backtesting.
    """
    exchange = ccxt.binance()
    
    # Calculate starting timestamp
    since = exchange.milliseconds() - (days_back * 24 * 60 * 60 * 1000)
    all_ohlcv = []
    
    print(f"Downloading {days_back} days of {timeframe} data for {symbol} from Binance...")
    
    while since < exchange.milliseconds():
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            if not len(ohlcv):
                break
            
            # The last element's timestamp
            since = ohlcv[-1][0] + 1
            all_ohlcv.extend(ohlcv)
            
            print(f"Fetched {len(ohlcv)} candles, total: {len(all_ohlcv)}...")
            time.sleep(exchange.rateLimit / 1000) # Respect rate limits
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            break
            
    # Convert to DataFrame
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Save to CSV
    os.makedirs('data', exist_ok=True)
    filename = f"data/{symbol.replace('/', '_')}_{timeframe}.csv"
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} candles to {filename}")
    
    return df

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTC/USDT'
    timeframe = sys.argv[2] if len(sys.argv) > 2 else '1m'
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    
    download_historical_data(symbol, timeframe, 1000, days)
