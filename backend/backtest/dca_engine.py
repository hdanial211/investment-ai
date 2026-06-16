import backtrader as bt
import pandas as pd
import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from features.indicators import calculate_features

logger = logging.getLogger(__name__)

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

class DCALayeringStrategy(bt.Strategy):
    params = (
        ('trade_size_fiat', 50.0), # Buy RM50 per layer
        ('drop_threshold', -0.05), # -5% from average price to trigger next layer
        ('take_profit_pct', 0.02), # +2.0% from average price to sell all
    )

    def __init__(self):
        self.signal = self.datas[0].ai_signal
        self.order = None
        self.layer_count = 0
        
    def next(self):
        # Do nothing if an order is pending
        if self.order:
            return

        current_signal = self.signal[0]
        current_price = self.data.close[0]
        cash = self.broker.get_cash()

        # Phase 1: Not in position. Wait for AI signal to enter Layer 1.
        if not self.position:
            if current_signal == 1:
                # Need enough cash to buy RM 50
                if cash >= self.p.trade_size_fiat:
                    size = self.p.trade_size_fiat / current_price
                    self.order = self.buy(size=size)
                    self.layer_count = 1
                    logger.debug(f"INITIAL BUY (Layer 1) at {current_price} size {size}")
        
        # Phase 2: In position. Manage DCA Layers and Take Profit
        else:
            # Calculate PnL based on Average Price
            avg_price = self.position.price
            profit_pct = (current_price - avg_price) / avg_price
            
            # 1. Take Profit Condition (Sell ALL)
            if profit_pct >= self.p.take_profit_pct:
                self.order = self.close() # Close entire position
                self.layer_count = 0
                logger.debug(f"TAKE PROFIT HIT at {current_price} | Layers: {self.position.size} units | Profit: {profit_pct*100:.2f}%")
                return
                
            # 2. DCA Layering Condition
            if profit_pct <= self.p.drop_threshold:
                if cash >= self.p.trade_size_fiat:
                    size = self.p.trade_size_fiat / current_price
                    self.order = self.buy(size=size) # Add to existing position
                    self.layer_count += 1
                    logger.debug(f"DCA LAYER {self.layer_count} TRIGGERED at {current_price} | Drop: {profit_pct*100:.2f}%")
                else:
                    logger.warning("OUT OF CASH FOR DCA LAYER!")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            logger.debug("Order Canceled/Margin/Rejected")
            self.order = None

def run_dca_backtest(csv_path, model_path, initial_cash=10000.0, commission=0.001):
    logger.info("Preparing data and AI predictions...")
    
    df = pd.read_csv(csv_path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    df_features = calculate_features(df)
    
    # Load XGBoost model
    import joblib
    model_obj = joblib.load(model_path)
    bb_cols = [c for c in df_features.columns if c.startswith('BB')]
    macd_cols = [c for c in df_features.columns if c.startswith('MACD')]
    stoch_cols = [c for c in df_features.columns if c.startswith('STOCH')]
    atr_cols = [c for c in df_features.columns if c.startswith('ATR')]
    feature_cols = ['open', 'high', 'low', 'close', 'volume', 'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 'Volume_ROC'] + bb_cols + macd_cols + stoch_cols + atr_cols
    vwap_col = 'VWAP_D' if 'VWAP_D' in df_features.columns else 'VWAP'
    if vwap_col in df_features.columns:
        feature_cols.append(vwap_col)
        
    import numpy as np
    logger.info("Loading XGBoost model...")
    X = df_features[feature_cols]
    probs = model_obj.predict_proba(X)
    signals = np.zeros(len(probs))
    # Threshold for entry = 65%
    signals[probs[:, 2] > 0.65] = 1
    # We ignore sell signals (-1) because DCA relies purely on Take Profit math.
    
    df_features['ai_signal'] = signals
    
    # Setup Backtrader
    cerebro = bt.Cerebro()
    cerebro.addstrategy(DCALayeringStrategy)
    
    data = PandasDataWithSignal(dataname=df_features)
    cerebro.adddata(data)
    
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    
    from backtest.metrics import add_analyzers, print_metrics
    add_analyzers(cerebro)
    
    logger.info(f"Starting Portfolio Value: RM {cerebro.broker.getvalue():.2f}")
    results = cerebro.run()
    logger.info(f"Final Portfolio Value: RM {cerebro.broker.getvalue():.2f}")
    
    print_metrics(results[0])
    return cerebro, results[0]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dataset_name = sys.argv[1] if len(sys.argv) > 1 else 'ETH_USDT_1m.csv'
    model_name = sys.argv[2] if len(sys.argv) > 2 else f"xgboost_scalping_ETH_1y.pkl"
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(base_dir, 'data', dataset_name)
    model_path = os.path.join(base_dir, 'models', model_name)
    
    if os.path.exists(data_path) and os.path.exists(model_path):
        run_dca_backtest(data_path, model_path, initial_cash=10000.0)
    else:
        logger.error(f"Cannot find data ({data_path}) or model ({model_path})")
