"""
strategy/decision_maker.py — Final decision engine
Combines signals + risk checks → Execute or skip
"""
from loguru import logger
from datetime import datetime, date
from sqlalchemy.orm import Session
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from strategy.signal_engine import Signal, signal_engine
from database.models import Trade, Portfolio, BotSettings, DailyLog


class DecisionMaker:
    """
    Buat keputusan final: execute trade atau tidak
    Checks: signal + risk limits + daily spend limit
    """

    def __init__(self, db: Session):
        self.db = db

    def get_daily_spent(self) -> float:
        """Berapa RM dah dibelanjakan hari ini"""
        today = date.today().isoformat()
        trades_today = self.db.query(Trade).filter(
            Trade.trade_type == "BUY",
            Trade.created_at >= datetime.combine(date.today(), datetime.min.time())
        ).all()
        return sum(t.amount_myr for t in trades_today)

    def get_portfolio(self) -> dict:
        """Latest portfolio snapshot"""
        snap = self.db.query(Portfolio).order_by(Portfolio.id.desc()).first()
        if snap:
            return {
                "btc": snap.btc_balance,
                "myr": snap.myr_balance,
                "total_value": snap.total_value,
                "pnl": snap.total_pnl
            }
        return {"btc": 0.0, "myr": settings.max_capital_myr, "total_value": settings.max_capital_myr, "pnl": 0.0}

    def get_avg_buy_price(self) -> float:
        """Harga purata beli BTC kita"""
        buys = self.db.query(Trade).filter(Trade.trade_type == "BUY", Trade.status == "COMPLETED").all()
        if not buys:
            return 0.0
        total_myr = sum(t.amount_myr for t in buys)
        total_btc = sum(t.amount_btc for t in buys)
        return total_myr / total_btc if total_btc > 0 else 0.0

    def can_buy(self, amount_myr: float) -> tuple[bool, str]:
        """
        Check sama ada boleh beli atau tidak
        Returns: (boleh_beli, sebab_tidak_boleh)
        """
        # Check bot enabled
        bot_settings = self.db.query(BotSettings).filter(BotSettings.id == 1).first()
        if bot_settings and not bot_settings.bot_enabled:
            return False, "Bot disabled by user"

        # Check daily spend limit
        daily_spent = self.get_daily_spent()
        daily_limit = bot_settings.daily_amount_myr if bot_settings else settings.daily_amount_myr
        if daily_spent + amount_myr > daily_limit * 1.5:  # Allow 1.5x for strong signals
            return False, f"Daily limit reached: dah belanja RM {daily_spent:.2f} hari ini"

        # Check total capital limit
        portfolio = self.get_portfolio()
        total_invested = settings.max_capital_myr - portfolio["myr"]
        if total_invested + amount_myr > settings.max_capital_myr:
            return False, f"Modal habis: sudah invest RM {total_invested:.2f} dari RM {settings.max_capital_myr:.2f}"

        # Check minimum MYR balance
        if portfolio["myr"] < amount_myr:
            return False, f"Baki tidak mencukupi: RM {portfolio['myr']:.2f} < RM {amount_myr:.2f}"

        return True, ""

    def can_sell(self, btc_amount: float) -> tuple[bool, str]:
        """Check sama ada boleh jual atau tidak"""
        portfolio = self.get_portfolio()
        if portfolio["btc"] < btc_amount:
            return False, f"BTC tidak mencukupi: {portfolio['btc']:.8f} < {btc_amount:.8f}"
        if portfolio["btc"] == 0:
            return False, "Tiada BTC dalam portfolio untuk dijual"
        return True, ""

    def decide(self, signal: Signal, real_balances: dict) -> dict:
        """
        Final decision berdasarkan signal + real balance dari Luno
        Returns decision dict
        """
        daily_amount = settings.daily_amount_myr
        portfolio = self.get_portfolio()

        result = {
            "action": "HOLD",
            "execute": False,
            "amount_myr": 0.0,
            "amount_btc": 0.0,
            "reason": signal.reason,
            "signal": signal,
            "blocked_reason": ""
        }

        if signal.action == "BUY":
            can_buy, blocked = self.can_buy(daily_amount)
            if can_buy:
                result.update({
                    "action": "BUY",
                    "execute": True,
                    "amount_myr": daily_amount,
                })
                logger.success(f"✅ DECISION: BUY RM{daily_amount:.2f} — {signal.reason}")
            else:
                result["blocked_reason"] = blocked
                logger.warning(f"⛔ BUY blocked: {blocked}")

        elif signal.action == "SELL":
            # Jual semua BTC yang ada
            btc_to_sell = real_balances.get("XBT", 0.0)
            if btc_to_sell > 0:
                can_sell, blocked = self.can_sell(btc_to_sell)
                if can_sell:
                    result.update({
                        "action": "SELL",
                        "execute": True,
                        "amount_btc": btc_to_sell,
                    })
                    logger.success(f"✅ DECISION: SELL {btc_to_sell:.8f} BTC — {signal.reason}")
                else:
                    result["blocked_reason"] = blocked
                    logger.warning(f"⛔ SELL blocked: {blocked}")
            else:
                result["blocked_reason"] = "Tiada BTC untuk dijual"

        else:
            logger.info(f"💤 DECISION: HOLD — {signal.reason}")

        return result

    def decide_rebalance(self, real_balances: dict, current_price: float) -> dict:
        """
        Fast 3-minute Rebalance Check:
        Beli RM 5 jika baki BTC jatuh RM 5 dari target.
        Jual RM 5 jika baki BTC naik RM 5 dari target.
        """
        bot_settings = self.db.query(BotSettings).filter(BotSettings.id == 1).first()
        if not bot_settings or not bot_settings.bot_enabled:
            return {"action": "HOLD", "execute": False, "reason": "Bot disabled"}

        target_base = bot_settings.target_baseline_myr
        margin = bot_settings.rebalance_margin_myr
        
        btc_balance = real_balances.get("XBT", 0.0)
        current_btc_value_myr = btc_balance * current_price

        result = {
            "action": "HOLD",
            "execute": False,
            "amount_myr": 0.0,
            "amount_btc": 0.0,
            "reason": f"BTC Value RM {current_btc_value_myr:.2f} within baseline RM {target_base:.2f}",
        }

        # Scenario 1: Naik (Take profit)
        if current_btc_value_myr >= target_base + margin:
            profit_to_take_myr = current_btc_value_myr - target_base
            btc_to_sell = profit_to_take_myr / current_price
            can_sell, blocked = self.can_sell(btc_to_sell)
            
            if can_sell:
                result.update({
                    "action": "SELL",
                    "execute": True,
                    "amount_btc": btc_to_sell,
                    "amount_myr": profit_to_take_myr,
                    "reason": f"Rebalance: Naik untung. Value RM {current_btc_value_myr:.2f} > RM {target_base:.2f}. Untung RM {profit_to_take_myr:.2f}"
                })
                logger.success(f"✅ REBALANCE DECISION: SELL RM {profit_to_take_myr:.2f} (Profit)")

        # Scenario 2: Turun (Buy the dip / Top up)
        elif current_btc_value_myr <= target_base - margin:
            dip_to_buy_myr = target_base - current_btc_value_myr
            can_buy, blocked = self.can_buy(dip_to_buy_myr)
            
            # Kita paksa limit kepada 'margin' jika nak DCA perlahan-lahan. 
            # Tapi arahan user: kalau 100 turun 95 awak topup 5 ringgit.
            if dip_to_buy_myr > margin * 2:
                # Elak topup gedabak kalau harga flash crash drastik (safety limit)
                dip_to_buy_myr = margin
                
            if can_buy:
                result.update({
                    "action": "BUY",
                    "execute": True,
                    "amount_myr": dip_to_buy_myr,
                    "reason": f"Rebalance: Harga diskaun. Value RM {current_btc_value_myr:.2f} < RM {target_base:.2f}. Beli RM {dip_to_buy_myr:.2f}"
                })
                logger.success(f"✅ REBALANCE DECISION: BUY RM {dip_to_buy_myr:.2f} (Top Up)")

        return result

    def log_daily_action(self, decision: dict, signal: Signal):
        """Log daily action ke database"""
        log = DailyLog(
            date=date.today().isoformat(),
            action=decision["action"],
            reason=signal.reason,
            btc_price=signal.current_price,
            price_change=signal.price_change_pct,
            rsi_value=signal.rsi,
            total_value=self.get_portfolio()["total_value"],
            pnl_myr=self.get_portfolio()["pnl"]
        )
        self.db.add(log)
        self.db.commit()
