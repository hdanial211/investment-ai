# 📘 HATA API Reference Guide
> **Last Updated:** 2026-07-04  
> **Purpose:** Reference file for agents/Antigravity when calling Hata API

---

## 🔐 Authentication

### Generate Signature
1. Get **API Key** & **Secret Key** from Hata Security page
2. Add `timestamp` parameter to every request
3. **Sort all parameters alphabetically** before signing
4. Generate signature: `HMAC-SHA256(sorted_params, secret_key)`

### Required Headers
```
X-API-KEY: <your_api_key>
Signature: <hmac_sha256_signature>
```

### Python Example
```python
import hmac, hashlib, time, requests

API_KEY = "your_api_key"
SECRET_KEY = "your_secret_key"

def generate_signature(params: dict, secret: str) -> str:
    sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hmac.new(secret.encode(), sorted_params.encode(), hashlib.sha256).hexdigest()

def hata_get(url: str, params: dict) -> dict:
    params["timestamp"] = int(time.time())
    sig = generate_signature(params, SECRET_KEY)
    headers = {"X-API-KEY": API_KEY, "Signature": sig}
    return requests.get(url, params=params, headers=headers).json()

def hata_post(url: str, body: dict) -> dict:
    body["timestamp"] = int(time.time())
    sorted_body = dict(sorted(body.items()))
    param_str = "&".join(f"{k}={v}" for k, v in sorted_body.items())
    sig = hmac.new(SECRET_KEY.encode(), param_str.encode(), hashlib.sha256).hexdigest()
    headers = {"X-API-KEY": API_KEY, "Signature": sig, "Content-Type": "application/json"}
    return requests.post(url, json=sorted_body, headers=headers).json()
```

---

## 🌐 Base URLs

| Platform | REST API | WebSocket |
|----------|----------|-----------|
| **Global** | `https://api.hata.io` | `wss://websocket.hata.io/sapi/connection/websocket` |
| **Malaysia** | `https://my-api.hata.io` | `wss://websocket-my.hata.io/sapi/connection/websocket` |

> All `/auth/...` endpoints use `https://api.hata.io`

---

## 📊 Market (Public - No Auth)

### Get Active Trading Pairs
```
GET /orderbook/api/v2/exchange-info
```
**Response:**
```json
[{
  "base": "BTC", "quote": "MYR", "symbol": "BTCMYR",
  "price": "12000", "percentage": "10",
  "base_volume": "1000", "quote_volume": "40000",
  "min_qty": "0.0001", "max_qty": "1",
  "min_notional": "30", "max_notional": "50000",
  "disp_qty_scale": 2, "disp_price_scale": 2,
  "tick_size": "2", "min_step": "3"
}]
```

### Get Order Book Depth
```
GET /orderbook/api/orderbook?pair_name=BTCMYR&is_buy=true
```
| Param | Required | Description |
|-------|----------|-------------|
| `pair_name` | ✅ | e.g. `BTCMYR` |
| `is_buy` | ❌ | `true` for bids, `false` for asks |

**Response:** `{ "asks": [...], "bids": [...] }`

---

## 📈 Trade (Auth Required)

### Get User Orders
```
GET /orderbook/sapi/users/orders
```
| Param | Required | Description |
|-------|----------|-------------|
| `order_rows` | ✅ | Max 250 |
| `pair_name` | ❌ | Filter by pair |
| `status` | ❌ | `active`, `fulfilled`, `cancelled` |
| `type` | ❌ | `market`, `limit` |
| `is_buy` | ❌ | Boolean |
| `start_time` | ❌ | Timestamp |
| `end_time` | ❌ | Timestamp |
| `offset` | ❌ | Pagination offset |
| `order_id` | ❌ | Specific order |
| `client_order_id` | ❌ | Client order ID |

**Response:**
```json
[{
  "id": 0, "time": 0, "user_id": 0,
  "pair_name": "BTCMYR", "price": "120000",
  "orig_qty": "0.001", "exec_qty": "0.001",
  "quote_order_qty": "120", "cummul_quote_qty": "120",
  "is_buy": true, "type": "limit", "status": "fulfilled",
  "average_price": "120000", "client_order_id": "abc123"
}]
```

