"""
ml_adaptive.py — Adaptive Confidence Threshold Engine (Per-Coin)

Dynamically adjusts the confidence threshold for each coin based on
recent trade performance. Each coin learns independently.

Instead of hardcoded > 0.60 threshold:
- Good win rate → lower threshold (be more aggressive)
- Bad win rate → raise threshold (be more selective)
- Always deploy new model (continuous learning, no blocking)
"""
import logging
import time

logger = logging.getLogger(__name__)

# Threshold tiers based on recent win rate
THRESHOLD_TIERS = [
    # (min_win_rate, max_win_rate, threshold, label)
    (0.70, 1.00, 0.50, "Very Aggressive — model performing excellently"),
    (0.60, 0.70, 0.55, "Aggressive — model performing well"),
    (0.50, 0.60, 0.60, "Normal — model performing adequately"),
    (0.40, 0.50, 0.65, "Conservative — model needs improvement"),
    (0.30, 0.40, 0.70, "Selective — model struggling"),
    (0.00, 0.30, 0.80, "Very Selective — model needs retrain urgently"),
]

# Minimum trades before adjusting threshold (per coin)
MIN_TRADES_FOR_ADJUSTMENT = 15

# How many recent trades to consider for win rate
RECENT_TRADES_WINDOW = 40


def calculate_adaptive_threshold(coin_id: str, recent_outcomes: list) -> dict:
    """
    Calculate the adaptive confidence threshold for a specific coin.
    
    Args:
        coin_id: The coin symbol (BTC, ETH, SOL, XRP, LTC)
        recent_outcomes: List of recent trade outcomes ['WIN', 'LOSS', 'WIN', ...]
                        Most recent first.
    
    Returns:
        dict with:
            - threshold: float (new confidence threshold)
            - win_rate: float (calculated win rate)
            - label: str (human-readable tier description)
            - sample_size: int (number of trades used)
            - adjusted: bool (whether threshold was changed from default)
    """
    default_result = {
        "threshold": 0.60,
        "win_rate": 0.0,
        "label": "Default — insufficient data for adjustment",
        "sample_size": len(recent_outcomes),
        "adjusted": False
    }
    
    if len(recent_outcomes) < MIN_TRADES_FOR_ADJUSTMENT:
        logger.info(
            f"[{coin_id}] Adaptive threshold: Not enough trades "
            f"({len(recent_outcomes)}/{MIN_TRADES_FOR_ADJUSTMENT}). "
            f"Using default 0.60."
        )
        return default_result
    
    # Use only the most recent trades (EWMA-like weighting via recency)
    window = recent_outcomes[:RECENT_TRADES_WINDOW]
    
    # Calculate win rate with exponential weighting (recent trades matter more)
    total_weight = 0.0
    weighted_wins = 0.0
    decay = 0.95  # Each older trade is worth 5% less
    
    for i, outcome in enumerate(window):
        weight = decay ** i
        total_weight += weight
        if outcome == "WIN":
            weighted_wins += weight
    
    win_rate = weighted_wins / total_weight if total_weight > 0 else 0.0
    
    # Find matching threshold tier
    threshold = 0.60
    label = "Normal"
    for min_wr, max_wr, thresh, tier_label in THRESHOLD_TIERS:
        if min_wr <= win_rate < max_wr:
            threshold = thresh
            label = tier_label
            break
    
    result = {
        "threshold": threshold,
        "win_rate": round(win_rate, 4),
        "label": label,
        "sample_size": len(window),
        "adjusted": True
    }
    
    logger.info(
        f"[{coin_id}] Adaptive threshold: win_rate={win_rate*100:.1f}% "
        f"(from {len(window)} trades) → threshold={threshold} ({label})"
    )
    
    return result


def recalculate_threshold_for_coin(coin_id: str) -> float:
    """
    Recalculate and update the adaptive threshold for a specific coin.
    Reads recent trade outcomes from the ML training log database.
    
    Returns the new threshold value.
    """
    try:
        from database.ml_models import MLTrainingLog
        from database.models import SessionLocal
        
        session = SessionLocal()
        try:
            # Fetch recent completed trades for this coin only
            recent_trades = (
                session.query(MLTrainingLog.actual_outcome)
                .filter(
                    MLTrainingLog.coin_id == coin_id,
                    MLTrainingLog.actual_outcome.in_(["WIN", "LOSS"]),
                    MLTrainingLog.predicted_signal == 1
                )
                .order_by(MLTrainingLog.timestamp.desc())
                .limit(RECENT_TRADES_WINDOW)
                .all()
            )
            
            outcomes = [row[0] for row in recent_trades]
            result = calculate_adaptive_threshold(coin_id, outcomes)
            
            # Update shared state for this coin
            import shared
            if coin_id in shared.engine_state:
                shared.engine_state[coin_id]["adaptive_threshold"] = result["threshold"]
                shared.engine_state[coin_id]["ml_stats"] = shared.engine_state[coin_id].get("ml_stats", {})
                shared.engine_state[coin_id]["ml_stats"]["recent_win_rate"] = result["win_rate"]
                shared.engine_state[coin_id]["ml_stats"]["threshold_label"] = result["label"]
                shared.engine_state[coin_id]["ml_stats"]["threshold_sample_size"] = result["sample_size"]
                shared.save_state()
            
            return result["threshold"]
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"[{coin_id}] Error recalculating adaptive threshold: {e}")
        return 0.60  # Safe fallback


def recalculate_all_thresholds():
    """Recalculate adaptive thresholds for all 5 coins."""
    coins = ["BTC", "ETH", "SOL", "XRP", "LTC"]
    results = {}
    for coin_id in coins:
        threshold = recalculate_threshold_for_coin(coin_id)
        results[coin_id] = threshold
    return results
