import backtrader as bt
import pandas as pd
import logging
import os
import sys

# Add backend to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from features.indicators import calculate_features
from models.ai_model import AIScalpingModel

logger = logging.getLogger(__name__)

# Extend PandasData to include our AI Signal
class PandasDataWithSignal(bt.feeds.PandasData):
    lines = ('ai_signal',)
    params = (
        ('datetime', 'timestamp'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
        ('ai_signal', 'ai_signal'),
    )

class AIScalpingStrategy(bt.Strategy):
    params = (
        ('trade_size_pct', 0.95),  # Use 95% of available cash per trade
    )

    def __init__(self):
        self.signal = self.datas[0].ai_signal
        self.order = None

    def next(self):
        # Do nothing if an order is pending
        if self.order:
            return

        current_signal = self.signal[0]

        if not self.position:
            if current_signal == 1:
                # Buy manually to support crypto fractional sizes
                price = self.data.close[0]
                cash = self.broker.get_cash()
                size = (cash * self.p.trade_size_pct) / price
                self.order = self.buy(size=size)
                logger.debug(f"BUY CREATED at {price} size {size}")
        else:
            # Risk Management: Take Profit (1.0%) and Stop Loss (0.5%)
            profit_pct = (self.data.close[0] - self.position.price) / self.position.price
            
            if profit_pct >= 0.010:
                self.order = self.close()
                logger.debug(f"TAKE PROFIT HIT at {self.data.close[0]}")
            elif profit_pct <= -0.005:
                self.order = self.close()
                logger.debug(f"STOP LOSS HIT at {self.data.close[0]}")
            elif current_signal == -1:
                # AI predicted SELL
                self.order = self.close()
                logger.debug(f"AI SELL CREATED at {self.data.close[0]}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                logger.debug(f"BUY EXECUTED: Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}")
            elif order.issell():
                logger.debug(f"SELL EXECUTED: Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            logger.debug("Order Canceled/Margin/Rejected")

        self.order = None

def run_backtest(csv_path, model_path, initial_cash=1000.0, commission=0.001):
    """
    Run backtest with Hata simulation parameters.
    commission = 0.001 is 0.1% (Standard crypto exchange taker fee)
    """
    logger.info("Preparing data and AI predictions...")
    
    # 1. Load Data
    df = pd.read_csv(csv_path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    # 2. Calculate Features & Predict
    df_features = calculate_features(df)
    
    # Load Model directly using joblib for bulk prediction
    import joblib
    model_obj = joblib.load(model_path)
    # Get the feature columns that the model expects
    bb_cols = [c for c in df_features.columns if c.startswith('BB')]
    macd_cols = [c for c in df_features.columns if c.startswith('MACD')]
    stoch_cols = [c for c in df_features.columns if c.startswith('STOCH')]
    atr_cols = [c for c in df_features.columns if c.startswith('ATR')]
    
    feature_cols = ['open', 'high', 'low', 'close', 'volume', 'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 'Volume_ROC'] + bb_cols + macd_cols + stoch_cols + atr_cols
    vwap_col = 'VWAP_D' if 'VWAP_D' in df_features.columns else 'VWAP'
    if vwap_col in df_features.columns:
        feature_cols.append(vwap_col)
        
    X = df_features[feature_cols]
    
    # Predict using probabilities to filter out low-confidence signals
    probs = model_obj.predict_proba(X)
    # probs[:, 0] = SELL (-1), probs[:, 1] = HOLD (0), probs[:, 2] = BUY (1)
    
    import numpy as np
    signals = np.zeros(len(probs))
    # Hanya beli jika confidence > 65% (Disesuaikan untuk data setahun)
    signals[probs[:, 2] > 0.65] = 1
    # Hanya jual (kalau ada) jika confidence > 65%
    signals[probs[:, 0] > 0.65] = -1
    
    df_features['ai_signal'] = signals
    
    logger.info(f"Signal Counts:\n{df_features['ai_signal'].value_counts()}")
    
    # 3. Setup Backtrader
    cerebro = bt.Cerebro()
    cerebro.addstrategy(AIScalpingStrategy)

    # Convert to Backtrader Data Feed
    data = PandasDataWithSignal(dataname=df_features)
    cerebro.adddata(data)

    # Broker settings (Hata Simulation)
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    # Hata Slippage (optional to add slippage model, but commission covers basic costs)
    
    # Add Analyzers
    from backtest.metrics import add_analyzers
    add_analyzers(cerebro)

    # Run
    logger.info(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
    results = cerebro.run()
    logger.info(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")
    
    # Print Metrics
    from backtest.metrics import print_metrics
    print_metrics(results[0])
    
    return cerebro, results[0]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    dataset_name = sys.argv[1] if len(sys.argv) > 1 else 'BTC_USDT_1m.csv'
    model_name = sys.argv[2] if len(sys.argv) > 2 else f"xgboost_scalping_{dataset_name.split('_')[0]}.pkl"
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(base_dir, 'data', dataset_name)
    model_path = os.path.join(base_dir, 'models', model_name)
    
    if os.path.exists(data_path) and os.path.exists(model_path):
        run_backtest(data_path, model_path, initial_cash=1000.0) # RM1000 modal permulaan
    else:
        logger.error(f"Cannot find data ({data_path}) or model ({model_path})")
