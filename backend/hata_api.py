"""
hata_api.py — Hata Exchange API wrapper for Investment AI bot.
Handles auth/signing, order placement, balance checking, trade history.

All functions preserve backward-compatible signatures.
Endpoint reference: HATA_API_REFERENCE.md
"""

import os
import time
import hmac
import hashlib
import requests
import urllib.parse
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config bridge: try config.py Settings first, fallback to os.getenv()
# ---------------------------------------------------------------------------
try:
    from config import settings as _cfg
    HATA_API_KEY = _cfg.hata_api_key or os.getenv("HATA_API_KEY", "")
    HATA_API_SECRET = _cfg.hata_api_secret or os.getenv("HATA_API_SECRET", "")
    BASE_URL = _cfg.hata_base_url or "https://my-api.hata.io"
    _REQUEST_TIMEOUT = _cfg.hata_request_timeout or 10
    _MAX_RETRIES = _cfg.hata_max_retries or 3
except Exception:
    HATA_API_KEY = os.getenv("HATA_API_KEY", "")
    HATA_API_SECRET = os.getenv("HATA_API_SECRET", "")
    BASE_URL = "https://my-api.hata.io"
    _REQUEST_TIMEOUT = 10
    _MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Retry helper — only retries on transient network errors
# ---------------------------------------------------------------------------
def _retry_request(func):
    """Decorator: retry on network errors (timeout, ConnectionError).
    Does NOT retry on 4xx client errors."""
    def wrapper(*args, **kwargs):
        last_exc = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                last_exc = e
                wait = min(2 ** attempt, 10)
                logger.warning(
                    f"[Retry {attempt}/{_MAX_RETRIES}] {func.__name__} "
                    f"failed: {e}. Retrying in {wait}s..."
                )
                time.sleep(wait)
            except Exception:
                raise  # Don't retry non-network errors
        logger.error(f"[Retry] {func.__name__} failed after {_MAX_RETRIES} attempts")
        raise last_exc
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# ---------------------------------------------------------------------------
# Signature generation
# ---------------------------------------------------------------------------
def _generate_signature(params: dict, secret: str, is_post: bool = False) -> str:
    """Generate HMAC-SHA256 signature for Hata API.
    
    GET: sign the URL-encoded query string (sorted alphabetically)
    POST: sign the compact JSON string (sorted alphabetically, no spaces)
    """
    sorted_params = dict(sorted(params.items()))

    if is_post:
        # Hata API requires hashing the exact raw JSON string payload with no spaces
        query_string = json.dumps(sorted_params, separators=(',', ':'))
    else:
        # Construct query string for GET requests
        query_string = urllib.parse.urlencode(sorted_params)

    signature = hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


# ---------------------------------------------------------------------------
# Coin scales (hardcoded primary, refreshable via get_exchange_info)
# ---------------------------------------------------------------------------
COIN_SCALES = {
    # qty     = decimal places untuk quantity
    # price   = decimal places untuk price
    # min_notional = minimum nilai order (price × qty) dalam MYR — Hata minimum RM10
    "BTC": {"qty": 5, "price": 0, "min_notional": 10.0},
    "ETH": {"qty": 4, "price": 0, "min_notional": 10.0},
    "SOL": {"qty": 3, "price": 1, "min_notional": 10.0},
    "LTC": {"qty": 3, "price": 1, "min_notional": 10.0},
    "XRP": {"qty": 1, "price": 3, "min_notional": 10.0}
}


