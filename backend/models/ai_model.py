import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
import logging
from features.indicators import calculate_features

logger = logging.getLogger(__name__)

class AIScalpingModel:
    def __init__(self, model_path='ai_model.pkl'):
        self.model_path = model_path
        self.model = None

    def train(self, csv_file_path):
        logger.info(f"Loading data from {csv_file_path}...")
        df = pd.read_csv(csv_file_path)
        
        logger.info("Calculating features (Technical Indicators)...")
        df_features = calculate_features(df)
        
        # Select features dynamically
        bb_cols = [c for c in df_features.columns if c.startswith('BB')]
        macd_cols = [c for c in df_features.columns if c.startswith('MACD')]
        stoch_cols = [c for c in df_features.columns if c.startswith('STOCH')]
        atr_cols = [c for c in df_features.columns if c.startswith('ATR')]
        
        feature_cols = [
            'open', 'high', 'low', 'close', 'volume', 
            'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 
            'Volume_ROC'
        ] + bb_cols + macd_cols + stoch_cols + atr_cols
        
        # VWAP column name depends on the fallback or pandas_ta
        vwap_col = 'VWAP_D' if 'VWAP_D' in df_features.columns else 'VWAP'
        if vwap_col in df_features.columns:
            feature_cols.append(vwap_col)
            
        X = df_features[feature_cols]
        y = df_features['target']
        
        # Need to shift class labels from [-1, 0, 1] to [0, 1, 2] for XGBoost multiclass
        y_mapped = y + 1 
        
        logger.info(f"Training data shape: {X.shape}")
        
        # Split data (Chronological split is better for trading, no shuffle)
        X_train, X_test, y_train, y_test = train_test_split(X, y_mapped, test_size=0.2, shuffle=False)
        
        logger.info("Training XGBoost Classifier with Class Weights...")
        from sklearn.utils.class_weight import compute_sample_weight
        sample_weights = compute_sample_weight(class_weight='balanced', y=y_train)
        
        self.model = xgb.XGBClassifier(
            objective='multi:softprob',
            num_class=3,
            max_depth=6,
            learning_rate=0.01,
            n_estimators=300,
            n_jobs=-1,
            random_state=42
        )
        
        self.model.fit(X_train, y_train, sample_weight=sample_weights)
        
        logger.info("Evaluating model...")
        predictions = self.model.predict(X_test)
        
        acc = accuracy_score(y_test, predictions)
        logger.info(f"Accuracy: {acc*100:.2f}%")
        
        report = classification_report(y_test, predictions, target_names=['SELL (-1)', 'HOLD (0)', 'BUY (1)'], zero_division=0)
        print("\nClassification Report:")
        print(report)
        
        # Save model
        os.makedirs(os.path.dirname(self.model_path) if os.path.dirname(self.model_path) else '.', exist_ok=True)
        joblib.dump(self.model, self.model_path)
        logger.info(f"Model saved to {self.model_path}")

    def predict(self, current_features: pd.DataFrame):
        if self.model is None:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
            else:
                raise ValueError("Model is not trained or loaded yet.")
                
        # Must match feature_cols
        prediction = self.model.predict(current_features)
        # Shift back to -1, 0, 1
        return prediction[0] - 1

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # Allow passing dataset filename via arguments
    dataset_name = sys.argv[1] if len(sys.argv) > 1 else 'BTC_USDT_1m.csv'
    model_name = sys.argv[2] if len(sys.argv) > 2 else f"xgboost_scalping_{dataset_name.split('_')[0]}.pkl"
    
    model_path = f"models/{model_name}"
    model = AIScalpingModel(model_path=model_path)
    
    # Determine the correct data path depending on execution directory
    data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', dataset_name)
    if not os.path.exists(data_path):
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', dataset_name)
        if not os.path.exists(data_path):
            data_path = os.path.join(os.path.dirname(__file__), 'data', dataset_name)
            
    if os.path.exists(data_path):
        model.train(data_path)
    else:
        logger.error(f"Data file not found: {data_path}. Please run binance_proxy.py first.")
