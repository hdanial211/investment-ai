"""
scheduler/daily_job.py — APScheduler daily job
Runs at 08:00 AM every day to execute trading strategy
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from datetime import datetime, date
import pytz
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from database.models import get_db, Trade, Portfolio, BotSettings, GridState, SessionLocal
from exchange.luno_client import luno_client
from strategy.signal_engine import signal_engine
from strategy.decision_maker import DecisionMaker
from notifications.telegram_bot import telegram

# Malaysia timezone
KL_TZ = pytz.timezone("Asia/Kuala_Lumpur")


def run_daily_job():
    """
    Main daily job — runs at 08:00 AM KL time
    1. Fetch BTC price
    2. Calculate signals
    3. Make decision
    4. Execute trade
    5. Save to database
    6. Send Telegram notification
    """
    logger.info("=" * 60)
    logger.info(f"🤖 DAILY JOB STARTED — {datetime.now(KL_TZ).strftime('%d %b %Y, %I:%M %p KLT')}")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        # ─── 1. Fetch current price & balance ───────────────────────
        price_data = luno_client.get_btc_price()
        current_price = price_data["last_trade"]
        balances = luno_client.get_balances()

        # ─── 2. Get yesterday's price from DB (last trade) ──────────
        last_portfolio = db.query(Portfolio).order_by(Portfolio.id.desc()).first()
        prev_price = last_portfolio.btc_price if last_portfolio else current_price

        # ─── 3. Get price history for indicators ────────────────────
        # Try to get from Luno candles, fallback to DB prices
        price_history = []
        try:
            candles = luno_client.get_price_history(duration=3600)  # 1h candles
            price_history = [float(c.get("close", current_price)) for c in candles[-50:]]
        except Exception:
            # Fallback: use prices from DB
            past = db.query(Portfolio).order_by(Portfolio.id.desc()).limit(30).all()
            price_history = [p.btc_price for p in reversed(past)]

        # ─── 4. Generate signal ──────────────────────────────────────
        has_btc = balances["XBT"] > 0.000001  # meaningful BTC amount
        signal = signal_engine.generate_signal(
            current_price=current_price,
            prev_price=prev_price,
            price_history=price_history,
            has_btc=has_btc
        )

        # ─── 5. Make decision ────────────────────────────────────────
        decision_maker = DecisionMaker(db)
        decision = decision_maker.decide(signal, balances)

        # ─── 6. Execute trade ────────────────────────────────────────
        trade_result = None
        if decision["execute"]:
            if decision["action"] == "BUY":
                trade_result = luno_client.place_buy_order(decision["amount_myr"])
                # Save trade to DB
                trade = Trade(
                    trade_type="BUY",
                    amount_myr=trade_result["amount_myr"],
                    amount_btc=trade_result["amount_btc"],
                    price_myr=trade_result["price"],
                    signal=signal.reason[:200],
                    order_id=trade_result.get("order_id"),
                    status="COMPLETED"
                )
                db.add(trade)
                db.commit()
                # Telegram notification
                telegram.notify_buy(
                    amount_myr=trade_result["amount_myr"],
                    amount_btc=trade_result["amount_btc"],
                    price=trade_result["price"],
                    reason=signal.reason
                )

            elif decision["action"] == "SELL":
                trade_result = luno_client.place_sell_order(decision["amount_btc"])
                # Calculate P&L
                avg_cost = decision_maker.get_avg_buy_price()
                pnl = (trade_result["price"] - avg_cost) * decision["amount_btc"]
                # Save trade to DB
                trade = Trade(
                    trade_type="SELL",
                    amount_myr=trade_result["amount_myr"],
                    amount_btc=trade_result["amount_btc"],
                    price_myr=trade_result["price"],
                    signal=signal.reason[:200],
                    pnl_myr=pnl,
                    order_id=trade_result.get("order_id"),
                    status="COMPLETED"
                )
                db.add(trade)
                db.commit()
                # Telegram notification
                telegram.notify_sell(
                    amount_btc=trade_result["amount_btc"],
                    amount_myr=trade_result["amount_myr"],
                    price=trade_result["price"],
                    reason=signal.reason,
                    pnl=pnl
                )
        else:
            # HOLD
            telegram.notify_hold(
                price=current_price,
                price_change=signal.price_change_pct,
                rsi=signal.rsi,
                reason=signal.reason
            )

        # ─── 7. Update portfolio snapshot ───────────────────────────
        # Re-fetch balances after trade
        updated_balances = luno_client.get_balances()
        updated_price = luno_client.get_btc_price()["last_trade"]
        btc_value = updated_balances["XBT"] * updated_price
        total_value = btc_value + updated_balances["MYR"]
        initial_capital = settings.max_capital_myr
        pnl_total = total_value - initial_capital

        snapshot = Portfolio(
            btc_balance=updated_balances["XBT"],
            myr_balance=updated_balances["MYR"],
            btc_price=updated_price,
            total_value=total_value,
            total_pnl=pnl_total,
            pnl_pct=(pnl_total / initial_capital) * 100
        )
        db.add(snapshot)
        db.commit()

        # ─── 8. Log daily action ────────────────────────────────────
        decision_maker.log_daily_action(decision, signal)

        logger.success(f"""
