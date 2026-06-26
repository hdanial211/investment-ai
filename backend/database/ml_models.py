"""
database/ml_models.py — SQLAlchemy models for Adaptive Learning Pipeline

Two tables:
  1. MLTrainingLog   — every AI prediction + eventual trade outcome (per coin)
  2. ModelPerformance — model version training metrics + live stats (per coin)

Shares Base / engine / SessionLocal from models.py so everything lives in the
same SQLite database.
"""

import logging
from datetime import datetime

from sqlalchemy import (
    Column, Integer, Float, String, Boolean, DateTime, Text, Index,
)

from database.models import Base, engine, SessionLocal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Table 1: MLTrainingLog
# ---------------------------------------------------------------------------
class MLTrainingLog(Base):
    """Records EVERY AI prediction + eventual trade outcome for ML feedback."""

    __tablename__ = "ml_training_log"

    id               = Column(Integer, primary_key=True, index=True)
    coin_id          = Column(String, nullable=False, index=True)          # BTC / ETH / SOL / XRP / LTC
    timestamp        = Column(DateTime, default=datetime.utcnow)

    # --- feature snapshot at prediction time ---
    features_json    = Column(Text, nullable=True)                         # JSON-serialised feature vector

    # --- model prediction ---
    confidence       = Column(Float, default=0.0)                          # XGBoost probability 0.0–1.0
    predicted_signal = Column(Integer, default=0)                          # 1 = Golden Entry triggered, 0 = No Entry

    # --- actual trade outcome (filled later when trade completes) ---
    actual_outcome   = Column(String, nullable=True)                       # WIN / LOSS / TIMEOUT / PENDING / null
    entry_price      = Column(Float, nullable=True)
    exit_price       = Column(Float, nullable=True)
    pnl_myr          = Column(Float, default=0.0)
    pnl_pct          = Column(Float, default=0.0)
    hold_duration_min = Column(Integer, default=0)
    layers_used      = Column(Integer, default=0)
    fee_total_myr    = Column(Float, default=0.0)

    # --- model metadata ---
    model_version    = Column(String, nullable=False, default="v1")        # e.g. 'v1', 'v2'
    trade_cycle_id   = Column(String, nullable=True)                       # links prediction → trade cycle

    __table_args__ = (
        Index("ix_ml_log_coin_ts", "coin_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<MLTrainingLog id={self.id} coin={self.coin_id} "
            f"signal={self.predicted_signal} outcome={self.actual_outcome}>"
        )


# ---------------------------------------------------------------------------
# Table 2: ModelPerformance
# ---------------------------------------------------------------------------
class ModelPerformance(Base):
    """Tracks each model version's training metrics + live performance PER COIN."""

    __tablename__ = "model_performance"

    id               = Column(Integer, primary_key=True, index=True)
    coin_id          = Column(String, nullable=False, index=True)          # BTC / ETH / SOL / XRP / LTC
    model_version    = Column(String, nullable=False)                      # e.g. 'v1', 'v2'

    # --- training-time metrics ---
    trained_at       = Column(DateTime, default=datetime.utcnow)
    training_samples = Column(Integer, default=0)
    accuracy         = Column(Float, default=0.0)
    precision_score  = Column(Float, default=0.0)                          # precision for class-1 (Golden Entry)
    recall_score     = Column(Float, default=0.0)
    f1_score         = Column(Float, default=0.0)

    # --- live performance (updated as trades complete) ---
    win_rate_live    = Column(Float, default=0.0)
    avg_pnl_per_trade = Column(Float, default=0.0)
    total_trades     = Column(Integer, default=0)
    total_pnl        = Column(Float, default=0.0)

    # --- lifecycle ---
    is_active        = Column(Boolean, default=False)
    retired_at       = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_perf_coin_version", "coin_id", "model_version"),
    )

    def __repr__(self) -> str:
        return (
            f"<ModelPerformance id={self.id} coin={self.coin_id} "
            f"version={self.model_version} active={self.is_active}>"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def create_ml_tables() -> None:
    """Create ONLY the ML tables (does not touch existing tables)."""
    MLTrainingLog.__table__.create(bind=engine, checkfirst=True)
    ModelPerformance.__table__.create(bind=engine, checkfirst=True)
    logger.info("✅ ML tables created (ml_training_log, model_performance)")


def get_ml_db():
    """Yield a SQLAlchemy session for ML tables (same DB as main app)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
