"""
notifications/telegram_bot.py — Telegram notification system
Hantar alert bila bot beli/jual/hold
"""
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from loguru import logger
from datetime import datetime
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


class TelegramNotifier:
    """Hantar notifikasi ke Telegram"""

    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.enabled = bool(self.bot_token and self.chat_id and
                           self.bot_token != "your_telegram_bot_token_here")

        if self.enabled:
            self.bot = Bot(token=self.bot_token)
            logger.info("✅ Telegram notifier initialized")
        else:
            logger.warning("⚠️ Telegram not configured — notifications disabled")

    async def _send(self, message: str):
        """Internal send method"""
        if not self.enabled:
            logger.debug(f"[Telegram DISABLED] {message[:100]}...")
            return
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            logger.info("📲 Telegram notification sent")
        except Exception as e:
            logger.error(f"❌ Telegram error: {e}")

    def send(self, message: str):
        """Synchronous wrapper"""
        asyncio.run(self._send(message))

    def notify_buy(self, amount_myr: float, amount_btc: float, price: float, reason: str, pnl: float = 0):
        """Notifikasi bila bot BELI BTC"""
        msg = f"""
🟢 <b>BITCOIN INVESTMENT AI — BELI</b>
━━━━━━━━━━━━━━━━━━━━━
💰 Jumlah Beli: <b>RM {amount_myr:.2f}</b>
₿  BTC Dapat:  <b>{amount_btc:.8f} BTC</b>
📊 Harga BTC:  <b>RM {price:,.2f}</b>

🔍 <i>Sebab: {reason}</i>

📦 Portfolio:
   P&amp;L: RM {pnl:+.2f}

⏰ {datetime.now().strftime('%d %b %Y, %I:%M %p')}
        """.strip()
        self.send(msg)

    def notify_sell(self, amount_btc: float, amount_myr: float, price: float, reason: str, pnl: float = 0):
        """Notifikasi bila bot JUAL BTC"""
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        msg = f"""
🔴 <b>BITCOIN INVESTMENT AI — JUAL</b>
━━━━━━━━━━━━━━━━━━━━━
₿  BTC Dijual: <b>{amount_btc:.8f} BTC</b>
💰 Dapat:      <b>RM {amount_myr:.2f}</b>
📊 Harga BTC:  <b>RM {price:,.2f}</b>

{pnl_emoji} Profit/Loss: <b>RM {pnl:+.2f}</b>
🔍 <i>Sebab: {reason}</i>

⏰ {datetime.now().strftime('%d %b %Y, %I:%M %p')}
        """.strip()
        self.send(msg)

    def notify_hold(self, price: float, price_change: float, rsi: float, reason: str):
        """Notifikasi HOLD (daily)"""
        msg = f"""
💤 <b>BITCOIN INVESTMENT AI — TAHAN</b>
━━━━━━━━━━━━━━━━━━━━━
📊 Harga BTC: <b>RM {price:,.2f}</b>
📈 Perubahan: <b>{price_change:+.2f}%</b> dari semalam
🔬 RSI: <b>{rsi if rsi else 'N/A'}</b>

💡 <i>{reason}</i>

⏰ {datetime.now().strftime('%d %b %Y, %I:%M %p')}
        """.strip()
        self.send(msg)

    def notify_daily_summary(self, portfolio: dict, trades_today: list, next_run: str):
        """Laporan harian setiap malam"""
        total = portfolio.get("total_value", 0)
        pnl = portfolio.get("pnl", 0)
        btc = portfolio.get("btc", 0)
        myr = portfolio.get("myr", 0)
        pnl_emoji = "📈" if pnl >= 0 else "📉"

        trades_summary = f"{len(trades_today)} transaksi hari ini" if trades_today else "Tiada transaksi hari ini"

        msg = f"""
📊 <b>LAPORAN HARIAN — BITCOIN INVESTMENT AI</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {datetime.now().strftime('%d %b %Y')}

💼 <b>Portfolio:</b>
   ₿  BTC: {btc:.8f} BTC
   💵 Cash: RM {myr:.2f}
   💰 Jumlah: RM {total:.2f}
   {pnl_emoji} P&amp;L: <b>RM {pnl:+.2f}</b>

📝 {trades_summary}

⏰ Run seterusnya: <b>{next_run}</b>
        """.strip()
        self.send(msg)

    def notify_error(self, error_msg: str):
        """Alert bila ada error"""
        msg = f"""
⚠️ <b>INVESTMENT AI — ERROR</b>
━━━━━━━━━━━━━━━━━━━━━
❌ {error_msg}

⏰ {datetime.now().strftime('%d %b %Y, %I:%M %p')}
        """.strip()
        self.send(msg)

    def notify_startup(self):
        """Bot startup notification"""
        msg = f"""
🚀 <b>BITCOIN INVESTMENT AI — STARTED</b>
━━━━━━━━━━━━━━━━━━━━━
✅ Bot telah diaktifkan!
⏰ Jadual: Setiap hari {settings.schedule_time}
💰 Jumlah harian: RM {settings.daily_amount_myr:.2f}
📊 Modal maksimum: RM {settings.max_capital_myr:.2f}
🔔 Notifikasi Telegram: Aktif

Exchange: Luno Malaysia (BTCMYR)
Strategi: DCA + RSI + Price Change
        """.strip()
        self.send(msg)


# Singleton
telegram = TelegramNotifier()
