"""
main.py — FastAPI backend server
REST API for dashboard + bot control
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta
from loguru import logger
import sys, os

from config import settings
from database.models import create_tables, get_db, Trade, Portfolio, BotSettings, DailyLog
from exchange.luno_client import luno_client
from strategy.signal_engine import signal_engine
from scheduler.daily_job import bot_scheduler
from notifications.telegram_bot import telegram

# ─── App Setup ──────────────────────────────────────────────────────
app = FastAPI(
    title="Bitcoin Investment AI",
    description="Auto-invest Bitcoin setiap hari — Luno Malaysia",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Pydantic Schemas ────────────────────────────────────────────────
class SettingsUpdate(BaseModel):
    daily_amount_myr: Optional[float] = None
    buy_threshold_pct: Optional[float] = None
    sell_threshold_pct: Optional[float] = None
    rsi_oversold: Optional[int] = None
    rsi_overbought: Optional[int] = None
    schedule_time: Optional[str] = None
    max_capital_myr: Optional[float] = None
    bot_enabled: Optional[bool] = None


# ─── Startup / Shutdown ──────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Bitcoin Investment AI...")
    create_tables()
    # Init default settings if not exists
    db = next(get_db())
    if not db.query(BotSettings).filter(BotSettings.id == 1).first():
        default_settings = BotSettings(
            id=1,
            daily_amount_myr=settings.daily_amount_myr,
            buy_threshold_pct=settings.buy_threshold_pct,
            sell_threshold_pct=settings.sell_threshold_pct,
            rsi_oversold=settings.rsi_oversold,
            rsi_overbought=settings.rsi_overbought,
            schedule_time=settings.schedule_time,
            max_capital_myr=settings.max_capital_myr,
            bot_enabled=settings.bot_enabled
        )
        db.add(default_settings)
        db.commit()
    bot_scheduler.start()
    telegram.notify_startup()
    logger.success("✅ Investment AI ready!")


@app.on_event("shutdown")
async def shutdown_event():
    bot_scheduler.stop()
    logger.info("Bot scheduler stopped")


# ─── API Endpoints ───────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "running", "name": "Bitcoin Investment AI", "version": "1.0.0"}


@app.get("/api/status")
def get_status(db: Session = Depends(get_db)):
    """Get bot status & next run time"""
    bot_settings = db.query(BotSettings).filter(BotSettings.id == 1).first()
    return {
        "bot_enabled": bot_settings.bot_enabled if bot_settings else True,
        "next_run": bot_scheduler.get_next_run(),
        "schedule_time": bot_settings.schedule_time if bot_settings else settings.schedule_time,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/price")
def get_current_price():
    """Get live BTC/MYR price from Luno"""
    try:
        price = luno_client.get_btc_price()
        return {"success": True, "data": price}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/balance")
def get_balance():
    """Get account balances from Luno"""
    try:
        balances = luno_client.get_balances()
        return {"success": True, "data": balances}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    """Get latest portfolio snapshot"""
    snapshot = db.query(Portfolio).order_by(Portfolio.id.desc()).first()
    if not snapshot:
        return {
            "btc_balance": 0.0,
            "myr_balance": settings.max_capital_myr,
            "btc_price": 0.0,
            "total_value": settings.max_capital_myr,
            "total_pnl": 0.0,
            "pnl_pct": 0.0
        }
    return {
        "btc_balance": snapshot.btc_balance,
        "myr_balance": snapshot.myr_balance,
        "btc_price": snapshot.btc_price,
        "total_value": snapshot.total_value,
        "total_pnl": snapshot.total_pnl,
        "pnl_pct": snapshot.pnl_pct,
        "updated_at": snapshot.snapshot_at.isoformat()
    }


@app.get("/api/portfolio/history")
def get_portfolio_history(days: int = 30, db: Session = Depends(get_db)):
    """Portfolio value history for chart"""
    since = datetime.now() - timedelta(days=days)
    snapshots = db.query(Portfolio).filter(
        Portfolio.snapshot_at >= since
    ).order_by(Portfolio.snapshot_at.asc()).all()
    return [{
        "date": s.snapshot_at.isoformat(),
        "total_value": s.total_value,
        "btc_price": s.btc_price,
        "pnl": s.total_pnl,
        "pnl_pct": s.pnl_pct
    } for s in snapshots]


@app.get("/api/trades")
def get_trades(limit: int = 50, trade_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Get trade history"""
    query = db.query(Trade).order_by(Trade.created_at.desc())
    if trade_type:
        query = query.filter(Trade.trade_type == trade_type.upper())
    trades = query.limit(limit).all()
    return [{
        "id": t.id,
        "type": t.trade_type,
        "amount_myr": t.amount_myr,
        "amount_btc": t.amount_btc,
        "price_myr": t.price_myr,
        "pnl_myr": t.pnl_myr,
        "signal": t.signal,
        "status": t.status,
        "order_id": t.order_id,
        "created_at": t.created_at.isoformat()
    } for t in trades]