✅ DAILY JOB COMPLETED
   Action: {decision['action']}
   BTC Price: RM {current_price:,.2f}
   Portfolio: RM {total_value:.2f} (P&L: RM {pnl_total:+.2f})
        """)

    except Exception as e:
        logger.error(f"❌ DAILY JOB ERROR: {e}")
        telegram.notify_error(str(e))
    finally:
        db.close()


import time as _time


def _execute_grid_trade(db, decision: dict, grid_state=None):
    """
    Helper: execute BUY or SELL based on decision dict, save to DB with fee tracking.
    Works for any pair via grid_state.
    """
    pair = decision.get("pair", "XBTMYR")

    if decision["action"] == "BUY":
        trade_result = luno_client.place_buy_order(decision["amount_myr"], pair=pair)
        fee_myr = 0.0
        if trade_result.get("order_id"):
            _time.sleep(1)
            try:
                order_info = luno_client.get_order_status(trade_result["order_id"])
                fee_myr = order_info.get("fee_myr", 0.0)
                logger.info(f"[{pair}] Fee BUY: RM {fee_myr:.4f}")
            except Exception:
                pass
        trade = Trade(
            pair=pair,
            trade_type="BUY",
            amount_myr=trade_result["amount_myr"],
            amount_btc=trade_result["amount_btc"],
            price_myr=trade_result["price"],
            fee_myr=fee_myr,
            signal=decision["reason"],
            order_id=trade_result.get("order_id"),
            status="COMPLETED"
        )
        db.add(trade)
        # Update base_price
        if decision.get("new_base_price"):
            if grid_state:
                grid_state.base_price_myr = decision["new_base_price"]
            else:
                bot_s = db.query(BotSettings).filter(BotSettings.id == 1).first()
                if bot_s:
                    bot_s.base_price_myr = decision["new_base_price"]
        db.commit()
        telegram.notify_buy(
            amount_myr=trade_result["amount_myr"],
            amount_btc=trade_result["amount_btc"],
            price=trade_result["price"],
            reason=decision["reason"]
        )

    elif decision["action"] == "SELL":
        trade_result = luno_client.place_sell_order(decision["amount_btc"], pair=pair)
        fee_myr = 0.0
        if trade_result.get("order_id"):
            _time.sleep(1)
            try:
                order_info = luno_client.get_order_status(trade_result["order_id"])
                fee_myr = order_info.get("fee_myr", 0.0)
                logger.info(f"[{pair}] Fee SELL: RM {fee_myr:.4f}")
            except Exception:
                pass
        pnl_after_fee = decision["amount_myr"] - fee_myr
        trade = Trade(
            pair=pair,
            trade_type="SELL",
            amount_myr=trade_result["amount_myr"],
            amount_btc=trade_result["amount_btc"],
            price_myr=trade_result["price"],
            fee_myr=fee_myr,
            signal=decision["reason"],
            pnl_myr=pnl_after_fee,
            order_id=trade_result.get("order_id"),
            status="COMPLETED"
        )
        db.add(trade)
        if decision.get("new_base_price"):
            if grid_state:
                grid_state.base_price_myr = decision["new_base_price"]
            else:
                bot_s = db.query(BotSettings).filter(BotSettings.id == 1).first()
                if bot_s:
                    bot_s.base_price_myr = decision["new_base_price"]
        db.commit()
        telegram.notify_sell(
            amount_btc=trade_result["amount_btc"],
            amount_myr=trade_result["amount_myr"],
            price=trade_result["price"],
            reason=decision["reason"],
            pnl=pnl_after_fee
        )


def run_rebalance_job():
    """
    Fast Rebalance Job — runs every 3 minutes.
    Loops through ALL enabled GridState pairs independently.
    """
    db = SessionLocal()
    try:
        balances = luno_client.get_balances()
        dm = DecisionMaker(db)

        # Ambil semua grid pairs yang aktif
        active_pairs = db.query(GridState).filter(GridState.enabled == True).all()

        if not active_pairs:
            logger.info("💤 No active pairs configured")
            return

        for gs in active_pairs:
            try:
                price_data  = luno_client.get_price(gs.pair)
                curr_price  = price_data["last_trade"]
                decision    = dm.decide_rebalance(balances, curr_price, grid_state=gs)

                if decision["execute"]:
                    logger.info("=" * 50)
                    logger.info(f"⚡ [{gs.pair}] GRID TRIGGERED — {datetime.now(KL_TZ).strftime('%H:%M:%S')}")
                    _execute_grid_trade(db, decision, grid_state=gs)
                else:
                    logger.info(f"💤 [{gs.pair}] {decision.get('reason', 'HOLD')}")

            except Exception as pair_err:
                logger.error(f"❌ [{gs.pair}] Error: {pair_err}")

    except Exception as e:
        logger.error(f"❌ REBALANCE JOB ERROR: {e}")
    finally:
        db.close()

def run_evening_summary():
    """Evening summary job — runs at 9:00 PM"""
    logger.info("📊 Running evening summary...")
    db = SessionLocal()
    try:
        snapshot = db.query(Portfolio).order_by(Portfolio.id.desc()).first()
        portfolio = {
            "btc": snapshot.btc_balance if snapshot else 0,
            "myr": snapshot.myr_balance if snapshot else settings.max_capital_myr,
            "total_value": snapshot.total_value if snapshot else settings.max_capital_myr,
            "pnl": snapshot.total_pnl if snapshot else 0
        }
        trades_today = db.query(Trade).filter(
            Trade.created_at >= datetime.combine(date.today(), datetime.min.time())
        ).all()
        next_run = f"Esok, {settings.schedule_time} pagi"
        telegram.notify_daily_summary(portfolio, trades_today, next_run)
    except Exception as e:
        logger.error(f"Evening summary error: {e}")
    finally:
        db.close()


class BotScheduler:
    """Manages the APScheduler instance"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=KL_TZ)
        self._setup_jobs()

    def _setup_jobs(self):
        """Setup all scheduled jobs"""
        # Parse schedule time
        hour, minute = settings.schedule_time.split(":")

        # Main daily trading job — 8:00 AM KL
        self.scheduler.add_job(
            func=run_daily_job,
            trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=KL_TZ),
            id="daily_trading_job",
            name="Daily Trading Job (8:00 AM)",
            replace_existing=True,
            misfire_grace_time=300  # 5 min grace period
        )
        logger.info(f"⏰ Trading job scheduled: every day at {settings.schedule_time} KLT")

        # Evening summary — 9:00 PM KL
        self.scheduler.add_job(
            func=run_evening_summary,
            trigger=CronTrigger(hour=21, minute=0, timezone=KL_TZ),
            id="evening_summary",
            name="Evening Summary (9:00 PM)",
            replace_existing=True
        )
        logger.info("📊 Evening summary scheduled: every day at 9:00 PM KLT")
        
        # Fast Rebalance — Every 3 Minutes
        self.scheduler.add_job(
            func=run_rebalance_job,
            trigger=IntervalTrigger(minutes=3, timezone=KL_TZ),
            id="fast_rebalance_job",
            name="Fast Rebalance (Every 3 Min)",
            replace_existing=True,
            misfire_grace_time=60
        )
        logger.info("⚡ Fast rebalance scheduled: every 3 minutes")

    def start(self):
        self.scheduler.start()
        logger.success("✅ Bot scheduler started!")

    def stop(self):
        self.scheduler.shutdown()
        logger.info("⏹️ Bot scheduler stopped")

    def trigger_now(self):
        """Manual trigger — run job immediately"""
        logger.info("🔥 Manual trigger — running daily job now...")
        run_daily_job()

    def get_next_run(self) -> str:
        """Get next scheduled run time"""
        job = self.scheduler.get_job("daily_trading_job")
        if job and job.next_run_time:
            daily_run = job.next_run_time.strftime("%d %b, %I:%M %p")
            return f"Setiap 3-minit (Rebalance) & Harian {daily_run}"
        return "N/A"


# Singleton
bot_scheduler = BotScheduler()
