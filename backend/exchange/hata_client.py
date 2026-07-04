"""
exchange/hata_client.py — Object-oriented Hata Exchange HTTP client.

Full-featured OOP alternative to hata_api.py module-level functions.
Supports both GET (query string signing) and POST (JSON body signing).

Usage:
    client = HataClient()
    client.get_balance("MYR")
    client.place_order("BTCMYR", "BUY", price=420000, qty=0.001)
"""

import os
import time
import hmac
import hashlib
import json
import urllib.parse
import requests
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class HataAPIError(Exception):
    """Raised when Hata API returns a non-200 status or error response."""
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class HataClient:
    """Full-featured HTTP client for Hata Exchange API.
    
    Args:
        api_key: Hata API key (falls back to HATA_API_KEY env var)
        api_secret: Hata API secret (falls back to HATA_API_SECRET env var)
        base_url: Base REST API URL (default: Malaysia endpoint)
        timeout: Request timeout in seconds
        max_retries: Max retry attempts for transient errors
    """

    def __init__(self, api_key: str = None, api_secret: str = None,
                 base_url: str = None, timeout: int = None,
                 max_retries: int = None):
        # Try config.py first, then env vars
        try:
            from config import settings as _cfg
            self.api_key = api_key or _cfg.hata_api_key or os.getenv("HATA_API_KEY", "")
            self.api_secret = api_secret or _cfg.hata_api_secret or os.getenv("HATA_API_SECRET", "")
            self.base_url = base_url or _cfg.hata_base_url or "https://my-api.hata.io"
            self.timeout = timeout or _cfg.hata_request_timeout or 10
            self.max_retries = max_retries or _cfg.hata_max_retries or 3
        except Exception:
            self.api_key = api_key or os.getenv("HATA_API_KEY", "")
            self.api_secret = api_secret or os.getenv("HATA_API_SECRET", "")
            self.base_url = base_url or "https://my-api.hata.io"
            self.timeout = timeout or 10
            self.max_retries = max_retries or 3

        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Auth / Signature
    # ------------------------------------------------------------------
    def _generate_signature(self, params: Dict[str, Any],
                            is_post: bool = False) -> str:
        """Generate HMAC-SHA256 signature.
        
        GET: sign URL-encoded query string (sorted alphabetically)
        POST: sign compact JSON string (sorted, no spaces)
        """
        if not params:
            query_string = ""
        else:
            sorted_params = dict(sorted(params.items()))
            if is_post:
                query_string = json.dumps(sorted_params, separators=(',', ':'))
            else:
                query_string = urllib.parse.urlencode(sorted_params)

        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _add_auth(self, params: Dict[str, Any], endpoint: str,
                  is_post: bool = False) -> Dict[str, str]:
        """Add timestamp to params and return auth headers."""
        # Add timestamp for signed endpoints
        if self.api_secret and "/sapi/" in endpoint:
            params['timestamp'] = str(int(time.time()))

        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        if self.api_secret:
            headers["Signature"] = self._generate_signature(params, is_post=is_post)

        return headers

    # ------------------------------------------------------------------
    # HTTP request with retry
    # ------------------------------------------------------------------
    def _request(self, method: str, endpoint: str,
                 params: Dict[str, Any] = None,
                 requires_auth: bool = True) -> Dict[str, Any]:
        """Execute HTTP request with retry on transient errors.
        
        Args:
            method: "GET" or "POST"
            endpoint: API endpoint path (e.g. "/orderbook/sapi/balance")
            params: Query params (GET) or body (POST)
            requires_auth: Whether to add auth headers
            
        Returns:
            Parsed JSON response
            
        Raises:
            HataAPIError: On non-200 response after all retries
        """
        params = params or {}
        is_post = method.upper() == "POST"

        # Auth
        if requires_auth:
            headers = self._add_auth(params, endpoint, is_post=is_post)
        else:
            headers = {}

        if is_post:
            headers["Content-Type"] = "application/json"

        url = f"{self.base_url}{endpoint}"
        last_exc = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = self._session.get(
                        url, headers=headers, params=params, timeout=self.timeout
                    )
                elif method.upper() == "POST":
                    response = self._session.post(
                        url, headers=headers, json=params, timeout=self.timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Success
                if response.status_code == 200:
                    return response.json()

                # Client error (4xx) — don't retry
                if 400 <= response.status_code < 500:
                    raise HataAPIError(
                        f"Hata API {response.status_code}: {response.text}",
                        status_code=response.status_code,
                        response_body=response.text
                    )

                # Server error (5xx) — retry
                last_exc = HataAPIError(
                    f"Hata API {response.status_code}: {response.text}",
                    status_code=response.status_code,
                    response_body=response.text
                )
                wait = min(2 ** attempt, 10)
                logger.warning(
                    f"[Retry {attempt}/{self.max_retries}] {method} {endpoint} "
                    f"→ {response.status_code}. Retrying in {wait}s..."
                )
                time.sleep(wait)

            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                last_exc = e
                wait = min(2 ** attempt, 10)
                logger.warning(
                    f"[Retry {attempt}/{self.max_retries}] {method} {endpoint} "
                    f"failed: {e}. Retrying in {wait}s..."
                )
                time.sleep(wait)

            except HataAPIError:
                raise  # Don't retry client errors

        # All retries exhausted
        if isinstance(last_exc, HataAPIError):
            raise last_exc
        raise HataAPIError(f"Request failed after {self.max_retries} retries: {last_exc}")

    # ------------------------------------------------------------------
    # Public endpoints (no auth)
    # ------------------------------------------------------------------
    def get_exchange_info(self) -> list:
        """Get all active trading pairs.
        
        Endpoint: GET /orderbook/api/v2/exchange-info (public)
        Returns list of pair dicts.
        """
        data = self._request("GET", "/orderbook/api/v2/exchange-info", requires_auth=False)
        return data if isinstance(data, list) else data.get("data", [])

    def get_orderbook(self, pair: str, is_buy: bool = None) -> dict:
        """Get order book depth.
        
        Endpoint: GET /orderbook/api/orderbook (public)
        Returns {"asks": [...], "bids": [...]}
        """
        params = {"pair_name": pair.replace("_", "").upper()}
        if is_buy is not None:
            params["is_buy"] = str(is_buy).lower()
        return self._request("GET", "/orderbook/api/orderbook",
                             params=params, requires_auth=False)

    def get_ticker(self, symbol: str = "ETH_MYR") -> float:
        """Get current market price for a trading pair.
        
        Returns price as float, 0.0 if not found.
        """
        clean_sym = symbol.replace("_", "").upper()
        items = self.get_exchange_info()

        for item in items:
            if item.get("symbol") == clean_sym:
                return float(item.get("price", 0.0))

        for item in items:
            base = item.get("base", "")
            quote = item.get("quote", "")
            if base and quote and (base + quote) == clean_sym:
                return float(item.get("price", 0.0))

        logger.warning(f"Ticker not found for {clean_sym}")
        return 0.0

    # ------------------------------------------------------------------
    # Balance
    # ------------------------------------------------------------------
    def get_balance(self, symbol: str = None) -> dict:
        """Get spot balance for a token (or all tokens).
        
        Endpoint: GET /orderbook/sapi/balance
        Returns raw API response dict.
        """
        params = {}
        if symbol:
            params["token_symbol"] = symbol.upper()
        return self._request("GET", "/orderbook/sapi/balance", params=params)

    def get_available_balance(self, symbol: str) -> Tuple[float, float]:
        """Get (available, frozen) balance for a specific token.
        
        Convenience method matching hata_api.get_token_balance() signature.
        Returns (available, frozen) as floats.
        """
        data = self.get_balance(symbol)

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

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    def get_order(self, order_id: str) -> dict:
        """Get order details including trades.
        
        Endpoint: GET /orderbook/sapi/order
        Returns raw API response with 'data' containing order + trades.
        """
        return self._request("GET", "/orderbook/sapi/order",
                             params={"order_id": str(order_id)})

    def get_orders(self, pair: str = None, status: str = "active",
                   limit: int = 250) -> dict:
        """Get user orders with optional filters.
        
        Endpoint: GET /orderbook/sapi/users/orders
        """
        params = {
            "order_rows": str(limit),
            "status": status
        }
        if pair:
            params["pair_name"] = pair.replace("_", "").upper()
        return self._request("GET", "/orderbook/sapi/users/orders", params=params)

    def place_order(self, pair: str, side: str, price: float, qty: float,
                    order_type: str = "limit", post_only: bool = False,
                    client_order_id: str = None) -> dict:
        """Create a new order.
        
        Endpoint: POST /orderbook/sapi/orders/create
        
        Args:
            pair: Trading pair e.g. "BTCMYR" or "BTC_MYR"
            side: "BUY" or "SELL"
            price: Limit price (required for limit orders)
            qty: Quantity of base asset
            order_type: "limit" or "market"
            post_only: If True, order is maker-only (0% fee)
            client_order_id: Custom ID (max 20 chars)
        """
        clean_pair = pair.replace("_", "").upper()
        params = {
            "pair": clean_pair,
            "is_buy": "true" if side.upper() == "BUY" else "false",
            "type": order_type,
            "price": str(price),
            "qty": str(qty),
        }
        if post_only:
            params["post_only"] = "true"
        if client_order_id:
            params["client_order_id"] = client_order_id[:20]

        return self._request("POST", "/orderbook/sapi/orders/create", params=params)

    def cancel_order(self, order_id: str) -> dict:
        """Cancel an open order.
        
        Endpoint: POST /orderbook/sapi/orders/cancel
        """
        return self._request("POST", "/orderbook/sapi/orders/cancel",
                             params={"order_id": str(order_id)})

    def cancel_all_orders(self, pair: str) -> dict:
        """Cancel all open orders for a trading pair.
        
        Endpoint: POST /orderbook/sapi/orders/cancel/all
        """
        return self._request("POST", "/orderbook/sapi/orders/cancel/all",
                             params={"pair_name": pair.replace("_", "").upper()})

    # ------------------------------------------------------------------
    # Trade History
    # ------------------------------------------------------------------
    def get_trade_history(self, pair: str = None, page: int = 1,
                          rows: int = 100, start_time: int = None,
                          end_time: int = None) -> dict:
        """Get executed trade history.
        
        Endpoint: GET /orderbook/sapi/trades/history
        Returns {"data": {"trades": [...], "pages": N}, "status": "success"}
        """
        params = {
            "page": str(page),
            "rows": str(min(rows, 100))
        }
        if pair:
            params["pair_name"] = pair.replace("_", "").replace("-", "").upper()
        if start_time:
            params["start_time"] = str(start_time)
        if end_time:
            params["end_time"] = str(end_time)

        return self._request("GET", "/orderbook/sapi/trades/history", params=params)

    def get_all_trade_history(self, pair: str, start_time: int = None,
                              end_time: int = None,
                              max_pages: int = 20) -> List[dict]:
        """Fetch ALL trade history with auto-pagination.
        
        Returns flat list of all trade dicts.
        """
        all_trades = []
        page = 1

        while page <= max_pages:
            res = self.get_trade_history(pair, page=page, rows=100,
                                         start_time=start_time, end_time=end_time)
            trades = res.get("data", {}).get("trades", [])
            if not trades:
                break
            all_trades.extend(trades)
            if len(trades) < 100:
                break
            page += 1
            time.sleep(0.3)  # Rate limit

        return all_trades

    # ------------------------------------------------------------------
    # Wallet (bonus methods)
    # ------------------------------------------------------------------
    def get_deposit_history(self, token: str = None, page: int = 1,
                            rows: int = 100) -> dict:
        """Get deposit history.
        
        Endpoint: GET /wallet/sapi/deposit/his
        """
        params = {"page": str(page), "rows": str(min(rows, 100))}
        if token:
            params["token_symbol"] = token.upper()
        return self._request("GET", "/wallet/sapi/deposit/his", params=params)

    def get_withdrawal_history(self, token: str = None, page: int = 1,
                               rows: int = 100) -> dict:
        """Get withdrawal history.
        
        Endpoint: GET /wallet/sapi/withdrawal/his
        """
        params = {"page": str(page), "rows": str(min(rows, 100))}
        if token:
            params["token_symbol"] = token.upper()
        return self._request("GET", "/wallet/sapi/withdrawal/his", params=params)
