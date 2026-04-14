"""
exchange/luno_client.py — Luno Malaysia API wrapper
Handles all buy/sell/balance operations via direct HTTP (requests)
"""
import requests
from loguru import logger
from typing import Optional
import sys, os
from dotenv import dotenv_values

# Cari .env dari root project
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
_cfg = dotenv_values(_env_path)


class LunoClient:
    """Wrapper untuk Luno Malaysia API"""

    PAIR = "XBTMYR"  # BTC/MYR pair di Luno
    BASE_URL = "https://api.luno.com/api/1"

    def __init__(self):
        self.api_key = _cfg.get('LUNO_API_KEY', '').strip()
        self.api_secret = _cfg.get('LUNO_API_SECRET', '').strip()
        self.session = requests.Session()
        self.session.auth = (self.api_key, self.api_secret)
        logger.info("✅ Luno client initialized")

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Helper: GET request ke Luno API"""
        url = f"{self.BASE_URL}{endpoint}"
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise Exception(f"Luno API Error: {data['error']}")
        return data

    def _post(self, endpoint: str, data: dict = None) -> dict:
        """Helper: POST request ke Luno API"""
        url = f"{self.BASE_URL}{endpoint}"
        resp = self.session.post(url, data=data, timeout=10)
        if not resp.ok:
            try:
                err_body = resp.json()
            except Exception:
                err_body = resp.text
            logger.error(f"Luno API {resp.status_code} — {err_body} | Payload: {data}")
            resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            raise Exception(f"Luno API Error: {result['error']}")
        return result

    def get_btc_price(self) -> dict:
        """
        Dapatkan harga BTC/MYR semasa
        Returns: {"bid": float, "ask": float, "last_trade": float, "timestamp": int}
        """
        try:
            ticker = self._get("/ticker", params={"pair": self.PAIR})
            result = {
                "bid": float(ticker["bid"]),
                "ask": float(ticker["ask"]),
                "last_trade": float(ticker["last_trade"]),
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
            data = self._get("/balance")
            balances = {}
            for b in data.get("balance", []):
                asset = b["asset"]
                available = float(b["balance"]) - float(b["reserved"])
                balances[asset] = available
            result = {
                "MYR": balances.get("MYR", 0.0),
                "XBT": balances.get("XBT", 0.0)  # BTC = XBT di Luno
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
            price_data = self.get_btc_price()
            bid_price = price_data["bid"]

            if amount_myr < 2.0:
                raise ValueError(f"Jumlah terlalu kecil: RM {amount_myr} (min: RM 2)")

            btc_volume = round(amount_myr / bid_price, 6)  # Luno: max 6 decimal places

            logger.info(f"🛒 Placing BUY order: RM {amount_myr:.2f} @ RM {bid_price:,.2f} = {btc_volume:.8f} BTC")

            order = self._post("/postorder", data={
                "pair": self.PAIR,
                "type": "BID",
                "volume": str(btc_volume),
                "price": str(int(bid_price))
            })

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

            myr_value = btc_volume * sell_price
            if myr_value < 2.0:
                raise ValueError(f"Nilai terlalu kecil: RM {myr_value:.2f} (min: RM 2)")

            logger.info(f"💸 Placing SELL order: {btc_volume:.8f} BTC @ RM {sell_price:,.2f}")

            order = self._post("/postorder", data={
                "pair": self.PAIR,
                "type": "ASK",
                "volume": str(round(btc_volume, 6)),  # Luno: max 6 decimal places
                "price": str(int(sell_price))
            })

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
            order = self._get(f"/orders/{order_id}")
            return {
                "order_id": order_id,
                "state": order.get("state", "UNKNOWN"),
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
            data = self._get("/listtrades", params={"pair": self.PAIR})
            return data.get("trades", [])[:limit]
        except Exception as e:
            logger.error(f"❌ Error getting trades: {e}")
            return []

    def get_order_book(self) -> dict:
        """Dapatkan order book (bid/ask levels)"""
        try:
            ob = self._get("/orderbook", params={"pair": self.PAIR})
            return {
                "asks": ob.get("asks", [])[:5],
                "bids": ob.get("bids", [])[:5],
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
            data = self._get("/candles", params={"pair": self.PAIR, "duration": duration})
            return data.get("candles", [])
        except Exception as e:
            logger.warning(f"⚠️ Cannot get candles: {e}")
            return []


# Singleton instance
luno_client = LunoClient()
