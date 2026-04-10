"""
exchange/luno_client.py — Luno Malaysia API wrapper
Handles all buy/sell/balance operations
"""
import luno_python.client as luno
import asyncio
from loguru import logger
from typing import Optional
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


class LunoClient:
    """Wrapper untuk Luno Malaysia API"""

    PAIR = "XBTMYR"  # BTC/MYR pair di Luno

    def __init__(self):
        self.client = luno.Client(
            api_key_id=settings.luno_api_key,
            api_key_secret=settings.luno_api_secret
        )
        logger.info("✅ Luno client initialized")

    def get_btc_price(self) -> dict:
        """
        Dapatkan harga BTC/MYR semasa
        Returns: {"bid": float, "ask": float, "last_trade": float, "timestamp": int}
        """
        try:
            ticker = self.client.get_ticker(pair=self.PAIR)
            result = {
                "bid": float(ticker["bid"]),          # harga terbaik pembeli
                "ask": float(ticker["ask"]),          # harga terbaik penjual
                "last_trade": float(ticker["last_trade"]),  # last traded price
                "timestamp": ticker["timestamp"]
            }
            logger.info(f"📊 BTC Price: RM {result['last_trade']:,.2f}")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting BTC price: {e}")
            raise

    def get_balances(self) -> dict:
        """
        Dapatkan baki akaun (RM dan BTC)
        Returns: {"MYR": float, "XBT": float}
        """
        try:
            balances_resp = self.client.get_balances()
            balances = {}
            for b in balances_resp.get("balance", []):
                currency = b["asset"]
                # Luno stores balance as string, convert to float
                available = float(b["balance"]) - float(b["reserved"])
                balances[currency] = available
            result = {
                "MYR": balances.get("MYR", 0.0),
                "XBT": balances.get("XBT", 0.0)   # BTC = XBT di Luno
            }
            logger.info(f"💰 Balances — RM: {result['MYR']:.2f} | BTC: {result['XBT']:.8f}")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting balances: {e}")
            raise

    def place_buy_order(self, amount_myr: float) -> dict:
        """
        Beli BTC dengan jumlah RM tertentu menggunakan LIMIT ORDER
        (maker fee = 0% — PERCUMA!)
        """
        try:
            # Dapatkan harga semasa
            price_data = self.get_btc_price()
            bid_price = price_data["bid"]

            # Kira berapa BTC boleh dibeli
            # Luno min order: ~RM 2
            if amount_myr < 2.0:
                raise ValueError(f"Jumlah terlalu kecil: RM {amount_myr} (min: RM 2)")

            # Kira BTC volume (round down untuk elak insufficient funds)
            btc_volume = amount_myr / bid_price
            # Round to 8 decimal places (satoshi precision)
            btc_volume = round(btc_volume, 8)

            logger.info(f"🛒 Placing BUY order: RM {amount_myr:.2f} @ RM {bid_price:,.2f} = {btc_volume:.8f} BTC")

            # Place limit buy order
            order = self.client.post_limit_order(
                pair=self.PAIR,
                type="BID",                          # BID = beli
                volume=str(btc_volume),
                price=str(int(bid_price))            # price dalam sen/unit
            )

            result = {
                "order_id": order.get("order_id", ""),
                "amount_myr": amount_myr,
                "amount_btc": btc_volume,
                "price": bid_price,
                "status": "PLACED"
            }
            logger.success(f"✅ BUY order placed: {result['order_id']}")
            return result

        except Exception as e:
            logger.error(f"❌ Error placing buy order: {e}")
            raise

    def place_sell_order(self, btc_volume: float, target_price: Optional[float] = None) -> dict:
        """
        Jual BTC
        btc_volume: berapa BTC nak jual
        target_price: jika None, guna harga semasa (ask price)
        """
        try:
            price_data = self.get_btc_price()
            sell_price = target_price if target_price else price_data["ask"]

            # Minimum volume check
            myr_value = btc_volume * sell_price
            if myr_value < 2.0:
                raise ValueError(f"Nilai terlalu kecil: RM {myr_value:.2f} (min: RM 2)")

            logger.info(f"💸 Placing SELL order: {btc_volume:.8f} BTC @ RM {sell_price:,.2f}")

            order = self.client.post_limit_order(
                pair=self.PAIR,
                type="ASK",                          # ASK = jual
                volume=str(round(btc_volume, 8)),
                price=str(int(sell_price))
            )

            result = {
                "order_id": order.get("order_id", ""),
                "amount_btc": btc_volume,
                "amount_myr": myr_value,
                "price": sell_price,
                "status": "PLACED"
            }
            logger.success(f"✅ SELL order placed: {result['order_id']}")
            return result

        except Exception as e:
            logger.error(f"❌ Error placing sell order: {e}")
            raise

    def get_order_status(self, order_id: str) -> dict:
        """Check status sesuatu order"""
        try:
            order = self.client.get_order(id=order_id)
            return {
                "order_id": order_id,
                "state": order.get("state", "UNKNOWN"),  # PENDING/COMPLETE/CANCELLED
                "type": order.get("type", ""),
                "volume_filled": float(order.get("base", 0)),
                "price": float(order.get("limit_price", 0))
            }
        except Exception as e:
            logger.error(f"❌ Error getting order status: {e}")
            raise

    def get_recent_trades(self, limit: int = 20) -> list:
        """Dapatkan history trades terkini dari Luno"""
        try:
            trades = self.client.list_trades(pair=self.PAIR)
            return trades.get("trades", [])[:limit]
        except Exception as e:
            logger.error(f"❌ Error getting trades: {e}")
            return []

    def get_order_book(self) -> dict:
        """Dapatkan order book (bid/ask levels)"""
        try:
            ob = self.client.get_order_book(pair=self.PAIR)
            return {
                "asks": ob.get("asks", [])[:5],  # top 5 sell orders
                "bids": ob.get("bids", [])[:5],  # top 5 buy orders
            }
        except Exception as e:
            logger.error(f"❌ Error getting order book: {e}")
            return {}

    def get_price_history(self, duration: int = 86400) -> list:
        """
        Dapatkan history harga untuk kira indicators
        duration: dalam saat (86400 = 24 jam, 604800 = 7 hari)
        """
        try:
            candles = self.client.get_candles(pair=self.PAIR, duration=duration)
            return candles.get("candles", [])
        except Exception as e:
            logger.warning(f"⚠️ Cannot get candles (API may not support): {e}")
            return []


# Singleton instance
luno_client = LunoClient()
