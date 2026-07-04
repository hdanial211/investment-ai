"""
exchange/hata_ws.py — Hata Exchange WebSocket client.

Implements the full Hata WebSocket protocol:
- Token authentication flow (REST → WS connect)
- Correct subscribe/unsubscribe format
- Ping/pong heartbeat (respond within 8 seconds)
- Newline-delimited message splitting
- Auto-reconnect with exponential backoff
- Channel management with auto-resubscribe

Reference: HATA_API_REFERENCE.md § WebSocket

Usage:
    ws = HataWebSocket()
    ws.on("trade", my_trade_handler)
    ws.on("candle", my_candle_handler)
    await ws.connect()
    await ws.subscribe("public:BTCMYR@trade")
    await ws.subscribe("public:BTCMYR@candles_1")
"""

import asyncio
import json
import time
import logging
import requests
from typing import Callable, Dict, Optional, Set

logger = logging.getLogger(__name__)

try:
    import websockets
except ImportError:
    websockets = None
    logger.warning("websockets package not installed. Run: pip install websockets")


class HataWebSocket:
    """Full-featured WebSocket client for Hata Exchange.
    
    Args:
        platform: "MY" (Malaysia) or "WW" (Global)
        private: If True, subscribe to private channels (requires auth)
        on_message_callback: Legacy callback for all messages (backward compat)
    """

    # WebSocket URLs per platform
    WS_URLS = {
        "MY": "wss://websocket-my.hata.io/sapi/connection/websocket",
        "WW": "wss://websocket.hata.io/sapi/connection/websocket",
    }

    # Token endpoints per platform/type
    TOKEN_ENDPOINTS = {
        ("MY", "public"):  "/auth/api/v2/my/user-stream-key",
        ("MY", "private"): "/auth/sapi/v2/my/user-stream-key",
        ("WW", "public"):  "/auth/api/v2/ww/user-stream-key",
        ("WW", "private"): "/auth/sapi/v2/ww/user-stream-key",
    }

    # Auth base URL (always api.hata.io per reference)
    AUTH_BASE_URL = "https://api.hata.io"

    def __init__(self, platform: str = "MY", private: bool = False,
                 on_message_callback: Callable = None):
        self.platform = platform.upper()
        self.private = private
        self.url = self.WS_URLS.get(self.platform, self.WS_URLS["MY"])

        # Legacy callback (backward compat with data/collector.py)
        self._legacy_callback = on_message_callback

        # Channel-specific callbacks
        self._callbacks: Dict[str, Callable] = {}

        # Track subscribed channels for auto-resubscribe on reconnect
        self._subscribed_channels: Set[str] = set()

        # Connection state
        self._websocket = None
        self.is_running = False
        self._msg_id_counter = 0
        self._connection_token: Optional[str] = None

        # Reconnect backoff
        self._reconnect_delay = 5
        self._max_reconnect_delay = 60

        # Heartbeat
        self._last_pong_time = 0
        self._heartbeat_timeout = 30  # seconds before considering connection stale

        # Auth credentials (for private channels)
        self._api_key = ""
        self._api_secret = ""
        self._load_credentials()

    def _load_credentials(self):
        """Load API credentials from config or env."""
        import os
        try:
            from config import settings as _cfg
            self._api_key = _cfg.hata_api_key or os.getenv("HATA_API_KEY", "")
            self._api_secret = _cfg.hata_api_secret or os.getenv("HATA_API_SECRET", "")
        except Exception:
            self._api_key = os.getenv("HATA_API_KEY", "")
            self._api_secret = os.getenv("HATA_API_SECRET", "")

    def _next_msg_id(self) -> int:
        """Get next message ID for WebSocket protocol."""
        self._msg_id_counter += 1
        return self._msg_id_counter

    # ------------------------------------------------------------------
    # Channel-specific callbacks
    # ------------------------------------------------------------------
    def on(self, event_type: str, callback: Callable):
        """Register a callback for a specific event type.
        
        Event types: "depth", "trade", "candle", "newOrder", "cancelOrder", "newTrade"
        
        Example:
            ws.on("trade", lambda data, channel: print(f"Trade on {channel}: {data}"))
        """
        self._callbacks[event_type] = callback
        logger.debug(f"Registered callback for event type: {event_type}")

    # ------------------------------------------------------------------
    # Token auth
    # ------------------------------------------------------------------
    def _get_connection_token(self) -> str:
        """Fetch WebSocket connection token from REST API.
        
        Public tokens don't require auth headers.
        Private tokens require API key + signature.
        """
        stream_type = "private" if self.private else "public"
        endpoint_key = (self.platform, stream_type)
        endpoint = self.TOKEN_ENDPOINTS.get(endpoint_key)

        if not endpoint:
            raise ValueError(f"Unknown platform/type: {endpoint_key}")

        url = f"{self.AUTH_BASE_URL}{endpoint}"

        headers = {}
        body = {}

        if self.private:
            # Private tokens need auth
            import hmac
            import hashlib
            timestamp = str(int(time.time()))
            body = {"timestamp": timestamp}
            sorted_body = dict(sorted(body.items()))
            param_str = json.dumps(sorted_body, separators=(',', ':'))
            sig = hmac.new(
                self._api_secret.encode('utf-8'),
                param_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            headers = {
                "X-API-KEY": self._api_key,
                "Signature": sig,
                "Content-Type": "application/json"
            }

        try:
            response = requests.post(url, json=body, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            token = data.get("token") or data.get("data", {}).get("token", "")
            if not token:
                logger.error(f"No token in response: {data}")
                raise ValueError("Failed to get WebSocket token")
            logger.info(f"Got WS token for {self.platform} ({stream_type})")
            return token
        except Exception as e:
            logger.error(f"Failed to get WS connection token: {e}")
            raise

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------
    def _parse_messages(self, raw_message: str) -> list:
        """Split and parse newline-delimited JSON messages.
        
        Hata may combine multiple messages with \\n delimiter.
        """
        messages = []
        for line in raw_message.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse WS message: {e} — raw: {line[:200]}")
        return messages

    def _is_ping(self, data: dict) -> bool:
        """Check if message is a ping (empty dict from server)."""
        return data == {} or data == {"type": "ping"}

    def _detect_event_type(self, data: dict, channel: str) -> str:
        """Detect event type from message data and channel name.
        
        Channel format: "public:BTCMYR@depth", "public:BTCMYR@trade",
                        "public:BTCMYR@candles_1", "private:{user_id}"
        """
        if not channel:
            return "unknown"

        # Private events
        if channel.startswith("private:"):
            event = data.get("event", "")
            if event in ("newOrder", "cancelOrder", "newTrade"):
                return event
            return "private"

        # Public events — extract from channel suffix
        if "@" in channel:
            suffix = channel.split("@", 1)[1]
            if suffix == "depth":
                return "depth"
            elif suffix == "trade":
                return "trade"
            elif suffix.startswith("candles_"):
                return "candle"

        return "unknown"

    async def _handle_message(self, data: dict):
        """Route parsed message to appropriate callback."""
        # Ping/pong
        if self._is_ping(data):
            await self._send_pong()
            return

        # Connection response
        if "connect" in data:
            logger.info(f"WS connected — client ID: {data.get('connect', {}).get('client')}")
            return

        # Subscribe response
        if "subscribe" in data:
            sub_info = data.get("subscribe", {})
            logger.debug(f"Subscribed to channel: {sub_info}")
            return

        # Unsubscribe response
        if "unsubscribe" in data:
            logger.debug(f"Unsubscribed: {data.get('unsubscribe', {})}")
            return

        # Push data (actual market/trade updates)
        push = data.get("push", {})
        if push:
            channel = push.get("channel", "")
            pub = push.get("pub", {})
            event_data = pub.get("data", {})

            # Try parsing data if it's a JSON string
            if isinstance(event_data, str):
                try:
                    event_data = json.loads(event_data)
                except (json.JSONDecodeError, TypeError):
                    pass

            event_type = self._detect_event_type(event_data, channel)

            # Channel-specific callback
            if event_type in self._callbacks:
                try:
                    self._callbacks[event_type](event_data, channel)
                except Exception as e:
                    logger.error(f"Error in {event_type} callback: {e}")

            # Legacy callback (backward compat)
            if self._legacy_callback:
                try:
                    self._legacy_callback(event_data)
                except Exception as e:
                    logger.error(f"Error in legacy callback: {e}")

            return

        # Fallback: send to legacy callback if nothing else matched
        if self._legacy_callback:
            try:
                self._legacy_callback(data)
            except Exception as e:
                logger.error(f"Error in legacy callback: {e}")

    async def _send_pong(self):
        """Respond to server ping — must reply within 8 seconds."""
        if self._websocket:
            try:
                await self._websocket.send("{}")
                self._last_pong_time = time.time()
            except Exception as e:
                logger.warning(f"Failed to send pong: {e}")

    # ------------------------------------------------------------------
    # Subscribe / Unsubscribe
    # ------------------------------------------------------------------
    async def subscribe(self, channel: str):
        """Subscribe to a channel.
        
        Channel format examples:
            "public:BTCMYR@depth"       — Order book updates
            "public:BTCMYR@trade"       — Real-time trades
            "public:BTCMYR@candles_1"   — 1-min candles
            "public:BTCMYR@candles_5"   — 5-min candles
            "public:BTCMYR@candles_15"  — 15-min candles
            "public:BTCMYR@candles_30"  — 30-min candles
            "public:BTCMYR@candles_60"  — 1-hour candles
            "public:BTCMYR@candles_240" — 4-hour candles
        """
        self._subscribed_channels.add(channel)

        if self._websocket:
            msg = {
                "id": self._next_msg_id(),
                "subscribe": {"channel": channel}
            }
            await self._websocket.send(json.dumps(msg))
            logger.info(f"Subscribe sent: {channel}")

    async def unsubscribe(self, channel: str):
        """Unsubscribe from a channel."""
        self._subscribed_channels.discard(channel)

        if self._websocket:
            msg = {
                "id": self._next_msg_id(),
                "unsubscribe": {"channel": channel}
            }
            await self._websocket.send(json.dumps(msg))
            logger.info(f"Unsubscribe sent: {channel}")

    async def _resubscribe_all(self):
        """Resubscribe to all previously subscribed channels after reconnect."""
        for channel in self._subscribed_channels.copy():
            msg = {
                "id": self._next_msg_id(),
                "subscribe": {"channel": channel}
            }
            if self._websocket:
                await self._websocket.send(json.dumps(msg))
                logger.info(f"Resubscribed: {channel}")
                await asyncio.sleep(0.1)  # Small delay between subscribes

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------
    async def connect(self):
        """Main connection loop with auto-reconnect and exponential backoff."""
        if websockets is None:
            raise ImportError("websockets package required. Run: pip install websockets")

        self.is_running = True
        reconnect_delay = self._reconnect_delay

        while self.is_running:
            try:
                # Step 1: Get connection token
                logger.info(f"Getting WS connection token ({self.platform})...")
                self._connection_token = self._get_connection_token()

                # Step 2: Connect to WebSocket
                logger.info(f"Connecting to Hata WS: {self.url}")
                async with websockets.connect(
                    self.url,
                    ping_interval=None,  # We handle ping/pong ourselves
                    ping_timeout=None,
                    close_timeout=5
                ) as ws:
                    self._websocket = ws
                    logger.info("WebSocket connected!")

                    # Step 3: Send connect message with token
                    connect_msg = {
                        "id": self._next_msg_id(),
                        "connect": {"token": self._connection_token}
                    }
                    await ws.send(json.dumps(connect_msg))

                    # Step 4: Resubscribe to previously subscribed channels
                    if self._subscribed_channels:
                        await asyncio.sleep(0.5)  # Wait for connect response
                        await self._resubscribe_all()

                    # Reset backoff on successful connection
                    reconnect_delay = self._reconnect_delay
                    self._last_pong_time = time.time()

                    # Step 5: Message loop
                    while self.is_running:
                        try:
                            raw_message = await asyncio.wait_for(
                                ws.recv(), timeout=self._heartbeat_timeout
                            )

                            # Parse potentially multi-message payload
                            messages = self._parse_messages(raw_message)
                            for msg in messages:
                                await self._handle_message(msg)

                        except asyncio.TimeoutError:
                            # No message received within heartbeat timeout
                            logger.warning("WS heartbeat timeout — connection may be stale")
                            break  # Reconnect

            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WS Connection closed: {e}. Reconnecting in {reconnect_delay}s...")
            except Exception as e:
                logger.error(f"WS Error: {e}. Reconnecting in {reconnect_delay}s...")

            # Cleanup
            self._websocket = None

            if self.is_running:
                await asyncio.sleep(reconnect_delay)
                # Exponential backoff
                reconnect_delay = min(reconnect_delay * 2, self._max_reconnect_delay)

    def stop(self):
        """Stop the WebSocket connection gracefully."""
        logger.info("Stopping WebSocket client...")
        self.is_running = False

    # ------------------------------------------------------------------
    # Convenience: subscribe helpers
    # ------------------------------------------------------------------
    async def subscribe_depth(self, pair: str):
        """Subscribe to order book depth updates."""
        clean = pair.replace("_", "").upper()
        await self.subscribe(f"public:{clean}@depth")

    async def subscribe_trades(self, pair: str):
        """Subscribe to real-time trade updates."""
        clean = pair.replace("_", "").upper()
        await self.subscribe(f"public:{clean}@trade")

    async def subscribe_candles(self, pair: str, interval: int = 1):
        """Subscribe to candlestick updates.
        
        Args:
            pair: Trading pair e.g. "BTC_MYR"
            interval: Candle interval in minutes (1, 5, 15, 30, 60, 240)
        """
        valid = {1, 5, 15, 30, 60, 240}
        if interval not in valid:
            raise ValueError(f"Invalid candle interval {interval}. Valid: {valid}")
        clean = pair.replace("_", "").upper()
        await self.subscribe(f"public:{clean}@candles_{interval}")


# ------------------------------------------------------------------
# Standalone test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    logging.basicConfig(level=logging.DEBUG)

    def on_trade(data, channel):
        print(f"[TRADE] {channel}: {data}")

    def on_depth(data, channel):
        print(f"[DEPTH] {channel}: asks={len(data.get('asks', []))} bids={len(data.get('bids', []))}")

    async def main():
        ws = HataWebSocket(platform="MY")
        ws.on("trade", on_trade)
        ws.on("depth", on_depth)

        # Subscribe before connect — will auto-subscribe after connection
        await ws.subscribe_trades("BTC_MYR")
        await ws.subscribe_depth("BTC_MYR")

        await ws.connect()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped.")