### Get Spot Balance
```
GET /orderbook/sapi/balance?token_symbol=BTC
```
| Param | Required | Description |
|-------|----------|-------------|
| `token_symbol` | ❌ | Filter by token, omit for all |

**Response:**
```json
{
  "name": "Bitcoin", "symbol": "BTC", "image": "...",
  "available": "0.5", "available_in_quote": "60000",
  "frozen": "0.1", "frozen_in_quote": "12000",
  "disp_qty_scale": 8, "disp_price_scale": 2, "is_fiat": false
}
```

### Get Order Details
```
GET /orderbook/sapi/order?order_id=12345
```
| Param | Required | Description |
|-------|----------|-------------|
| `order_id` | ✅ | Order ID |

**Response:** Same as orders + `"trades": [...]`

### Get Trade History
```
GET /orderbook/sapi/trades/history
```
| Param | Required | Description |
|-------|----------|-------------|
| `page` | ✅ | Page number (≥1) |
| `rows` | ✅ | Max 100 |
| `pair_name` | ❌ | Filter by pair |
| `is_buy` | ❌ | Boolean |
| `start_time` | ❌ | Timestamp |
| `end_time` | ❌ | Timestamp |
| `trade_id` | ❌ | Specific trade |

**Response:** `{ "trades": [...], "pages": 5 }`

### Create Order
```
POST /orderbook/sapi/orders/create
```
| Field | Required | Description |
|-------|----------|-------------|
| `pair` | ✅ | e.g. `"BTCUSDT"` |
| `is_buy` | ✅ | `"true"` or `"false"` (string) |
| `type` | ✅ | `"limit"` or `"market"` |
| `price` | ❌ | Required for limit orders |
| `qty` | ❌ | Quantity |
| `quote_qty` | ❌ | For market buy orders |
| `post_only` | ❌ | `"true"` = maker only (0% fee) |
| `stop_limit_price` | ❌ | Stop-limit trigger |
| `client_order_id` | ❌ | Custom ID (max 20 chars) |

> **Max 100 open orders per pair**

**Request Example (Limit Buy):**
```json
{
  "pair": "BTCMYR",
  "is_buy": "true",
  "type": "limit",
  "price": "120000",
  "qty": "0.001",
  "post_only": "true",
  "timestamp": 1704789520
}
```

### Cancel Order
```
POST /orderbook/sapi/orders/cancel
```
```json
{ "order_id": "1234567890", "timestamp": 1704789520 }
```
**Response:** `{ "order_id": "1234567890", "status": "cancelled" }`

### Cancel All Orders (by pair)
```
POST /orderbook/sapi/orders/cancel/all
```
```json
{ "pair_name": "BTCUSDT", "timestamp": 1704789520 }
```
**Response:** `{ "row_affected": 3 }`

---

## 💰 Wallet (Auth Required)

### Deposit History
```
GET /wallet/sapi/deposit/his
```
| Param | Required | Description |
|-------|----------|-------------|
| `page` | ✅ | ≥1 |
| `rows` | ✅ | Max 100 |
| `token_symbol` | ❌ | e.g. `BTC` |
| `start_time` | ❌ | Default: 90 days ago |
| `end_time` | ❌ | Default: now |

### Withdrawal History
```
GET /wallet/sapi/withdrawal/his
```
Same params as Deposit History.

### Internal Transfer History
```
GET /wallet/sapi/internal-transfer/his
```
Same params as Deposit History.

### Get Crypto List
```
GET /wallet/sapi/cryptolist?asset=ETH
```
**Response:**
```json
[{
  "asset": "ETH", "decimals": 10,
  "network": "Ethereum Sepolia",
  "withdrawal_fee": "0.0001", "min_withdrawal": "0.0001",
  "is_native": true, "is_tag": false
}]
```

### Create Withdrawal
```
POST /wallet/sapi/withdrawal/create
```
```json
{
  "amount": "0.01", "asset": "ETH",
  "network": "Ethereum", "address": "0x...",
  "tag": null, "remark": null, "timestamp": 1704789520
}
```

