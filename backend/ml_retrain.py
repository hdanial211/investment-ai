"""
ml_retrain.py — Auto-Retrain Engine for Adaptive ML Pipeline (Per-Coin)

Periodically retrains XGBoost models using BOTH historical data AND live trade
outcomes. Each coin has its own independent retrain cycle.

Trigger: Every 20 completed trades per coin OR every 3 days (whichever first)
Strategy: Always deploy new model (continuous learning, no blocking)
"""
import os
import sys
import json
import time
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Retrain configuration (per-coin)
RETRAIN_TRADE_THRESHOLD = 20   # Retrain after 20 completed trades
RETRAIN_TIME_DAYS = 3          # Or retrain every 3 days
MIN_TRAINING_SAMPLES = 50      # Minimum samples to even attempt retrain


def should_retrain(coin_id: str) -> bool:
    """Check if this specific coin needs retraining."""
    try:
        import shared
        coin_state = shared.engine_state.get(coin_id, {})
        
        trades_since = coin_state.get("trades_since_retrain", 0)
        last_retrain_str = coin_state.get("last_retrain_at")
        
        # Check trade threshold
        if trades_since >= RETRAIN_TRADE_THRESHOLD:
            logger.info(
                f"[{coin_id}] RETRAIN CHECK: {trades_since} trades since last retrain "
                f"(threshold: {RETRAIN_TRADE_THRESHOLD}). Retrain needed."
            )
            return True
        
        # Check time threshold
        if last_retrain_str:
            try:
                last_retrain = datetime.fromisoformat(last_retrain_str)
                days_since = (datetime.utcnow() - last_retrain).days
                if days_since >= RETRAIN_TIME_DAYS:
                    logger.info(
                        f"[{coin_id}] RETRAIN CHECK: {days_since} days since last retrain "
                        f"(threshold: {RETRAIN_TIME_DAYS}). Retrain needed."
                    )
                    return True
            except (ValueError, TypeError):
                pass
        else:
            # Never retrained — check if we have enough data
            from ml_logger import get_training_data
            df = get_training_data(coin_id, limit=MIN_TRAINING_SAMPLES)
            if len(df) >= MIN_TRAINING_SAMPLES:
                logger.info(
                    f"[{coin_id}] RETRAIN CHECK: Never retrained but have "
                    f"{len(df)} logged trades. Retrain needed."
                )
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"[{coin_id}] Error checking retrain status: {e}")
        return False


