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
    pair        = Column(String, nullable=False)  # e.g. BTC_MYR, ETH_MYR
    trade_type  = Column(String, nullable=False)      # BUY / SELL
    amount_myr  = Column(Float, nullable=False)        # RM yang digunakan
    amount_btc  = Column(Float, nullable=False)        # Crypto yang dibeli/dijual
    price_myr   = Column(Float, nullable=False)        # Harga crypto masa tu
    fee_myr     = Column(Float, default=0.0)           # Fee (MYR) — deducted from P&L
    signal      = Column(String, nullable=True)        # AI_BUY / DCA_BUY / TAKE_PROFIT
    pnl_myr     = Column(Float, default=0.0)           # Profit/Loss selepas fee (untuk SELL)
    status      = Column(String, default="COMPLETED")  # COMPLETED / FAILED / PENDING
    order_id    = Column(String, nullable=True)        # Exchange order ID
    created_at  = Column(DateTime, default=datetime.utcnow)


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


class DCALog(Base):
    __tablename__ = "dca_logs"

    id          = Column(Integer, primary_key=True, index=True)
    pair        = Column(String, index=True, nullable=False)
    layer       = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    amount_fiat = Column(Float, nullable=False)
    status      = Column(String, default="OPEN") # OPEN, CLOSED
    created_at  = Column(DateTime, default=datetime.utcnow)


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id          = Column(Integer, primary_key=True, index=True)
    pair        = Column(String, unique=True, index=True, nullable=False)
    is_auto     = Column(Boolean, default=False)
    trade_size_fiat = Column(Float, default=50.0)
    take_profit_pct = Column(Float, default=0.006)
    max_layers  = Column(Integer, default=10)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)
    # Also create ML tables
    try:
        from database.ml_models import create_ml_tables
        create_ml_tables()
    except Exception:
        pass  # ML tables will be created by live_engine on startup


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
