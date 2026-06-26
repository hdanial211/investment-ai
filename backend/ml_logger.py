"""
ml_logger.py — Trade Outcome Logger for Adaptive ML Pipeline

Logs every AI prediction and trade outcome PER COIN for continuous learning.
Each coin's data is kept COMPLETELY SEPARATE — never mixed.

Key functions:
1. log_prediction()    — Called on every XGBoost prediction in process_kline()
2. log_trade_outcome() — Called when consolidated sell fills (cycle complete)
3. get_training_data() — Returns logged data for retrain engine
4. get_ml_stats()      — Returns ML performance stats per coin
5. update_model_performance() — Saves new model training metrics
"""
import json
import time
import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


def _get_session():
    """Get a new database session. Caller must close it."""
    from database.models import SessionLocal
    return SessionLocal()


# ─────────────────────────────────────────────
# 1. Log AI Prediction
# ─────────────────────────────────────────────
def log_prediction(coin_id: str, features_dict: dict, confidence: float,
                   signal: int, current_price: float, model_version: str = "v1"):
    """
    Log an AI prediction event. Called every time XGBoost runs in process_kline().
    
    Only logs when:
      - signal=1 (Golden Entry triggered), OR
      - confidence > 0.50 (near-miss, valuable for learning)
    
    Args:
        coin_id: Coin symbol (BTC, ETH, SOL, XRP, LTC)
        features_dict: Feature vector at time of prediction (dict)
        confidence: XGBoost probability 0.0-1.0
        signal: 1=Golden Entry, 0=No Entry
        current_price: Current price at prediction time
        model_version: Model version string (e.g. 'v1', 'v2')
    
    Returns:
        trade_cycle_id (str) if signal=1, else None
    """
    # Only log significant predictions (signal=1 or near-miss)
    if signal != 1 and confidence <= 0.50:
        return None

    trade_cycle_id = None
    
    try:
        from database.ml_models import MLTrainingLog
        
        # Generate trade cycle ID for signal=1 (for outcome matching later)
        if signal == 1:
            trade_cycle_id = f"{coin_id}_{int(time.time())}"
            # Store in shared state so we can match outcome later
            try:
                import shared
                if coin_id in shared.engine_state:
                    shared.engine_state[coin_id]["active_trade_cycle_id"] = trade_cycle_id
            except Exception:
                pass

        # Serialize features (keep only numeric values, skip NaN)
        try:
            clean_features = {}
            for k, v in features_dict.items():
                if isinstance(v, (int, float)) and v == v:  # v == v filters NaN
                    clean_features[k] = round(float(v), 6)
            features_str = json.dumps(clean_features)
        except Exception:
            features_str = "{}"

        session = _get_session()
        try:
            entry = MLTrainingLog(
                coin_id=coin_id,
                timestamp=datetime.utcnow(),
                features_json=features_str,
                confidence=confidence,
                predicted_signal=signal,
                actual_outcome="PENDING" if signal == 1 else None,
                entry_price=current_price if signal == 1 else None,
                model_version=model_version,
                trade_cycle_id=trade_cycle_id
            )
            session.add(entry)
            session.commit()
            
            if signal == 1:
                logger.info(
                    f"[{coin_id}] ML LOG: Prediction logged — "
                    f"confidence={confidence*100:.1f}%, signal=GOLDEN_ENTRY, "
                    f"cycle={trade_cycle_id}, model={model_version}"
                )
        finally:
            session.close()

    except Exception as e:
        logger.error(f"[{coin_id}] ML LOG ERROR (prediction): {e}")

    return trade_cycle_id


