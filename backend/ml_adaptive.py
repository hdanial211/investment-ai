"""
ml_adaptive.py — Adaptive Confidence Threshold Engine (Per-Coin)

Dynamically adjusts the confidence threshold for each coin based on
recent trade performance. Each coin learns independently.

v5.7.0: Now uses COMPOSITE score (win rate + expectancy) instead of
        pure win rate. This prevents high-WR but negative-profit scenarios
        (e.g. BTC 84.6% WR but losing money because wins are tiny).

NOTE: Threshold HANYA adjust berapa confident model perlu sebelum signal.
      BUKAN untuk pause/stop trading — hanya user yang boleh toggle on/off.
"""
import logging
import time

logger = logging.getLogger(__name__)

# ─── Threshold Tiers based on composite score ───
# Composite = (win_rate * 0.6) + (expectancy_score * 0.4)
# expectancy_score: 1.0 jika expectancy > +0.10, 0.0 jika < -0.10
THRESHOLD_TIERS = [
    # (min_score, max_score, threshold, label)
    (0.70, 1.00, 0.50, "Very Aggressive — profitable & consistent signals"),
    (0.60, 0.70, 0.55, "Aggressive — good signal quality"),
    (0.50, 0.60, 0.60, "Normal — adequate signal quality"),
    (0.40, 0.50, 0.65, "Conservative — signals need improvement"),
    (0.30, 0.40, 0.70, "Selective — signals inconsistent"),
    (0.00, 0.30, 0.80, "Very Selective — low confidence in signals"),
]

# Minimum trades before adjusting threshold (per coin)
MIN_TRADES_FOR_ADJUSTMENT = 15

# How many recent trades to consider
RECENT_TRADES_WINDOW = 40


def _calculate_expectancy_score(avg_win: float, avg_loss: float, win_rate: float) -> float:
    """
    Convert raw expectancy (RM per trade) to a 0-1 score.
    
    Expectancy = (WR × avg_win) - (LR × abs(avg_loss))
    Score mapping: < -0.10 → 0.0, > +0.10 → 1.0, linear between
    """
    loss_rate = 1.0 - win_rate
    expectancy = (win_rate * avg_win) - (loss_rate * abs(avg_loss))
    
    # Map to 0-1 score: -0.10 → 0.0, +0.10 → 1.0
    score = (expectancy + 0.10) / 0.20  # Linear mapping
    return max(0.0, min(1.0, score))


def calculate_adaptive_threshold(coin_id: str, recent_outcomes: list,
                                  pnl_list: list = None) -> dict:
    """
    Calculate the adaptive confidence threshold for a specific coin.
    
    Args:
        coin_id: The coin symbol (BTC, ETH, SOL, XRP, LTC)
        recent_outcomes: List of recent trade outcomes ['WIN', 'LOSS', ...]
                        Most recent first.
        pnl_list: List of PnL values matching outcomes (for expectancy calc)
    
    Returns:
        dict with threshold, win_rate, expectancy, composite_score, label, etc.
    """
    default_result = {
        "threshold": 0.60,
        "win_rate": 0.0,
        "expectancy": 0.0,
        "composite_score": 0.0,
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
    
    # Use only the most recent trades
    window = recent_outcomes[:RECENT_TRADES_WINDOW]
    pnl_window = (pnl_list[:RECENT_TRADES_WINDOW] if pnl_list 
                  else [0.0] * len(window))
    
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
    
    # Calculate expectancy from PnL data
    wins_pnl = [p for o, p in zip(window, pnl_window) if o == "WIN" and p != 0]
    losses_pnl = [p for o, p in zip(window, pnl_window) if o == "LOSS" and p != 0]
    
    avg_win = sum(wins_pnl) / len(wins_pnl) if wins_pnl else 0.0
    avg_loss = sum(losses_pnl) / len(losses_pnl) if losses_pnl else 0.0
    
    # ★ Composite Score = WR (60%) + Expectancy Score (40%)
    expectancy_score = _calculate_expectancy_score(avg_win, abs(avg_loss), win_rate)
    composite_score = (win_rate * 0.6) + (expectancy_score * 0.4)
    
    raw_expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
    
    # Find matching threshold tier using composite score
    threshold = 0.60
    label = "Normal"
    for min_s, max_s, thresh, tier_label in THRESHOLD_TIERS:
        if min_s <= composite_score < max_s:
            threshold = thresh
            label = tier_label
            break
    
    result = {
        "threshold": threshold,
        "win_rate": round(win_rate, 4),
        "expectancy": round(raw_expectancy, 4),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "expectancy_score": round(expectancy_score, 4),
        "composite_score": round(composite_score, 4),
        "label": label,
        "sample_size": len(window),
        "adjusted": True
    }
    
    logger.info(
        f"[{coin_id}] Adaptive threshold: WR={win_rate*100:.1f}% | "
        f"Exp=RM{raw_expectancy:.4f}/trade | "
        f"Composite={composite_score:.2f} → threshold={threshold} ({label})"
    )
    
    return result


def recalculate_threshold_for_coin(coin_id: str) -> float:
    """
    Recalculate and update the adaptive threshold for a specific coin.
    Reads recent trade outcomes + PnL from the ML training log database.
    
    Returns the new threshold value.
    """
    try:
        from database.ml_models import MLTrainingLog
        from database.models import SessionLocal
        
        session = SessionLocal()
        try:
            # Fetch recent completed trades with PnL for this coin
            recent_trades = (
                session.query(MLTrainingLog.actual_outcome, MLTrainingLog.pnl_myr)
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
            pnl_list = [float(row[1]) if row[1] else 0.0 for row in recent_trades]
            
            result = calculate_adaptive_threshold(coin_id, outcomes, pnl_list)
            
            # Update shared state for this coin
            import shared
            if coin_id in shared.engine_state:
                shared.engine_state[coin_id]["adaptive_threshold"] = result["threshold"]
                ml_stats = shared.engine_state[coin_id].get("ml_stats", {})
                ml_stats["recent_win_rate"] = result["win_rate"]
                ml_stats["expectancy"] = result["expectancy"]
                ml_stats["avg_win"] = result.get("avg_win", 0)
                ml_stats["avg_loss"] = result.get("avg_loss", 0)
                ml_stats["composite_score"] = result["composite_score"]
                ml_stats["threshold_label"] = result["label"]
                ml_stats["threshold_sample_size"] = result["sample_size"]
                shared.engine_state[coin_id]["ml_stats"] = ml_stats
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
