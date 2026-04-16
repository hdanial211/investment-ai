"""
exchange/luno_client.py — Luno Malaysia API wrapper
Supports multiple trading pairs (XBTMYR, ETHMYR, XRPMYR, SOLMYR)
"""
import requests
from loguru import logger
from typing import Optional
import sys, os
from dotenv import dotenv_values

# Cari .env dari root project
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
_cfg = dotenv_values(_env_path)

# Minimum order value in MYR for each pair
MIN_ORDER_MYR = 2.0

# Decimal precision per pair (Luno requirements)
VOLUME_PRECISION = {
    "XBTMYR": 6,
    "ETHMYR": 6,
    "XRPMYR": 2,   # XRP uses 2 decimal places
    "SOLMYR": 4,
    "AVAXMYR": 4,
    "ADAMY R": 0,
}


class LunoClient:
    """Wrapper untuk Luno Malaysia API — multi-pair support"""

    BASE_URL = "https://api.luno.com/api/1"

    def __init__(self):
        self.api_key    = _cfg.get('LUNO_API_KEY', '').strip()
        self.api_secret = _cfg.get('LUNO_API_SECRET', '').strip()
        self.session    = requests.Session()
        self.session.auth = (self.api_key, self.api_secret)
        logger.info("✅ Luno client initialized")

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Helper: GET request ke Luno API"""
        url  = f"{self.BASE_URL}{endpoint}"
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise Exception(f"Luno API Error: {data['error']}")
        return data

    def _post(self, endpoint: str, data: dict = None) -> dict:
        """Helper: POST request ke Luno API"""
        url  = f"{self.BASE_URL}{endpoint}"
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

    # ─────────────────────────────────────────────
    #  Price & Balance
    # ─────────────────────────────────────────────

    def get_price(self, pair: str = "XBTMYR") -> dict:
        """
        Dapatkan harga semasa untuk sebarang pasangan
        Returns: {"bid": float, "ask": float, "last_trade": float}
        """
        try:
            ticker = self._get("/ticker", params={"pair": pair})
            result = {
                "pair":       pair,
                "bid":        float(ticker["bid"]),
                "ask":        float(ticker["ask"]),
                "last_trade": float(ticker["last_trade"]),
                "timestamp":  ticker["timestamp"],
            }
            logger.info(f"📊 {pair} Price: RM {result['last_trade']:,.2f}")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting {pair} price: {e}")
            raise

    def get_btc_price(self) -> dict:
        """Backward compat — get XBTMYR price"""
        return self.get_price("XBTMYR")

    def get_all_prices(self, pairs: list = None) -> dict:
        """Dapatkan harga untuk semua atau senarai pair yang diberikan"""
        if pairs is None:
            pairs = ["XBTMYR", "ETHMYR", "XRPMYR", "SOLMYR"]
        result = {}
        for pair in pairs:
            try:
                result[pair] = self.get_price(pair)
            except Exception as e:
                logger.warning(f"⚠️ Cannot get price for {pair}: {e}")
                result[pair] = None
        return result

    def get_balances(self) -> dict:
        """
        Dapatkan semua baki akaun (semua asset)
        Returns: {"MYR": float, "XBT": float, "ETH": float, "XRP": float, "SOL": float, ...}
        """
        try:
            data     = self._get("/balance")
            balances = {}
            for b in data.get("balance", []):
                asset     = b["asset"]
                available = float(b["balance"]) - float(b["reserved"])
                balances[asset] = round(available, 8)
            logger.info(f"💰 MYR: {balances.get('MYR', 0):.2f} | XBT: {balances.get('XBT', 0):.6f}")
            return balances
        except Exception as e:
            logger.error(f"❌ Error getting balances: {e}")
            raise

    # ─────────────────────────────────────────────
    #  Order Placement — Multi-pair
    # ─────────────────────────────────────────────

    def place_buy_order(self, amount_myr: float, pair: str = "XBTMYR") -> dict:
        """
        Beli crypto dengan jumlah RM tertentu menggunakan LIMIT ORDER di bid price.
        Bekerja untuk semua pair: XBTMYR, ETHMYR, XRPMYR, SOLMYR
        """
        try:
            price_data = self.get_price(pair)
            bid_price  = price_data["bid"]

            if amount_myr < MIN_ORDER_MYR:
                raise ValueError(f"Jumlah terlalu kecil: RM {amount_myr} (min: RM {MIN_ORDER_MYR})")

            precision  = VOLUME_PRECISION.get(pair, 6)
            volume     = round(amount_myr / bid_price, precision)
            myr_value  = volume * bid_price

            logger.info(f"🛒 BUY {pair}: RM {amount_myr:.2f} @ RM {bid_price:,.2f} = {volume} units")

            order = self._post("/postorder", data={
                "pair":   pair,
                "type":   "BID",
                "volume": str(volume),
                "price":  str(int(bid_price)),
            })

            result = {
                "order_id":  order.get("order_id", ""),
                "pair":      pair,
                "amount_myr": myr_value,
                "amount_btc": volume,   # 'btc' untuk backward compat — sebenarnya ialah unit crypto
                "price":     bid_price,
                "status":    "PLACED",
            }
            logger.success(f"✅ BUY {pair} order placed: {result['order_id']}")
            return result

        except Exception as e:
            logger.error(f"❌ Error placing buy order [{pair}]: {e}")
            raise

    def place_sell_order(self, crypto_volume: float, pair: str = "XBTMYR",
                         target_price: Optional[float] = None) -> dict:
        """
        Jual crypto — guna BID price supaya order fill SEGERA.
        Bekerja untuk semua pair: XBTMYR, ETHMYR, XRPMYR, SOLMYR
        """
        try:
            price_data = self.get_price(pair)
            sell_price = target_price if target_price else price_data["bid"]

            precision     = VOLUME_PRECISION.get(pair, 6)
            crypto_volume = round(crypto_volume, precision)
            myr_value     = crypto_volume * sell_price

            if myr_value < MIN_ORDER_MYR:
                raise ValueError(f"Nilai terlalu kecil: RM {myr_value:.2f} (min: RM {MIN_ORDER_MYR})")

            logger.info(f"💸 SELL {pair}: {crypto_volume} units @ RM {sell_price:,.2f} = RM {myr_value:.2f}")

            order = self._post("/postorder", data={
                "pair":   pair,
                "type":   "ASK",
                "volume": str(crypto_volume),
                "price":  str(int(sell_price)),
            })

            result = {
                "order_id":  order.get("order_id", ""),
                "pair":      pair,
                "amount_btc": crypto_volume,
                "amount_myr": myr_value,
                "price":     sell_price,
                "status":    "PLACED",
            }
            logger.success(f"✅ SELL {pair} order placed: {result['order_id']}")
            return result

        except Exception as e:
            logger.error(f"❌ Error placing sell order [{pair}]: {e}")
            raise

    # ─────────────────────────────────────────────
    #  Order Management
    # ─────────────────────────────────────────────

    def cancel_order(self, order_id: str) -> bool:
        """Cancel open order"""
        try:
            self._post("/stoporder", data={"order_id": order_id})
            logger.info(f"🚫 Order {order_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"❌ Error cancelling order {order_id}: {e}")
            return False

    def get_open_orders(self, pair: str = "XBTMYR") -> list:
        """Dapatkan semua open orders untuk pair tertentu"""
        try:
            data = self._get("/listorders", params={"pair": pair, "state": "PENDING"})
            return data.get("orders", [])
        except Exception as e:
            logger.error(f"❌ Error getting open orders [{pair}]: {e}")
            return []

    def get_order_status(self, order_id: str) -> dict:
        """Check status sesuatu order — termasuk fee sebenar dari Luno"""
        try:
            order = self._get(f"/orders/{order_id}")
            # fee_counter = fee dalam MYR (dalam sen → bahagi 100)
            fee_myr = float(order.get("fee_counter", 0)) / 100
            return {
                "order_id":     order_id,
                "state":        order.get("state", "UNKNOWN"),
                "type":         order.get("type", ""),
                "volume_filled": float(order.get("base", 0)),
                "price":        float(order.get("limit_price", 0)),
                "fee_myr":      fee_myr,
            }
        except Exception as e:
            logger.error(f"❌ Error getting order status: {e}")
            raise

    def get_recent_trades(self, pair: str = "XBTMYR", limit: int = 20) -> list:
        """Dapatkan history trades terkini dari Luno untuk pair tertentu"""
        try:
            data = self._get("/listtrades", params={"pair": pair})
            return data.get("trades", [])[:limit]
        except Exception as e:
            logger.error(f"❌ Error getting trades [{pair}]: {e}")
            return []

    def get_price_history(self, pair: str = "XBTMYR", duration: int = 86400) -> list:
        """
        Dapatkan history harga untuk kira indicators
        duration: dalam saat (86400 = 24 jam)
        """
        try:
            data = self._get("/candles", params={"pair": pair, "duration": duration})
            return data.get("candles", [])
        except Exception as e:
            logger.warning(f"⚠️ Cannot get candles [{pair}]: {e}")
            return []


# Singleton instance
luno_client = LunoClient()