# ─────────────────────────────────────────────
# 2. Log Trade Outcome
# ─────────────────────────────────────────────
def log_trade_outcome(coin_id: str, entry_price: float, exit_price: float,
                      pnl_myr: float, pnl_pct: float, hold_duration_min: int,
                      layers_used: int, fee_total_myr: float):
    """
    Log the actual trade outcome when consolidated sell fills.
    Updates the matching MLTrainingLog entry with real results.
    
    Args:
        coin_id: Coin symbol
        entry_price: Average entry price (weighted)
        exit_price: Sell price
        pnl_myr: Profit/loss in MYR
        pnl_pct: Profit/loss percentage
        hold_duration_min: How long position was held (minutes)
        layers_used: Number of DCA layers used
        fee_total_myr: Total fees paid in MYR
    """
    try:
        from database.ml_models import MLTrainingLog, ModelPerformance
        import shared

        # Determine outcome
        if pnl_myr > 0:
            outcome = "WIN"
        elif pnl_myr < 0:
            outcome = "LOSS"
        else:
            outcome = "TIMEOUT"

        # Find matching prediction using trade_cycle_id
        active_cycle_id = shared.engine_state.get(coin_id, {}).get("active_trade_cycle_id")
        
        session = _get_session()
        try:
            updated = False
            
            if active_cycle_id:
                # Find exact match by cycle ID
                entry = (
                    session.query(MLTrainingLog)
                    .filter(
                        MLTrainingLog.trade_cycle_id == active_cycle_id,
                        MLTrainingLog.coin_id == coin_id
                    )
                    .first()
                )
                
                if entry:
                    entry.actual_outcome = outcome
                    entry.exit_price = exit_price
                    entry.pnl_myr = pnl_myr
                    entry.pnl_pct = pnl_pct
                    entry.hold_duration_min = hold_duration_min
                    entry.layers_used = layers_used
                    entry.fee_total_myr = fee_total_myr
                    session.commit()
                    updated = True
            
            if not updated:
                # Fallback: find most recent PENDING entry for this coin
                entry = (
                    session.query(MLTrainingLog)
                    .filter(
                        MLTrainingLog.coin_id == coin_id,
                        MLTrainingLog.actual_outcome == "PENDING",
                        MLTrainingLog.predicted_signal == 1
                    )
                    .order_by(MLTrainingLog.timestamp.desc())
                    .first()
                )
                
                if entry:
                    entry.actual_outcome = outcome
                    entry.exit_price = exit_price
                    entry.entry_price = entry_price
                    entry.pnl_myr = pnl_myr
                    entry.pnl_pct = pnl_pct
                    entry.hold_duration_min = hold_duration_min
                    entry.layers_used = layers_used
                    entry.fee_total_myr = fee_total_myr
                    session.commit()
                    updated = True
                else:
                    # No prediction found — create new entry for this outcome
                    new_entry = MLTrainingLog(
                        coin_id=coin_id,
                        timestamp=datetime.utcnow(),
                        confidence=0.0,
                        predicted_signal=1,
                        actual_outcome=outcome,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        pnl_myr=pnl_myr,
                        pnl_pct=pnl_pct,
                        hold_duration_min=hold_duration_min,
                        layers_used=layers_used,
                        fee_total_myr=fee_total_myr,
                        model_version=shared.engine_state.get(coin_id, {}).get("model_version", "v1")
                    )
                    session.add(new_entry)
                    session.commit()
                    updated = True

            # Update live performance for active model
            if updated:
                _update_live_model_stats(session, coin_id, outcome, pnl_myr)
                session.commit()

        finally:
            session.close()

        # Update shared state counters
        if coin_id in shared.engine_state:
            ml_stats = shared.engine_state[coin_id].get("ml_stats", {})
            ml_stats["total_trades_logged"] = ml_stats.get("total_trades_logged", 0) + 1
            
            # Increment trades_since_retrain
            shared.engine_state[coin_id]["trades_since_retrain"] = \
                shared.engine_state[coin_id].get("trades_since_retrain", 0) + 1
            shared.engine_state[coin_id]["ml_stats"] = ml_stats
            
            # Clear active trade cycle
            shared.engine_state[coin_id]["active_trade_cycle_id"] = None
            shared.save_state()

        logger.info(
            f"[{coin_id}] ML LOG: Trade outcome={outcome} | "
            f"PnL=RM{pnl_myr:.2f} ({pnl_pct*100:.2f}%) | "
            f"Hold={hold_duration_min}min | Layers={layers_used} | "
            f"Fee=RM{fee_total_myr:.4f}"
        )

    except Exception as e:
        logger.error(f"[{coin_id}] ML LOG ERROR (outcome): {e}")


