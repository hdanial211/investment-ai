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
        ('datetime', None),
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
        ('drop_threshold', -0.05), # -5% from last buy price to trigger next layer
        ('take_profit_pct', 0.10), # Hard TP at +10.0%
        ('max_layers_per_signal', 6), # Max layers per signal sequence
        ('trailing_activation_pct', 0.03), # Activate trailing stop at +3.0%
        ('trailing_gap_pct', 0.01), # Trailing stop gap 1.0%
        ('progress_callback', None), # Callback for live progress
        ('total_len', 0), # Pass total length explicitly
        ('enable_dca', True), # Toggle DCA Layering vs Pure Scalping
        ('stop_loss_pct', -0.004), # Hard Stop Loss for Pure Scalping Mode
        ('rl_model', None),
        ('df_features', None),
        ('feature_cols', None),
        ('use_martingale', False),
        ('use_dynamic_tp', False)
    )

    def __init__(self):
        self.signal = self.datas[0].ai_signal
        self.order = None
        self.layer_count = 0
        self.current_sequence_layers = 0
        self.last_buy_price = None
        self.max_profit_pct = 0.0
        self.total_len = self.p.total_len
        self.last_progress_pct = 0
        
    def next(self):
        current_len = len(self)
        if self.total_len > 0:
            progress_pct = int((current_len / self.total_len) * 100)
            if progress_pct > self.last_progress_pct and self.p.progress_callback:
                self.p.progress_callback({"type": "progress", "percent": progress_pct})
                self.last_progress_pct = progress_pct

        # Do nothing if an order is pending
        if self.order:
            return

        timestamp = self.data.datetime.datetime(0).strftime('%Y-%m-%d %H:%M:%S')
        current_price = self.data.close[0]
        cash = self.broker.get_cash()
        
        # 1. Evaluate Signal
        rl_action = 0
        xgb_signal = self.data.ai_signal[0]
        
        if self.p.rl_model is not None:
            import numpy as np
            idx = len(self) - 1
            start_idx = max(0, idx - 15 + 1)
            end_idx = idx + 1
            window_df = self.p.df_features.iloc[start_idx:end_idx]
            features = window_df[self.p.feature_cols].values.astype(np.float32)
            
            pad_len = 15 - len(features)
            if pad_len > 0:
                features = np.pad(features, ((pad_len, 0), (0, 0)), mode='edge')
                
            unrealized_profit = 0.0
            pos = 0
            time_held = 0
            if self.position.size > 0:
                pos = 1
                if self.last_buy_price:
                    unrealized_profit = (current_price - self.last_buy_price) / self.last_buy_price
                time_held = 10 # Approx placeholder
                
            state_vars = np.array([pos, unrealized_profit, time_held], dtype=np.float32)
            state_vars_repeated = np.tile(state_vars, (15, 1))
            
            obs = np.concatenate((features, state_vars_repeated), axis=1)
            obs = np.nan_to_num(obs, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
            
            action, _ = self.p.rl_model.predict(obs, deterministic=True)
            rl_action = action
            
        if self.p.rl_model is not None and xgb_signal == 1:
            # Ensemble OR logic
            current_signal = 1
        elif self.p.rl_model is not None:
            current_signal = rl_action
        else:
            current_signal = xgb_signal
        
        # Phase 1: Not in position. Wait for AI signal to enter Layer 1.
        if not self.position:
            if current_signal == 1:
                # Need enough cash to buy
                if cash >= self.p.trade_size_fiat:
                    size = self.p.trade_size_fiat / current_price
                    self.order = self.buy(size=size)
                    self.layer_count = 1
                    self.current_sequence_layers = 1
                    self.last_buy_price = current_price
                    self.max_profit_pct = 0.0
                    msg = f"INITIAL BUY at RM{current_price:,.2f} size {size:.5f} units | Bal: RM{self.broker.getvalue():,.2f}"
                    logger.debug(msg)
                    if self.p.progress_callback:
                        self.p.progress_callback({"type": "trade", "message": f"[{timestamp}] 🟢 " + msg})
        
        # Phase 2: In position. Manage DCA Layers and Take Profit
        else:
            avg_price = self.position.price
            total_profit_pct = (current_price - avg_price) / avg_price
            
            if total_profit_pct > self.max_profit_pct:
                self.max_profit_pct = total_profit_pct
            
            # 1. Take Profit / Trailing Stop Condition
            # Dynamic TP Calculation
            active_tp = self.p.take_profit_pct
            if self.p.use_dynamic_tp:
                if self.current_sequence_layers == 1:
                    active_tp = 0.0025
                elif self.current_sequence_layers == 2:
                    active_tp = 0.0030
                elif self.current_sequence_layers == 3:
                    active_tp = 0.0035
                elif self.current_sequence_layers >= 4:
                    active_tp = 0.0040

            # Hard TP (Sell ALL)
            if total_profit_pct >= active_tp:
                size = self.position.size
                self.order = self.close() # Close entire position
                self.layer_count = 0
                self.current_sequence_layers = 0
                self.last_buy_price = None
                self.max_profit_pct = 0.0
                msg = f"HARD TAKE PROFIT HIT at RM{current_price:,.2f} | Profit: +{total_profit_pct*100:.2f}% | Bal: RM{self.broker.getvalue():,.2f}"
                logger.debug(msg)
                if self.p.progress_callback:
                    self.p.progress_callback({"type": "trade", "message": f"[{timestamp}] 🔴 " + msg})
                return
                
            # Trailing Stop Condition
            if self.max_profit_pct >= self.p.trailing_activation_pct:
                trailing_stop_pct = self.max_profit_pct - self.p.trailing_gap_pct
                if total_profit_pct <= trailing_stop_pct:
                    size = self.position.size
                    self.order = self.close() # Close entire position
                    self.layer_count = 0
                    self.current_sequence_layers = 0
                    self.last_buy_price = None
                    self.max_profit_pct = 0.0
                    msg = f"TRAILING STOP HIT at RM{current_price:,.2f} | Profit: +{total_profit_pct*100:.2f}% (Max: +{self.max_profit_pct*100:.2f}%) | Bal: RM{self.broker.getvalue():,.2f}"
                    logger.debug(msg)
                    if self.p.progress_callback:
                        self.p.progress_callback({"type": "trade", "message": f"[{timestamp}] 🔴 " + msg})
                    return
                
            # Pure Scalping Mode (Stop Loss Hit)
            if not self.p.enable_dca:
                if total_profit_pct <= self.p.stop_loss_pct:
                    size = self.position.size
                    self.order = self.close()
                    self.layer_count = 0
                    self.current_sequence_layers = 0
                    self.last_buy_price = None
                    self.max_profit_pct = 0.0
                    msg = f"STOP LOSS HIT at RM{current_price:,.2f} | Loss: {total_profit_pct*100:.2f}% | Bal: RM{self.broker.getvalue():,.2f}"
                    logger.debug(msg)
                    if self.p.progress_callback:
                        self.p.progress_callback({"type": "trade", "message": f"[{timestamp}] ⚠️ " + msg})
                    return
                
            # 2. Signal-Based Layering (If AI throws a new signal, just buy!)
            if current_signal == 1 and self.last_buy_price is not None:
                drop_from_last_buy = (current_price - self.last_buy_price) / self.last_buy_price
                if drop_from_last_buy <= self.p.drop_threshold and self.layer_count < self.p.max_layers_per_signal: 
                    target_size_fiat = self.p.trade_size_fiat
                    if self.p.use_martingale:
                        target_size_fiat = self.p.trade_size_fiat * 1  # Reset to 1x multiplier for fresh AI signal
                    if cash >= target_size_fiat:
                        size = target_size_fiat / current_price
                        self.order = self.buy(size=size)
                        self.layer_count += 1
                        self.current_sequence_layers = 1 # RESET sequence so TP resets to 0.25%
                        self.last_buy_price = current_price
                        msg = f"AI SIGNAL LAYER TRIGGERED (RESET SEQ) at RM{current_price:,.2f} | Total Layers: {self.layer_count} | Bal: RM{self.broker.getvalue():,.2f}"
                        logger.debug(msg)
                        if self.p.progress_callback:
                            self.p.progress_callback({"type": "trade", "message": f"[{timestamp}] 🔵 " + msg})
                    return
                
            # 3. DCA Layering Condition (only if total layers < max AND DCA is enabled)
            if self.p.enable_dca and self.last_buy_price is not None:
                drop_from_last_buy = (current_price - self.last_buy_price) / self.last_buy_price
                if drop_from_last_buy <= self.p.drop_threshold and self.layer_count < self.p.max_layers_per_signal:
                    target_size_fiat = self.p.trade_size_fiat
                    if self.p.use_martingale:
                        target_size_fiat = self.p.trade_size_fiat * (2 ** self.current_sequence_layers) # 2x, 4x, 8x
                    if cash >= target_size_fiat:
                        size = target_size_fiat / current_price
                        self.order = self.buy(size=size) # Add to existing position
                        self.layer_count += 1
                        self.current_sequence_layers += 1 # Increment sequence so TP increases
                        self.last_buy_price = current_price
                        msg = f"DCA LAYER {self.layer_count}/{self.p.max_layers_per_signal} TRIGGERED at RM{current_price:,.2f} | Drop: {drop_from_last_buy*100:.2f}% | Bal: RM{self.broker.getvalue():,.2f}"
                        logger.debug(msg)
                        if self.p.progress_callback:
                            self.p.progress_callback({"type": "trade", "message": f"[{timestamp}] 🔵 " + msg})

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            logger.debug("Order Canceled/Margin/Rejected")
            self.order = None

def run_dca_backtest(csv_path, model_path, initial_cash=100000.0, trade_size_fiat=4000.0, commission=0.000, 
                     drop_threshold=-0.05, take_profit_pct=0.10, max_layers_per_signal=6,
                     trailing_activation_pct=0.03, trailing_gap_pct=0.01, progress_callback=None,
                     enable_dca=True, stop_loss_pct=-0.004, ai_type="xgboost", use_martingale=False, use_dynamic_tp=False):
    logger.info(f"Preparing data and {ai_type} AI predictions...")
    
    df = pd.read_csv(csv_path)
    # Using full dataset as requested
    pass
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    df_features = calculate_features(df)
    
    if 'timestamp' in df_features.columns:
        df_features.set_index('timestamp', inplace=True)
    
    # Load model (dynamically below)
    import joblib
    bb_cols = [c for c in df_features.columns if c.startswith('BB')]
    macd_cols = [c for c in df_features.columns if c.startswith('MACD')]
    stoch_cols = [c for c in df_features.columns if c.startswith('STOCH')]
    atr_cols = [c for c in df_features.columns if c.startswith('ATR')]
    feature_cols = ['open', 'high', 'low', 'close', 'volume', 'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 'Volume_ROC'] + bb_cols + macd_cols + stoch_cols + atr_cols
    vwap_col = 'VWAP_D' if 'VWAP_D' in df_features.columns else 'VWAP'
    if vwap_col in df_features.columns:
        feature_cols.append(vwap_col)
        
    import numpy as np
    
    rl_model = None
    if ai_type == "xgboost" or ai_type == "ensemble":
        logger.info("Loading XGBoost model...")
        model_obj = joblib.load(model_path.replace("ppo_lstm", "xgboost_scalping").replace(".zip", "_1y.pkl")) if ai_type=="ensemble" else joblib.load(model_path)
        X = df_features[feature_cols]
        probs = model_obj.predict_proba(X)
        signals = np.zeros(len(probs))
        signals[probs[:, 1] > 0.60] = 1
        df_features['ai_signal'] = signals
    else:
        df_features['ai_signal'] = 0
        
    if ai_type == "rl_lstm" or ai_type == "ensemble":
        logger.info("Loading RL+LSTM model...")
        from stable_baselines3 import PPO
        try:
            rl_path = model_path if ai_type == "rl_lstm" else model_path.replace("xgboost_scalping", "ppo_lstm").replace("_1y.pkl", ".zip")
            if rl_path.endswith('.zip'):
                rl_model = PPO.load(rl_path[:-4])
            else:
                rl_model = PPO.load(rl_path)
        except Exception as e:
            logger.error(f"Failed to load RL model: {e}")
            rl_model = None
        
    # Setup Backtrader
    cerebro = bt.Cerebro()
    total_len = len(df_features)
    cerebro.addstrategy(
        DCALayeringStrategy, 
        trade_size_fiat=trade_size_fiat,
        drop_threshold=drop_threshold,
        take_profit_pct=take_profit_pct,
        max_layers_per_signal=max_layers_per_signal,
        trailing_activation_pct=trailing_activation_pct,
        trailing_gap_pct=trailing_gap_pct,
        progress_callback=progress_callback,
        total_len=total_len,
        enable_dca=enable_dca,
        stop_loss_pct=stop_loss_pct,
        rl_model=rl_model,
        df_features=df_features,
        feature_cols=feature_cols,
        use_martingale=use_martingale,
        use_dynamic_tp=use_dynamic_tp
    )
    
    data = PandasDataWithSignal(dataname=df_features)
    cerebro.adddata(data)
    
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    
    from backtest.metrics import add_analyzers, print_metrics, get_metrics_dict
    add_analyzers(cerebro)
    
    logger.info(f"Starting Portfolio Value: RM {cerebro.broker.getvalue():.2f}")
    results = cerebro.run()
    
    final_value = cerebro.broker.getvalue()
    logger.info(f"Final Portfolio Value: RM {final_value:.2f}")
    
    print_metrics(results[0])
    metrics_dict = get_metrics_dict(results[0])
    metrics_dict['final_value'] = final_value
    
    return metrics_dict

if __name__ == "__main__":
    import log_config
    dataset_name = sys.argv[1] if len(sys.argv) > 1 else 'ETH_USDT_1m.csv'
    model_name = sys.argv[2] if len(sys.argv) > 2 else f"xgboost_scalping_ETH_1y.pkl"
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(base_dir, 'data', dataset_name)
    model_path = os.path.join(base_dir, 'models', model_name)
    
    if os.path.exists(data_path) and os.path.exists(model_path):
        run_dca_backtest(data_path, model_path, initial_cash=100000.0, trade_size_fiat=4000.0, commission=0.000)
    else:
        logger.error(f"Cannot find data ({data_path}) or model ({model_path})")
