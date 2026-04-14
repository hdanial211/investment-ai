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

    def can_buy(self, amount_myr: float, live_myr: float = None) -> tuple[bool, str]:
        """
        Check sama ada boleh beli atau tidak
        Returns: (boleh_beli, sebab_tidak_boleh)
        """
        # Check bot enabled
        bot_settings = self.db.query(BotSettings).filter(BotSettings.id == 1).first()
        if bot_settings and not bot_settings.bot_enabled:
            return False, "Bot disabled by user"


        portfolio = self.get_portfolio()
        current_myr = live_myr if live_myr is not None else portfolio["myr"]
        total_invested = settings.max_capital_myr - current_myr
        
        if total_invested + amount_myr > settings.max_capital_myr:
            return False, f"Modal habis: sudah invest RM {total_invested:.2f} dari RM {settings.max_capital_myr:.2f}"

        # Check minimum MYR balance
        if current_myr < amount_myr:
            return False, f"Baki tunai (MYR) tidak mencukupi: RM {current_myr:.2f} < RM {amount_myr:.2f}"

        return True, ""

    def can_sell(self, btc_amount: float, live_btc: float = None) -> tuple[bool, str]:
        """Check sama ada boleh jual atau tidak"""
        # Gunakan live balance dari Luno jika ada, fallback ke DB snapshot
        btc_held = live_btc if live_btc is not None else self.get_portfolio()["btc"]
        if btc_held == 0:
            return False, "Tiada BTC dalam portfolio untuk dijual"
        if btc_held < btc_amount:
            return False, f"BTC tidak mencukupi: {btc_held:.8f} < {btc_amount:.8f}"
        return True, ""

    def decide(self, signal: Signal, real_balances: dict) -> dict:
        """
        Final decision berdasarkan signal Momentum Harian + real balance dari Luno
        Returns decision dict
        """
        bot_settings = self.db.query(BotSettings).filter(BotSettings.id == 1).first()
        trade_amount = bot_settings.trade_size_myr if bot_settings else 30.0

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
            can_buy, blocked = self.can_buy(trade_amount)
            if can_buy:
                result.update({
                    "action": "BUY",
                    "execute": True,
                    "amount_myr": trade_amount,
                })
                logger.success(f"✅ 8AM DECISION: BUY RM {trade_amount:.2f} — {signal.reason}")
            else:
                result["blocked_reason"] = blocked
                logger.warning(f"⛔ BUY blocked: {blocked}")

        elif signal.action == "SELL":
            # Jual sebahagian BTC bersamaan nilai Trade Amount (RM 30)
            btc_to_sell = trade_amount / signal.current_price
            
            # Semak jika BTC cukup untuk mengelakkan ralat
            can_sell, blocked = self.can_sell(btc_to_sell)
            if can_sell:
                result.update({
                    "action": "SELL",
                    "execute": True,
                    "amount_btc": btc_to_sell,
                    "amount_myr": trade_amount
                })
                logger.success(f"✅ 8AM DECISION: SELL RM {trade_amount:.2f} — {signal.reason}")
            else:
                result["blocked_reason"] = blocked
                logger.warning(f"⛔ SELL blocked: {blocked}")
        else:
            logger.info(f"💤 8AM DECISION: HOLD — {signal.reason}")

        return result

    def decide_rebalance(self, real_balances: dict, current_price: float) -> dict:
        """
        Fast 3-minute Rebalance (Price-Step Grid):
        Tracks actual BTC price changes independently of user's MYR/BTC equity to bypass
        small portfolio constraints while avoiding Luno Minimum Trade Volume blocks.
        """
        bot_settings = self.db.query(BotSettings).filter(BotSettings.id == 1).first()
        if not bot_settings or not bot_settings.bot_enabled:
            return {"action": "HOLD", "execute": False, "reason": "Bot disabled"}

        # Initialize Base Price from last actual trade, NOT current market price
        if not bot_settings.base_price_myr or bot_settings.base_price_myr == 0.0:
            last_trade = self.db.query(Trade).order_by(Trade.created_at.desc()).first()
            if last_trade and last_trade.price_myr:
                bot_settings.base_price_myr = last_trade.price_myr
                logger.info(f"🔒 Base Price dikunci dari trade terakhir: RM {last_trade.price_myr:,.2f} ({last_trade.trade_type} pada {last_trade.created_at})")
            else:
                bot_settings.base_price_myr = current_price
                logger.info(f"🔒 Base Price dikunci pada harga semasa (tiada rekod trade): RM {current_price:,.2f}")
            self.db.commit()

        base_price = bot_settings.base_price_myr
        margin_pct = bot_settings.rebalance_margin_pct
        trade_size = bot_settings.trade_size_myr

        req_upper = base_price * (1 + margin_pct / 100.0)
        req_lower = base_price * (1 - margin_pct / 100.0)
        
        price_change_pct = ((current_price - base_price) / base_price) * 100

        result = {
            "action": "HOLD",
            "execute": False,
            "amount_myr": 0.0,
            "amount_btc": 0.0,
            "reason": f"Harga RM {current_price:,.2f} masih dalam grid (Base: RM {base_price:,.2f})",
        }

        # Scenario 1: Naik (Take profit) — Tiered Sell
        if current_price >= req_upper:
            # Jika naik 2x margin (contoh 5% bila margin 2.5%) → jual 2x ganda
            req_double = base_price * (1 + (margin_pct * 2) / 100.0)
            is_double_trigger = current_price >= req_double
            effective_size = trade_size * 2 if is_double_trigger else trade_size

            btc_to_sell = effective_size / current_price
            can_sell, blocked = self.can_sell(btc_to_sell, live_btc=real_balances.get("XBT", 0.0))

            if can_sell:
                # Update Base Price to new execution price
                bot_settings.base_price_myr = current_price
                self.db.commit()

                label = f"2× GANDA (naik {price_change_pct:.2f}%)" if is_double_trigger else f"naik {price_change_pct:.2f}%"
                result.update({
                    "action": "SELL",
                    "execute": True,
                    "amount_btc": btc_to_sell,
                    "amount_myr": effective_size,
                    "reason": f"Grid Sell {label} (> RM {req_upper:,.2f}). Jual RM {effective_size:.2f}"
                })
                logger.success(f"✅ GRID SELL {'2×' if is_double_trigger else '1×'} RM {effective_size:.2f} di harga RM {current_price:,.2f}")
            else:
                result["reason"] = f"Grid Sell Tersekat: {blocked}"
                logger.warning(f"⛔ GRID SELL BLOCKED: {blocked}")

        # Scenario 2: Turun (Buy the dip)
        elif current_price <= req_lower:
            can_buy, blocked = self.can_buy(trade_size, live_myr=real_balances.get("MYR", 0.0))
                
            if can_buy:
                bot_settings.base_price_myr = current_price
                self.db.commit()
                
                result.update({
                    "action": "BUY",
                    "execute": True,
                    "amount_myr": trade_size,
                    "reason": f"Grid Buy: Harga jatuh {price_change_pct:.2f}% (< RM {req_lower:,.2f}). Beli RM {trade_size:.2f}"
                })
                logger.success(f"✅ GRID DECISION: BUY RM {trade_size:.2f} di harga RM {current_price:,.2f}")
            else:
                result["reason"] = f"Grid Buy Tersekat: {blocked}"
                logger.warning(f"⛔ GRID BUY BLOCKED: {blocked}")

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