def _update_live_model_stats(session, coin_id: str, outcome: str, pnl_myr: float):
    """Update the active model's live stats with a new trade result."""
    try:
        from database.ml_models import ModelPerformance
        
        perf = (
            session.query(ModelPerformance)
            .filter(
                ModelPerformance.coin_id == coin_id,
                ModelPerformance.is_active == True
            )
            .first()
        )
        
        if perf:
            perf.total_trades += 1
            perf.total_pnl += pnl_myr
            
            # Recalculate win rate
            wins = session.query(MLTrainingLog).filter(
                MLTrainingLog.coin_id == coin_id,
                MLTrainingLog.actual_outcome == "WIN",
                MLTrainingLog.model_version == perf.model_version
            ).count()
            
            total = session.query(MLTrainingLog).filter(
                MLTrainingLog.coin_id == coin_id,
                MLTrainingLog.actual_outcome.in_(["WIN", "LOSS"]),
                MLTrainingLog.model_version == perf.model_version
            ).count()
            
            if total > 0:
                perf.win_rate_live = round(wins / total, 4)
                perf.avg_pnl_per_trade = round(perf.total_pnl / perf.total_trades, 4)
                
    except Exception as e:
        logger.error(f"[{coin_id}] Error updating model live stats: {e}")


# ─────────────────────────────────────────────
# 3. Get Training Data for Retrain
# ─────────────────────────────────────────────
def get_training_data(coin_id: str, limit: int = 500) -> pd.DataFrame:
    """
    Get logged prediction data with outcomes for this coin (for retraining).
    Returns DataFrame with features + outcomes. Each coin is separate.
    """
    try:
        from database.ml_models import MLTrainingLog
        
        session = _get_session()
        try:
            entries = (
                session.query(MLTrainingLog)
                .filter(
                    MLTrainingLog.coin_id == coin_id,
                    MLTrainingLog.actual_outcome.in_(["WIN", "LOSS"]),
                    MLTrainingLog.features_json.isnot(None)
                )
                .order_by(MLTrainingLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            
            if not entries:
                return pd.DataFrame()
            
            rows = []
            for e in entries:
                try:
                    features = json.loads(e.features_json) if e.features_json else {}
                    features["_outcome"] = e.actual_outcome
                    features["_pnl_myr"] = e.pnl_myr
                    features["_confidence"] = e.confidence
                    features["_timestamp"] = str(e.timestamp)
                    features["_model_version"] = e.model_version
                    rows.append(features)
                except json.JSONDecodeError:
                    continue
            
            return pd.DataFrame(rows)
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"[{coin_id}] Error getting training data: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────
# 4. Get ML Stats for API/Dashboard
# ─────────────────────────────────────────────
def get_ml_stats(coin_id: str) -> dict:
    """Get ML performance stats for a specific coin."""
    try:
        from database.ml_models import MLTrainingLog, ModelPerformance
        import shared
        
        session = _get_session()
        try:
            # Total predictions logged for this coin
            total_predictions = session.query(MLTrainingLog).filter(
                MLTrainingLog.coin_id == coin_id
            ).count()
            
            # Total trades with outcomes for this coin
            total_trades = session.query(MLTrainingLog).filter(
                MLTrainingLog.coin_id == coin_id,
                MLTrainingLog.actual_outcome.in_(["WIN", "LOSS"])
            ).count()
            
            # Recent win rate (last 50 trades for this coin)
            recent = (
                session.query(MLTrainingLog.actual_outcome)
                .filter(
                    MLTrainingLog.coin_id == coin_id,
                    MLTrainingLog.actual_outcome.in_(["WIN", "LOSS"])
                )
                .order_by(MLTrainingLog.timestamp.desc())
                .limit(50)
                .all()
            )
            
            wins = sum(1 for r in recent if r[0] == "WIN")
            recent_win_rate = (wins / len(recent)) if recent else 0.0
            
            # Active model info for this coin
            active_model = (
                session.query(ModelPerformance)
                .filter(
                    ModelPerformance.coin_id == coin_id,
                    ModelPerformance.is_active == True
                )
                .first()
            )
            
            # Get model version from shared state
            model_version = shared.engine_state.get(coin_id, {}).get("model_version", "v1")
            trades_since_retrain = shared.engine_state.get(coin_id, {}).get("trades_since_retrain", 0)
            adaptive_threshold = shared.engine_state.get(coin_id, {}).get("adaptive_threshold", 0.60)
            
            return {
                "coin_id": coin_id,
                "total_predictions": total_predictions,
                "total_trades": total_trades,
                "recent_win_rate": round(recent_win_rate * 100, 1),
                "model_version": model_version,
                "model_accuracy": active_model.accuracy if active_model else 0.0,
                "model_precision": active_model.precision_score if active_model else 0.0,
                "model_f1": active_model.f1_score if active_model else 0.0,
                "win_rate_live": active_model.win_rate_live * 100 if active_model else 0.0,
                "avg_pnl_per_trade": active_model.avg_pnl_per_trade if active_model else 0.0,
                "total_model_pnl": active_model.total_pnl if active_model else 0.0,
                "trades_since_retrain": trades_since_retrain,
                "adaptive_threshold": adaptive_threshold,
                "last_retrain": str(active_model.trained_at) if active_model else None
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"[{coin_id}] Error getting ML stats: {e}")
        return {
            "coin_id": coin_id,
            "total_predictions": 0,
            "total_trades": 0,
            "recent_win_rate": 0.0,
            "model_version": "v1",
            "error": str(e)
        }


# ─────────────────────────────────────────────
# 5. Update Model Performance After Retrain
# ─────────────────────────────────────────────
def update_model_performance(coin_id: str, model_version: str, metrics: dict):
    """
    Save new model's training metrics after retrain.
    Retires old model versions for this coin, activates new one.
    
    Args:
        coin_id: Coin symbol (this coin only)
        model_version: New version string (e.g. 'v3')
        metrics: Dict with keys: accuracy, precision, recall, f1, training_samples
    """
    try:
        from database.ml_models import ModelPerformance
        
        session = _get_session()
        try:
            # Retire ALL old active versions for THIS COIN only
            old_active = (
                session.query(ModelPerformance)
                .filter(
                    ModelPerformance.coin_id == coin_id,
                    ModelPerformance.is_active == True
                )
                .all()
            )
            for old in old_active:
                old.is_active = False
                old.retired_at = datetime.utcnow()
            
            # Create new performance entry for this coin
            new_perf = ModelPerformance(
                coin_id=coin_id,
                model_version=model_version,
                trained_at=datetime.utcnow(),
                training_samples=metrics.get("training_samples", 0),
                accuracy=metrics.get("accuracy", 0.0),
                precision_score=metrics.get("precision", 0.0),
                recall_score=metrics.get("recall", 0.0),
                f1_score=metrics.get("f1", 0.0),
                is_active=True
            )
            session.add(new_perf)
            session.commit()
            
            logger.info(
                f"[{coin_id}] ML PERF: Model {model_version} registered — "
                f"acc={metrics.get('accuracy', 0)*100:.1f}%, "
                f"prec={metrics.get('precision', 0)*100:.1f}%, "
                f"f1={metrics.get('f1', 0)*100:.1f}%, "
                f"samples={metrics.get('training_samples', 0)}"
            )
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"[{coin_id}] Error updating model performance: {e}")