# ---------------------------------------------------------------------------
# Balance functions
# ---------------------------------------------------------------------------
@_retry_request
def get_myr_balance() -> tuple:
    """Fetch the real MYR balance (available, frozen) from Hata API"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        logger.warning("HATA_API_KEY or HATA_API_SECRET not found. Using simulated balance.")
        return 10000.00, 0.00

    endpoint = "/orderbook/sapi/balance"
    timestamp = str(int(time.time()))

    params = {
        "timestamp": timestamp,
        "token_symbol": "MYR"
    }

    signature = _generate_signature(params, HATA_API_SECRET)

    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }

    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(url, params=params, headers=headers, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        logger.debug(f"Hata Balance Response: {data}")

        if isinstance(data, list):
            for item in data:
                if item.get("symbol") == "MYR":
                    return float(item.get("available", 0.0)), float(item.get("frozen", 0.0))
        elif isinstance(data, dict):
            if "available" in data:
                return float(data.get("available", 0.0)), float(data.get("frozen", 0.0))
            elif "data" in data and isinstance(data["data"], list):
                 for item in data["data"]:
                    if item.get("symbol") == "MYR":
                        return float(item.get("available", 0.0)), float(item.get("frozen", 0.0))

        return 0.0, 0.0

    except requests.exceptions.RequestException:
        raise  # Let retry decorator handle network errors
    except Exception as e:
        logger.error(f"Error parsing Hata balance response: {e}")
        return 0.0, 0.0


@_retry_request
def get_token_balance(symbol: str) -> tuple:
    """Fetch the real token balance (available, frozen) from Hata API"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        return 0.0, 0.0

    endpoint = "/orderbook/sapi/balance"
    timestamp = str(int(time.time()))

    params = {
        "timestamp": timestamp,
        "token_symbol": symbol.upper()
    }

    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(url, params=params, headers=headers, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            for item in data:
                if item.get("symbol") == symbol.upper():
                    return float(item.get("available", 0.0)), float(item.get("frozen", 0.0))
        elif isinstance(data, dict):
            if "available" in data:
                return float(data.get("available", 0.0)), float(data.get("frozen", 0.0))
            elif "data" in data and isinstance(data["data"], list):
                 for item in data["data"]:
                    if item.get("symbol") == symbol.upper():
                        return float(item.get("available", 0.0)), float(item.get("frozen", 0.0))

        return 0.0, 0.0
    except requests.exceptions.RequestException:
        raise  # Let retry decorator handle
    except Exception as e:
        logger.error(f"Error parsing Hata balance for {symbol}: {e}")
        return 0.0, 0.0


# ---------------------------------------------------------------------------
# Order functions
# ---------------------------------------------------------------------------
@_retry_request
def get_order_status(order_id: str) -> dict:
    """Fetch order status/details from Hata API.
    
    Returns dict with structure:
        {"status": "success", "data": {"status": "fulfilled"|"active"|"cancelled", "trades": [...], ...}}
    """
    if not HATA_API_KEY or not HATA_API_SECRET:
        # Simulated mode: assume all orders are fulfilled
        return {"status": "success", "data": {"status": "fulfilled"}}

    endpoint = "/orderbook/sapi/order"
    timestamp = str(int(time.time()))

    params = {
        "order_id": str(order_id),
        "timestamp": timestamp
    }

    signature = _generate_signature(params, HATA_API_SECRET)

    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }

    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(url, params=params, headers=headers, timeout=_REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching order status for {order_id}: {response.text}")
            return {"status": "error", "message": response.text}
    except requests.exceptions.RequestException:
        raise  # Let retry decorator handle
    except Exception as e:
        logger.error(f"Error fetching order status for {order_id}: {e}")
        return {"status": "error", "message": str(e)}


@_retry_request
def place_limit_order(symbol: str, side: str, price: float, quantity: float) -> dict:
    """Place a Limit Maker Order on Hata.
    
    Args:
        symbol: Trading pair e.g. "BTC_MYR" or "BTCMYR"
        side: "BUY" or "SELL"
        price: Limit price in MYR
        quantity: Amount of base asset
        
    Returns:
        dict with order result. On success: {"status": "success", "data": {"id": "..."}}
        On error: {"status": "error", "message": "...", "code": "..."}
    """
    if not HATA_API_KEY or not HATA_API_SECRET:
        logger.info(f"SIMULATED: Placed Limit {side} for {quantity} {symbol} at RM{price}")
        return {"status": "simulated", "orderId": "sim_123", "price": price}

    endpoint = "/orderbook/sapi/orders/create"
    timestamp = str(int(time.time()))

    hata_side = "true" if side.upper() == "BUY" else "false"
    clean_symbol = symbol.replace("_", "").upper()
    base_coin = symbol.split("_")[0] if "_" in symbol else clean_symbol.replace("MYR", "")

    qty_scale = COIN_SCALES.get(base_coin, {}).get("qty", 4)
    price_scale = COIN_SCALES.get(base_coin, {}).get("price", 2)

    # Format according to exact scale
    fmt_price = f"{price:.{price_scale}f}"
    fmt_qty = f"{quantity:.{qty_scale}f}"

    # ★ Pre-flight: Validate notional (price × qty) sebelum hit API
    min_notional = COIN_SCALES.get(base_coin, {}).get("min_notional", 10.0)
    actual_notional = float(fmt_price) * float(fmt_qty)
    if actual_notional < min_notional:
        err_msg = (f"Order rejected (pre-flight): Notional RM{actual_notional:.4f} "
                   f"< minimum RM{min_notional:.2f} for {base_coin}. "
                   f"Increase trade_amount_myr or wait for lower price.")
        logger.warning(f"[MIN NOTIONAL GUARD] {err_msg}")
        return {"status": "error", "message": err_msg, "code": "min_notional"}

    params = {
        "is_buy": hata_side,
        "pair": clean_symbol,
        "price": fmt_price,
        "qty": fmt_qty,
        "timestamp": timestamp,
        "type": "limit"
    }

    signature = _generate_signature(params, HATA_API_SECRET, is_post=True)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.post(url, json=params, headers=headers, timeout=_REQUEST_TIMEOUT)
        if response.status_code != 200:
            err_msg = response.text
            logger.error(f"Error placing Limit {side} Order: {err_msg}")
            return {"status": "error", "message": err_msg}

        logger.info(f"Order Success: Limit {side} {quantity} {symbol} at RM{price}")
        return response.json()
    except requests.exceptions.RequestException:
        raise  # Let retry decorator handle
    except Exception as e:
        logger.error(f"Error placing Limit {side} Order: {e}")
        return {"status": "error", "message": str(e)}


@_retry_request
def cancel_order(symbol: str, order_id: str) -> dict:
    """Cancel an open order on Hata.
    
    Note: `symbol` param kept for backward compatibility but is NOT sent to API.
    Hata cancel endpoint only requires order_id + timestamp.
    """
    if not HATA_API_KEY or not HATA_API_SECRET:
        logger.info(f"SIMULATED: Cancelled Order {order_id}")
        return {"status": "simulated_cancelled"}

    endpoint = "/orderbook/sapi/orders/cancel"
    timestamp = str(int(time.time()))

    # API ref: only order_id + timestamp needed for cancel
    params = {
        "order_id": str(order_id),
        "timestamp": timestamp
    }

    signature = _generate_signature(params, HATA_API_SECRET, is_post=True)

    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.post(url, json=params, headers=headers, timeout=_REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error cancelling order {order_id}: {response.text}")
            return {"status": "error", "message": response.text}
    except requests.exceptions.RequestException:
        raise  # Let retry decorator handle
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        return {"status": "error", "message": str(e)}


@_retry_request
def get_my_orders(pair: str, status: str = "active") -> dict:
    """Fetch open/active orders from Hata API.
    
    Endpoint: GET /orderbook/sapi/users/orders
    Returns dict — callers read .get('data', []) for list of orders.
    """
    if not HATA_API_KEY or not HATA_API_SECRET:
        return {"status": "simulated", "data": []}

    endpoint = "/orderbook/sapi/users/orders"
    timestamp = str(int(time.time()))
    clean_pair = pair.replace("_", "").upper()

    params = {
        "order_rows": "250",
        "pair_name": clean_pair,
        "status": status,
        "timestamp": timestamp
    }

    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(url, params=params, headers=headers, timeout=_REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching orders for {pair}: {response.text}")
            return {"status": "error", "message": response.text}
    except requests.exceptions.RequestException:
        raise  # Let retry decorator handle
    except Exception as e:
        logger.error(f"Error fetching orders for {pair}: {e}")
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Ticker / market data
# ---------------------------------------------------------------------------
@_retry_request
def get_ticker(symbol: str = "ETH_MYR") -> float:
    """Fetch current market price (ticker) from exchange-info.
    
    Public endpoint, no auth required.
    Checks response fields: symbol → base+quote fallback.
    """
    clean_sym = symbol.replace("_", "").upper()
    url = f"{BASE_URL}/orderbook/api/v2/exchange-info"
    try:
        response = requests.get(url, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        items = data if isinstance(data, list) else data.get("data", [])

        # Primary: match by 'symbol' field (per API reference)
        for item in items:
            if item.get("symbol") == clean_sym:
                return float(item.get("price", 0.0))

        # Fallback: match by base + quote concatenation
        for item in items:
            base = item.get("base", "")
            quote = item.get("quote", "")
            if base and quote and (base + quote) == clean_sym:
                return float(item.get("price", 0.0))

        logger.warning(f"Ticker not found for {clean_sym}")
        return 0.0
    except requests.exceptions.RequestException:
        raise  # Let retry decorator handle
    except Exception as e:
        logger.error(f"Error fetching ticker for {symbol}: {e}")
        return 0.0


@_retry_request
def get_exchange_info() -> list:
    """Fetch all active trading pairs from Hata (public, no auth).
    
    Endpoint: GET /orderbook/api/v2/exchange-info
    Returns list of pair dicts with: base, quote, symbol, price, min_qty, max_qty,
    min_notional, max_notional, disp_qty_scale, disp_price_scale, tick_size, min_step
    """
    url = f"{BASE_URL}/orderbook/api/v2/exchange-info"
    try:
        response = requests.get(url, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        items = data if isinstance(data, list) else data.get("data", [])
        return items
    except Exception as e:
        logger.error(f"Error fetching exchange info: {e}")
        return []


def refresh_coin_scales() -> dict:
    """Optional: refresh COIN_SCALES from live exchange-info data.
    
    Fetches disp_qty_scale, disp_price_scale, min_notional from Hata API
    and updates the global COIN_SCALES dict.
    
    Returns the updated COIN_SCALES dict.
    """
    global COIN_SCALES
    items = get_exchange_info()
    if not items:
        logger.warning("refresh_coin_scales: No exchange info data, keeping existing scales")
        return COIN_SCALES

    updated = 0
    for item in items:
        quote = item.get("quote", "")
        if quote != "MYR":
            continue
        base = item.get("base", "")
        if not base:
            continue

        try:
            new_scale = {
                "qty": int(item.get("min_step", item.get("disp_qty_scale", 4))),
                "price": int(item.get("tick_size", item.get("disp_price_scale", 2))),
                "min_notional": float(item.get("min_notional", 10.0))
            }
            COIN_SCALES[base] = new_scale
            updated += 1
        except (ValueError, TypeError) as e:
            logger.warning(f"refresh_coin_scales: Failed to parse scales for {base}: {e}")

    logger.info(f"refresh_coin_scales: Updated {updated} coins — {list(COIN_SCALES.keys())}")
    return COIN_SCALES


# ---------------------------------------------------------------------------
# Trade history
# ---------------------------------------------------------------------------
@_retry_request
def get_trade_history(pair: str, limit: int = 50, start_time: str = None,
                      end_time: str = None, page: int = 1) -> dict:
    """Fetch trade history from Hata API for real P&L calculation.
    
    Endpoint: GET /orderbook/sapi/trades/history
    Returns dict — callers read .get("data", {}).get("trades", [])
    """
    if not HATA_API_KEY or not HATA_API_SECRET:
        return {"status": "simulated", "data": []}

    endpoint = "/orderbook/sapi/trades/history"
    timestamp = str(int(time.time()))
    clean_pair = pair.replace("_", "").replace("-", "").upper()

    # Single params dict — used for BOTH signing AND request
    params = {
        "timestamp": timestamp,
        "pair_name": clean_pair,
        "page": str(page),
        "rows": str(min(limit, 100))
    }

    if start_time:
        params["start_time"] = str(start_time)
    if end_time:
        params["end_time"] = str(end_time)

    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(url, params=params, headers=headers, timeout=_REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching trade history for {pair}: {response.text}")
            return {"status": "error", "message": response.text}
    except requests.exceptions.RequestException:
        raise  # Let retry decorator handle
    except Exception as e:
        logger.error(f"Error fetching trade history for {pair}: {e}")
        return {"status": "error", "message": str(e)}


def get_all_trade_history(pair: str, start_time: str = None, end_time: str = None) -> list:
    """Fetch ALL trade history with pagination (100 per page).
    Returns flat list of all fulfilled trades.
    Hata API response format: { "trades": [...], "pages": N }
    Trade history endpoint ONLY returns executed/fulfilled trades."""
    all_trades = []
    page = 1
    max_pages = 20  # Safety limit: 20 × 100 = 2000 trades max

    while page <= max_pages:
        res = get_trade_history(pair, limit=100, start_time=start_time, end_time=end_time, page=page)

        # Hata API: response = { "data": { "trades": [...], "pages": N }, "status": "success" }
        trades = res.get("data", {}).get("trades", [])

        if not trades:
            break
        all_trades.extend(trades)
        if len(trades) < 100:
            break  # Last page
        page += 1
        time.sleep(0.3)  # Rate limit

    return all_trades
