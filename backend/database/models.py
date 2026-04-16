"""
database/models.py — SQLAlchemy database models
"""
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Trade(Base):
    __tablename__ = "trades"

    id          = Column(Integer, primary_key=True, index=True)
    pair        = Column(String, default="XBTMYR", nullable=False)  # e.g. XBTMYR, ETHMYR, XRPMYR
    trade_type  = Column(String, nullable=False)      # BUY / SELL
    amount_myr  = Column(Float, nullable=False)        # RM yang digunakan
    amount_btc  = Column(Float, nullable=False)        # Crypto yang dibeli/dijual (kolum lama kekal)
    price_myr   = Column(Float, nullable=False)        # Harga crypto masa tu
    fee_myr     = Column(Float, default=0.0)           # Fee Luno (MYR) — deducted from P&L
    signal      = Column(String, nullable=True)        # RSI_OVERSOLD / GRID_BUY / GRID_SELL
    pnl_myr     = Column(Float, default=0.0)           # Profit/Loss selepas fee (untuk SELL)
    status      = Column(String, default="COMPLETED")  # COMPLETED / FAILED / PENDING
    order_id    = Column(String, nullable=True)        # Luno order ID
    created_at  = Column(DateTime, default=datetime.utcnow)


class GridState(Base):
    """Satu baris per pasangan crypto — simpan state grid untuk setiap pair"""
    __tablename__ = "grid_states"
    __table_args__ = (UniqueConstraint("pair", name="uq_grid_pair"),)

    id                = Column(Integer, primary_key=True, index=True)
    pair              = Column(String, nullable=False, unique=True)  # e.g. XBTMYR
    display_name      = Column(String, nullable=False)               # e.g. Bitcoin (BTC)
    base_currency     = Column(String, nullable=False)               # e.g. XBT, ETH, XRP
    enabled           = Column(Boolean, default=True)
    base_price_myr    = Column(Float, default=0.0)       # Harga rujukan grid (0 = auto-detect)
    rebalance_margin_pct = Column(Float, default=2.5)    # % naik/turun untuk trigger
    trade_size_myr    = Column(Float, default=35.0)      # RM per trade
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Portfolio(Base):
    __tablename__ = "portfolio_snapshots"

    id           = Column(Integer, primary_key=True, index=True)
    btc_balance  = Column(Float, default=0.0)
    myr_balance  = Column(Float, default=0.0)
    btc_price    = Column(Float, default=0.0)
    total_value  = Column(Float, default=0.0)    # btc_balance * btc_price + myr_balance
    total_pnl    = Column(Float, default=0.0)
    pnl_pct      = Column(Float, default=0.0)
    snapshot_at  = Column(DateTime, default=datetime.utcnow)


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id                = Column(Integer, primary_key=True, default=1)
    daily_amount_myr  = Column(Float, default=5.0)
    buy_threshold_pct = Column(Float, default=1.5)
    sell_threshold_pct= Column(Float, default=2.0)
    rsi_oversold      = Column(Integer, default=30)
    rsi_overbought    = Column(Integer, default=70)
    schedule_time     = Column(String, default="08:00")
    max_capital_myr   = Column(Float, default=100.0)
    bot_enabled       = Column(Boolean, default=True)

    # Legacy Grid Trading (XBTMYR only — migrated to GridState)
    target_baseline_myr  = Column(Float, default=100.0)
    rebalance_margin_pct = Column(Float, default=2.5)
    base_price_myr       = Column(Float, default=0.0)
    trade_size_myr       = Column(Float, default=35.0)

    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id           = Column(Integer, primary_key=True, index=True)
    date         = Column(String, nullable=False)    # YYYY-MM-DD
    action       = Column(String, nullable=False)    # BUY / SELL / HOLD
    reason       = Column(String, nullable=True)
    btc_price    = Column(Float)
    price_change = Column(Float)
    rsi_value    = Column(Float)
    total_value  = Column(Float)
    pnl_myr      = Column(Float)
    created_at   = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