### Internal Transfer (to Hata user)
```
POST /wallet/sapi/withdrawal/internal
```
```json
{
  "amount": "0.01", "symbol": "ETH",
  "user_Id": "12345", "to_platform": "MY",
  "email": "user@hata.io", "remark": null,
  "borrowing": false, "timestamp": 1704789520
}
```

### Get Deposit Address
```
POST /wallet/sapi/address/deposit
```
| Field | Required | Description |
|-------|----------|-------------|
| `asset` | ✅ | e.g. `"ETH"` |
| `network` | ✅ | e.g. `"Ethereum"` |

---

## 💵 Fiat (Auth Required)

### Fiat Transaction History
```
GET /fiat/sapi/get-transaction
```
| Param | Required | Description |
|-------|----------|-------------|
| `page` | ✅ | ≥1 |
| `rows` | ✅ | Max 100 |
| `symbol` | ✅ | e.g. `MYR` |
| `action` | ❌ | `deposit` or `withdrawal` |
| `start_time` | ❌ | Default: 90 days ago |
| `end_time` | ❌ | Default: now |

### Fiat Transaction Details
```
GET /fiat/sapi/get-transaction-details?transaction_id=FW-abCdefgHI89631139
```

---

## 🔌 WebSocket

### Connection Flow
1. Get token via REST API (see token endpoints below)
2. Connect to WebSocket URL
3. Send connect message with token
4. Handle ping/pong (respond within 8 seconds)
5. Subscribe to channels

### Token Endpoints
| Endpoint | Type | Platform |
|----------|------|----------|
| `POST /auth/api/v2/ww/user-stream-key` | Public | Global |
| `POST /auth/api/v2/my/user-stream-key` | Public | Malaysia |
| `POST /auth/sapi/v2/ww/user-stream-key` | Private | Global |
| `POST /auth/sapi/v2/my/user-stream-key` | Private | Malaysia |

### Connect
```json
{ "id": 1, "connect": { "token": "CONNECTION_TOKEN" } }
```

### Ping/Pong
Send `{}` back within 8 seconds when receiving `{}`.

### Subscribe to Channel
```json
{ "id": 2, "subscribe": { "channel": "public:BTCMYR@depth" } }
```

### Public Channels
| Channel | Description |
|---------|-------------|
| `{symbol}@depth` | Order book updates |
| `{symbol}@trade` | Real-time trades |
| `{symbol}@candles_1` | 1-min candles |
| `{symbol}@candles_5` | 5-min candles |
| `{symbol}@candles_15` | 15-min candles |
| `{symbol}@candles_30` | 30-min candles |
| `{symbol}@candles_60` | 1-hour candles |
| `{symbol}@candles_240` | 4-hour candles |

### Message Parsing
Messages may be combined with `\n`. Always split by newline and parse each as JSON.

### Depth Event Data
```json
{ "asks": [{"price": "1.0005", "qty": "19.995"}], "bids": [{"price": "1.0001", "qty": "19.995"}] }
```

### Candle Event Data
| Field | Description |
|-------|-------------|
| `t` | Timestamp |
| `o` | Open |
| `h` | High |
| `l` | Low |
| `c` | Close |
| `v` | Volume |

### Trade Event Data
| Field | Description |
|-------|-------------|
| `price` | Execution price |
| `amount` | Total amount (price × qty) |
| `quantity` | Trade quantity |
| `time` | Execution timestamp |
| `trade_id` | Unique trade ID |
| `is_buyer_maker` | Buyer was maker? |

### Private Events (auto-assigned channel `private:{user_id}`)

**newOrder:** Order placed
**cancelOrder:** Order cancelled  
**newTrade:** Trade executed

Private trade fields: `time`, `pair`, `is_buy`, `price`, `qty`, `fee`, `is_maker`, `trade_id`, `order_id`

---

## ⚠️ HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Unauthorized (bad API key/signature) |
| 429 | Rate limited |
| 4XX | Client error (malformed request) |
| 5XX | Server error |

---

## 💡 Tips for Bot Usage
- Use `post_only: "true"` for **0% maker fee**
- Market orders = taker fee applies
- `is_buy` in create order is a **string** (`"true"`/`"false"`), not boolean
- Always sort params alphabetically before signing
- Max open orders per pair: **100**
- Trade history max rows: **100** per page
- Order history max rows: **250** per request