def retrain_coin(coin_id: str) -> bool:
    """
    Retrain the XGBoost model for a SPECIFIC coin using:
    1. Historical CSV data (existing training data)
    2. Live trade outcomes from ML training log (weighted 3x)
    
    Always deploys the new model (continuous learning).
    
    Returns True if retrain was successful.
    """
    try:
        import shared
        from features.indicators import calculate_features
        from ml_logger import get_training_data, update_model_performance
        from ml_adaptive import recalculate_threshold_for_coin
        
        logger.info(f"[{coin_id}] ★ RETRAIN: Starting model retrain...")
        
        # 1. Determine new version number
        current_version = shared.engine_state.get(coin_id, {}).get("model_version", "v1")
        try:
            version_num = int(current_version.replace("v", "")) + 1
        except (ValueError, AttributeError):
            version_num = 2
        new_version = f"v{version_num}"
        
        # 2. Load historical CSV data for this coin
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, '..', 'data', f'{coin_id}_USDT_1m.csv')
        
        if not os.path.exists(csv_path):
            # Try alternative paths
            csv_path = os.path.join(base_dir, 'data', f'{coin_id}_USDT_1m.csv')
            if not os.path.exists(csv_path):
                logger.error(f"[{coin_id}] RETRAIN: CSV data not found at {csv_path}")
                return False
        
        logger.info(f"[{coin_id}] RETRAIN: Loading historical data from {csv_path}")
        df_hist = pd.read_csv(csv_path)
        
        # Use last 3 months of data (approx 129,600 minutes)
        df_hist = df_hist.tail(129600).reset_index(drop=True)
        
        logger.info(f"[{coin_id}] RETRAIN: Calculating features for {len(df_hist)} candles...")
        df_features = calculate_features(df_hist)
        
        # 3. Build feature columns (same as ai_model.py)
        bb_cols = [c for c in df_features.columns if c.startswith('BB')]
        macd_cols = [c for c in df_features.columns if c.startswith('MACD')]
        stoch_cols = [c for c in df_features.columns if c.startswith('STOCH')]
        atr_cols = [c for c in df_features.columns if c.startswith('ATR')]
        
        feature_cols = [
            'open', 'high', 'low', 'close', 'volume',
            'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14',
            'Volume_ROC'
        ] + bb_cols + macd_cols + stoch_cols + atr_cols
        
        vwap_col = 'VWAP_D' if 'VWAP_D' in df_features.columns else 'VWAP'
        if vwap_col in df_features.columns:
            feature_cols.append(vwap_col)
        
        # 4. Apply Triple Barrier Labelling (same as ai_model.py)
        from numba import jit
        
        @jit(nopython=True)
        def apply_triple_barrier(closes, highs, lows, tp_pct, sl_pct, max_horizon):
            n = len(closes)
            labels = np.zeros(n, dtype=np.int32)
            for i in range(n - 1):
                entry_price = closes[i]
                tp_price = entry_price * (1 + tp_pct)
                sl_price = entry_price * (1 + sl_pct)
                label = 0
                for j in range(1, max_horizon + 1):
                    idx = i + j
                    if idx >= n:
                        break
                    if lows[idx] <= sl_price:
                        label = 0
                        break
                    if highs[idx] >= tp_price:
                        label = 1
                        break
                labels[i] = label
            return labels
        
        closes = df_features['close'].values
        highs = df_features['high'].values
        lows = df_features['low'].values
        
        labels = apply_triple_barrier(closes, highs, lows, 0.006, -0.004, 60)
        df_features['target'] = labels
        df_features = df_features.iloc[:-60].reset_index(drop=True)
        
        X_hist = df_features[feature_cols]
        y_hist = df_features['target']
        
        # 5. Load live trade outcomes (boosted weight for real experience)
        live_data = get_training_data(coin_id, limit=500)
        
        live_features = None
        live_labels = None
        live_weight_multiplier = 3.0  # Live data weighted 3x more
        
        if len(live_data) >= 10:
            logger.info(f"[{coin_id}] RETRAIN: Incorporating {len(live_data)} live trade outcomes (3x weight)")
            
            # Extract features that match our feature_cols
            available_cols = [c for c in feature_cols if c in live_data.columns]
            if len(available_cols) >= 5:  # At least some features available
                live_features = live_data[available_cols].copy()
                # Fill missing columns with 0
                for col in feature_cols:
                    if col not in live_features.columns:
                        live_features[col] = 0.0
                live_features = live_features[feature_cols]
                
                # Convert outcomes to labels: WIN=1, LOSS=0
                live_labels = (live_data['_outcome'] == 'WIN').astype(int)
        
        # 6. Combine training data
        if live_features is not None and len(live_features) > 0:
            X_combined = pd.concat([X_hist, live_features], ignore_index=True)
            y_combined = pd.concat([y_hist, live_labels], ignore_index=True)
            
            # Create sample weights: 1.0 for historical, 3.0 for live
            hist_weights = np.ones(len(X_hist))
            live_weights = np.full(len(live_features), live_weight_multiplier)
            sample_weights = np.concatenate([hist_weights, live_weights])
        else:
            X_combined = X_hist
            y_combined = y_hist
            sample_weights = None
        
        # Drop any NaN rows
        mask = X_combined.notna().all(axis=1) & y_combined.notna()
        X_combined = X_combined[mask].reset_index(drop=True)
        y_combined = y_combined[mask].reset_index(drop=True)
        if sample_weights is not None:
            sample_weights = sample_weights[mask.values]
        
        logger.info(f"[{coin_id}] RETRAIN: Total training samples: {len(X_combined)}")
        
        if len(X_combined) < MIN_TRAINING_SAMPLES:
            logger.warning(f"[{coin_id}] RETRAIN: Not enough samples ({len(X_combined)}). Skipping.")
            return False
        
        # 7. Train new XGBoost model
        import xgboost as xgb
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        from sklearn.utils.class_weight import compute_sample_weight
        
        # Chronological split (no shuffle for time series)
        X_train, X_test, y_train, y_test = train_test_split(
            X_combined, y_combined, test_size=0.2, shuffle=False
        )
        
        if sample_weights is not None:
            w_train = sample_weights[:len(X_train)]
        else:
            w_train = compute_sample_weight(class_weight='balanced', y=y_train)
        
        model = xgb.XGBClassifier(
            objective='binary:logistic',
            max_depth=6,
            learning_rate=0.01,
            n_estimators=300,
            n_jobs=-1,
            random_state=42
        )
        
        logger.info(f"[{coin_id}] RETRAIN: Training XGBoost {new_version}...")
        model.fit(X_train, y_train, sample_weight=w_train)
        
        # 8. Evaluate
        predictions = model.predict(X_test)
        
        acc = accuracy_score(y_test, predictions)
        prec = precision_score(y_test, predictions, zero_division=0)
        rec = recall_score(y_test, predictions, zero_division=0)
        f1 = f1_score(y_test, predictions, zero_division=0)
        
        logger.info(
            f"[{coin_id}] RETRAIN: {new_version} metrics — "
            f"Accuracy={acc*100:.1f}%, Precision={prec*100:.1f}%, "
            f"Recall={rec*100:.1f}%, F1={f1*100:.1f}%"
        )
        
        # 9. Save new model (always deploy — continuous learning)
        models_dir = os.path.join(base_dir, '..', 'models')
        if not os.path.exists(models_dir):
            models_dir = os.path.join(base_dir, 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        # Save as versioned file
        versioned_path = os.path.join(models_dir, f'xgboost_scalping_{coin_id}_{new_version}.pkl')
        joblib.dump(model, versioned_path)
        
        # Also overwrite the main model file (used by live engine)
        main_model_path = os.path.join(models_dir, f'xgboost_scalping_{coin_id}_1y.pkl')
        joblib.dump(model, main_model_path)
        
        logger.info(f"[{coin_id}] RETRAIN: Model saved → {versioned_path} + {main_model_path}")
        
        # 10. Update model performance tracking
        update_model_performance(coin_id, new_version, {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "training_samples": len(X_combined)
        })
        
        # 11. Update shared state for this coin
        shared.engine_state[coin_id]["model_version"] = new_version
        shared.engine_state[coin_id]["trades_since_retrain"] = 0
        shared.engine_state[coin_id]["last_retrain_at"] = datetime.utcnow().isoformat()
        shared.save_state()
        
        # 12. Recalculate adaptive threshold for this coin
        recalculate_threshold_for_coin(coin_id)
        
        logger.info(f"[{coin_id}] ★ RETRAIN COMPLETE: {new_version} deployed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"[{coin_id}] RETRAIN ERROR: {e}", exc_info=True)
        return False


def hot_reload_model(coin_id: str):
    """
    Hot-reload the XGBoost model for a specific coin into the live engine.
    Called after retrain to swap model without restarting bot.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, '..', 'models', f'xgboost_scalping_{coin_id}_1y.pkl')
        
        if not os.path.exists(model_path):
            model_path = os.path.join(base_dir, 'models', f'xgboost_scalping_{coin_id}_1y.pkl')
        
        if os.path.exists(model_path):
            new_model = joblib.load(model_path)
            
            # Import and update the MODELS dict in live_engine
            import live_engine
            live_engine.MODELS[coin_id] = new_model
            
            import shared
            version = shared.engine_state.get(coin_id, {}).get("model_version", "?")
            logger.info(f"[{coin_id}] HOT RELOAD: Model {version} loaded into live engine!")
            return True
        else:
            logger.error(f"[{coin_id}] HOT RELOAD: Model file not found at {model_path}")
            return False
            
    except Exception as e:
        logger.error(f"[{coin_id}] HOT RELOAD ERROR: {e}")
        return False


def check_and_retrain_all():
    """
    Check all 5 coins and retrain any that need it.
    Called periodically from the live engine background loop.
    """
    coins = ["BTC", "ETH", "SOL", "XRP", "LTC"]
    
    for coin_id in coins:
        try:
            if should_retrain(coin_id):
                success = retrain_coin(coin_id)
                if success:
                    hot_reload_model(coin_id)
                    logger.info(f"[{coin_id}] Auto-retrain + hot-reload complete!")
                else:
                    logger.warning(f"[{coin_id}] Auto-retrain failed. Keeping current model.")
        except Exception as e:
            logger.error(f"[{coin_id}] Error in auto-retrain check: {e}")


if __name__ == "__main__":
    """Manual retrain for testing."""
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import log_config
    
    coin = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    print(f"Manual retrain for {coin}...")
    success = retrain_coin(coin)
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