@app.get("/api/trades/stats")
def get_trade_stats(db: Session = Depends(get_db)):
    """Trading statistics"""
    all_trades = db.query(Trade).all()
    buys = [t for t in all_trades if t.trade_type == "BUY"]
    sells = [t for t in all_trades if t.trade_type == "SELL"]
    total_invested = sum(t.amount_myr for t in buys)
    total_returned = sum(t.amount_myr for t in sells)
    total_pnl = sum(t.pnl_myr for t in sells)
    return {
        "total_trades": len(all_trades),
        "total_buys": len(buys),
        "total_sells": len(sells),
        "total_invested_myr": total_invested,
        "total_returned_myr": total_returned,
        "total_pnl_myr": total_pnl,
        "win_rate": (len([t for t in sells if t.pnl_myr > 0]) / len(sells) * 100) if sells else 0
    }


@app.get("/api/signal")
def get_current_signal(db: Session = Depends(get_db)):
    """Get current market signal without executing"""
    try:
        price_data = luno_client.get_btc_price()
        current_price = price_data["last_trade"]
        balances = luno_client.get_balances()

        last = db.query(Portfolio).order_by(Portfolio.id.desc()).first()
        prev_price = last.btc_price if last else current_price

        signal = signal_engine.generate_signal(
            current_price=current_price,
            prev_price=prev_price,
            has_btc=balances["XBT"] > 0.000001
        )
        return {
            "action": signal.action,
            "reason": signal.reason,
            "confidence": signal.confidence,
            "current_price": signal.current_price,
            "price_change_pct": signal.price_change_pct,
            "rsi": signal.rsi,
            "ema_20": signal.ema_20,
            "timestamp": signal.timestamp.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs")
def get_daily_logs(days: int = 30, db: Session = Depends(get_db)):
    """Get daily action logs"""
    logs = db.query(DailyLog).order_by(DailyLog.created_at.desc()).limit(days).all()
    return [{
        "date": l.date,
        "action": l.action,
        "reason": l.reason,
        "btc_price": l.btc_price,
        "price_change": l.price_change,
        "rsi_value": l.rsi_value,
        "total_value": l.total_value,
        "pnl_myr": l.pnl_myr,
        "created_at": l.created_at.isoformat()
    } for l in logs]


@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    """Get current bot settings"""
    s = db.query(BotSettings).filter(BotSettings.id == 1).first()
    if not s:
        return settings.model_dump()
    return {
        "daily_amount_myr": s.daily_amount_myr,
        "buy_threshold_pct": s.buy_threshold_pct,
        "sell_threshold_pct": s.sell_threshold_pct,
        "rsi_oversold": s.rsi_oversold,
        "rsi_overbought": s.rsi_overbought,
        "schedule_time": s.schedule_time,
        "max_capital_myr": s.max_capital_myr,
        "bot_enabled": s.bot_enabled
    }


@app.put("/api/settings")
def update_settings(update: SettingsUpdate, db: Session = Depends(get_db)):
    """Update bot settings"""
    s = db.query(BotSettings).filter(BotSettings.id == 1).first()
    if not s:
        raise HTTPException(status_code=404, detail="Settings not found")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    s.updated_at = datetime.now()
    db.commit()
    logger.info(f"⚙️ Settings updated: {update.model_dump(exclude_none=True)}")
    return {"success": True, "message": "Settings updated"}


@app.post("/api/bot/toggle")
def toggle_bot(db: Session = Depends(get_db)):
    """Toggle bot ON/OFF"""
    s = db.query(BotSettings).filter(BotSettings.id == 1).first()
    if s:
        s.bot_enabled = not s.bot_enabled
        db.commit()
        status = "ENABLED" if s.bot_enabled else "DISABLED"
        logger.info(f"🤖 Bot {status}")
        return {"success": True, "bot_enabled": s.bot_enabled, "status": status}
    raise HTTPException(status_code=404, detail="Settings not found")


@app.post("/api/bot/trigger")
def manual_trigger(background_tasks: BackgroundTasks):
    """Manual trigger — run trading job immediately"""
    logger.info("🔥 Manual trigger from API")
    background_tasks.add_task(bot_scheduler.trigger_now)
    return {"success": True, "message": "Trading job triggered — running in background"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.backend_port, reload=True)
