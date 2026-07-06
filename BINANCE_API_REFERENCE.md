# Binance Futures API Reference

## General API Information
* Some endpoints will require an API Key.
* The base endpoint is: `https://fapi.binance.com`
* All endpoints return either a JSON object or array.
* Data is returned in ascending order. Oldest first, newest last.
* All time and timestamp related fields are in milliseconds.
* All data types adopt definition in JAVA.

## Testnet API Information
* Most of the endpoints can be used in the testnet platform.
* The REST base url for testnet is `https://demo-fapi.binance.com`
* The Websocket base url for testnet is `wss://demo-fstream.binance.com`

## General Information on Endpoints
* For GET endpoints, parameters must be sent as a query string.
* For POST, PUT, and DELETE endpoints, the parameters may be sent as a query string or in the request body with content type `application/x-www-form-urlencoded`. You may mix parameters between both the query string and request body if you wish to do so.
* Parameters may be sent in any order.
* If a parameter sent in both the query string and request body, the query string parameter will be used.

## HTTP Return Codes
* **HTTP 4XX** return codes are used for malformed requests; the issue is on the sender's side.
* **HTTP 403** return code is used when the WAF Limit (Web Application Firewall) has been violated.
* **HTTP 408** return code is used when a timeout has occurred while waiting for a response from the backend server.
* **HTTP 429** return code is used when breaking a request rate limit.
* **HTTP 418** return code is used when an IP has been auto-banned for continuing to send requests after receiving 429 codes.
* **HTTP 5XX** return codes are used for internal errors; the issue is on Binance's side.

### Handling Specific 503 Errors
* **"Request occur unknown error."**: Please retry later.
* **"Unknown error, please check your request or try again later." (Execution status unknown)**: The API successfully sent the request but did not get a response within the timeout period. Do not treat as an immediate failure. Verify via WebSocket updates or orderId queries to avoid duplicates.
* **"Service Unavailable." (Failure)**: This is a failure API operation. The service might be unavailable. Retry with exponential backoff.
* **"Internal error; unable to process your request. Please try again."**: Failure API operation, resend request if needed.
* **"Request throttled by system-level protection. Reduce-only/close-position orders are exempt. Please try again." (-1008)**: System overload, 100% failure. Retry with backoff and reduce concurrency.

## Error Codes and Messages
Any endpoint can return an ERROR. The error payload is as follows:
```json
{
  "code": -1121,
  "msg": "Invalid symbol."
}
```

## LIMITS
* The `/fapi/v1/exchangeInfo` rateLimits array contains objects related to the exchange's `RAW_REQUEST`, `REQUEST_WEIGHT`, and `ORDER` rate limits.
* A 429 will be returned when either rate limit is violated.

### IP Limits
* Every request will contain `X-MBX-USED-WEIGHT-(intervalNum)(intervalLetter)` in the response headers.
* When a 429 is received, back off and do not spam the API.
* Repeatedly violating rate limits leads to an automated IP ban (HTTP status 418), from 2 minutes to 3 days.
* Limits are based on IPs, not API keys.
* WebSocket streams are highly recommended to reduce access restriction pressure.

### Order Rate Limits
* Every order response contains a `X-MBX-ORDER-COUNT-(intervalNum)(intervalLetter)` header.
* The order rate limit is counted against each account.

## Endpoint Security Type
* API-keys are passed into the Rest API via the `X-MBX-APIKEY` header.
* API-keys and secret-keys are case sensitive.

| Security Type | Description |
|---|---|
| `NONE` | Endpoint can be accessed freely. |
| `TRADE` | Endpoint requires sending a valid API-Key and signature. |
| `USER_DATA` | Endpoint requires sending a valid API-Key and signature. |
| `USER_STREAM` | Endpoint requires sending a valid API-Key. |
| `MARKET_DATA` | Endpoint requires sending a valid API-Key. |

## SIGNED (TRADE and USER_DATA) Endpoint Security
* SIGNED endpoints require an additional parameter, `signature`.
* Uses HMAC SHA256 signatures using your `secretKey` as the key and `totalParams` (query string concatenated with request body) as the value.

### Timing Security
* Requires `timestamp` (millisecond timestamp of request creation).
* Optional `recvWindow` (milliseconds after timestamp the request is valid for, defaults to 5000).
* Recommended to use a small `recvWindow` of 5000 or less.

## WebSocket API General Info
* The base endpoint is: `wss://ws-fapi.binance.com/ws-fapi/v1`
* The base endpoint for testnet is: `wss://testnet.binancefuture.com/ws-fapi/v1`
* A single connection is valid for 24 hours; expect disconnection after the 24-hour mark.
* Server sends a ping frame every 3 minutes.
* If the server does not receive a pong frame back within 10 minutes, it disconnects.
* When receiving a ping, you must send a pong with a copy of ping's payload ASAP.
* Unsolicited pong frames are allowed but won't prevent disconnection. Recommended empty payload.
* Signature payload must be generated by taking all request params except signature and sorting them by name alphabetically.
* Lists are returned in chronological order.
* All timestamps are in milliseconds in UTC.
* All field names and values are case-sensitive.
* `INT` parameters (e.g. timestamp) are expected as JSON integers, not strings.
* `DECIMAL` parameters (e.g. price) are expected as JSON strings, not floats.
* User Data Stream requests require a separate WebSocket connection.

### WebSocket API Request Format
* Requests must be sent as JSON in text frames, one request per frame.
* Request `id` is arbitrary (UUIDs, sequential IDs, timestamp, etc.). Avoid using the same ID for concurrent requests.
* Request method names may be prefixed with explicit version (e.g., `v3/order.place`).
* The order of `params` is not significant.

Example Request:
```json
{
  "id": "9ca10e58-7452-467e-9454-f669bb9c764e",
  "method": "order.place",
  "params": {
    "apiKey": "yeqKcXjtA9Eu4Tr3nJk61UJAGzXsEmFqqfVterxpMpR4peNfqE7Zl7oans8Qj089",
    "price": "42088.0",
    "quantity": "0.1",
    "recvWindow": 5000,
    "side": "BUY",
    "signature": "996962a19802b5a09d7bc6ab1524227894533322a2f8a1f8934991689cabf8fe",
    "symbol": "BTCUSDT",
    "timeInForce": "GTC",
    "timestamp": 1705311512994,
    "type": "LIMIT"
  }
}
```

### Response Format
* Responses are returned as JSON in text frames, one response per frame.
* Response fields include `id`, `status`, `result` (if successful), `error` (if failed), and `rateLimits`.

### WebSocket API Rate Limits
* Rate limits are shared with the REST API.
* Handshake attempt costs 5 weight.
* Ping/pong frames limit: max 5 per second.
* Control `rateLimits` visibility with `returnRateLimits` boolean parameter. (e.g., `wss://ws-fapi.binance.com/ws-fapi/v1?returnRateLimits=false`).

### Authentication & Sessions
* Authenticate via `session.logon` using API key (Ed25519 supported), timestamp, and signature.
* After logon, `apiKey` and `signature` can be omitted for future requests.
* Only one API key can be authenticated per connection.
* `session.status`: Check connection status and current API key.
* `session.logout`: Forget the API key previously authenticated.
* Explicit `apiKey` and `signature` on individual requests override the authenticated key (for ad hoc authorization).
* If the API key becomes invalid, the next request revokes the session.

## Public Endpoints Info

### Terminology
* **base asset**: refers to the asset that is the quantity of a symbol.
* **quote asset**: refers to the asset that is the price of a symbol.

### ENUM Definitions

* **Symbol type**: `FUTURE`
* **Contract type (`contractType`)**: `PERPETUAL`, `CURRENT_MONTH`, `NEXT_MONTH`, `CURRENT_QUARTER`, `NEXT_QUARTER`, `PERPETUAL_DELIVERING`
* **Contract status (`contractStatus`, `status`)**: `PENDING_TRADING`, `TRADING`, `PRE_DELIVERING`, `DELIVERING`, `DELIVERED`, `PRE_SETTLE`, `SETTLING`, `CLOSE`
* **Order status (`status`)**: `NEW`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `REJECTED`, `EXPIRED`, `EXPIRED_IN_MATCH`
* **Order types (`orderTypes`, `type`)**: `LIMIT`, `MARKET`, `STOP`, `STOP_MARKET`, `TAKE_PROFIT`, `TAKE_PROFIT_MARKET`, `TRAILING_STOP_MARKET`
* **Order side (`side`)**: `BUY`, `SELL`
* **Position side (`positionSide`)**: `BOTH`, `LONG`, `SHORT`
* **Time in force (`timeInForce`)**:
  * `GTC` - Good Till Cancel (validity is 1 year from placement)
  * `IOC` - Immediate or Cancel
  * `FOK` - Fill or Kill
  * `GTX` - Good Till Crossing (Post Only)
  * `GTD` - Good Till Date
  * `RPI` - Retail Price Improvement (post only, match with APP/Web only)
* **Working Type (`workingType`)**: `MARK_PRICE`, `CONTRACT_PRICE`
* **Response Type (`newOrderRespType`)**: `ACK`, `RESULT`
* **Kline/Candlestick chart intervals**: `1s`, `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`, `1M`
  * s = seconds; m = minutes; h = hours; d = days; w = weeks; M = months
* **STP MODE (`selfTradePreventionMode`)**: `EXPIRE_TAKER`, `EXPIRE_BOTH`, `EXPIRE_MAKER`
* **Price Match (`priceMatch`)**:
  * `NONE` (No price match)
  * `OPPONENT` (counterparty best price)
  * `OPPONENT_5` (5th best price from the counterparty)
  * `OPPONENT_10` (10th best price from the counterparty)
  * `OPPONENT_20` (20th best price from the counterparty)
  * `QUEUE` (best price on the same side)
  * `QUEUE_5` (5th best price on the same side)
  * `QUEUE_10` (10th best price on the same side)
  * `QUEUE_20` (20th best price on the same side)
* **Rate limiters (`rateLimitType`)**: `REQUEST_WEIGHT`, `ORDERS`
* **Rate limit intervals (`interval`)**: `MINUTE`

## Filters
Filters define trading rules on a symbol or an exchange.

### Symbol Filters

#### `PRICE_FILTER`
The `PRICE_FILTER` defines the price rules for a symbol.
```json
{
  "filterType": "PRICE_FILTER",
  "minPrice": "0.00000100",
  "maxPrice": "100000.00000000",
  "tickSize": "0.00000100"
}
```
* `minPrice`: minimum price/stopPrice allowed; disabled on 0.
* `maxPrice`: maximum price/stopPrice allowed; disabled on 0.
* `tickSize`: intervals that a price/stopPrice can be increased/decreased by; disabled on 0.
Rules for enabled values:
* `price >= minPrice`
* `price <= maxPrice`
* `(price-minPrice) % tickSize == 0`

#### `LOT_SIZE`
The `LOT_SIZE` filter defines the quantity (lots) rules for a symbol.
```json
{
  "filterType": "LOT_SIZE",
  "minQty": "0.00100000",
  "maxQty": "100000.00000000",
  "stepSize": "0.00100000"
}
```
* `minQty`: minimum quantity allowed.
* `maxQty`: maximum quantity allowed.
* `stepSize`: intervals that a quantity can be increased/decreased by.
Rules:
* `quantity >= minQty`
* `quantity <= maxQty`
* `(quantity-minQty) % stepSize == 0`

#### `MARKET_LOT_SIZE`
Defines quantity rules specifically for MARKET orders.
```json
{
  "filterType": "MARKET_LOT_SIZE",
  "minQty": "0.00100000",
  "maxQty": "100000.00000000",
  "stepSize": "0.00100000"
}
```
Same rules as `LOT_SIZE`.

#### `MAX_NUM_ORDERS`
Defines the maximum number of orders an account is allowed to have open on a symbol (includes algo and normal orders).
```json
{
  "filterType": "MAX_NUM_ORDERS",
  "limit": 200
}
```

#### `MAX_NUM_ALGO_ORDERS`
Defines the maximum number of all kinds of algo orders open on a symbol. (STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET).
```json
{
  "filterType": "MAX_NUM_ALGO_ORDERS",
  "limit": 100
}
```

#### `PERCENT_PRICE`
Defines valid range for a price based on the mark price.
```json
{
  "filterType": "PERCENT_PRICE",
  "multiplierUp": "1.1500",
  "multiplierDown": "0.8500",
  "multiplierDecimal": 4
}
```
Rules:
* BUY: `price <= markPrice * multiplierUp`
* SELL: `price >= markPrice * multiplierDown`

#### `MIN_NOTIONAL`
Defines the minimum notional value allowed for an order on a symbol (`price * quantity`). For MARKET orders, the mark price is used.
```json
{
  "filterType": "MIN_NOTIONAL",
  "notional": "5.0"
}
```

## Test Connectivity

**API Description:** Test connectivity to the Rest API.

* **HTTP Request:** `GET /fapi/v1/ping`
* **Request Weight:** 1
* **Request Parameters:** NONE

**Response Example:**
```json
{}
```

## Check Server Time

**API Description:** Test connectivity to the Rest API and get the current server time.

* **HTTP Request:** `GET /fapi/v1/time`
* **Request Weight:** 1
* **Request Parameters:** NONE

**Response Example:**
```json
{
  "serverTime": 1499827319559
}
```

## Exchange Information

**API Description:** Current exchange trading rules and symbol information

* **HTTP Request:** `GET /fapi/v1/exchangeInfo`
* **Request Weight:** 1
* **Request Parameters:** NONE

**Response Example:**
```json
{
  "exchangeFilters": [],
  "rateLimits": [
    {
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "rateLimitType": "REQUEST_WEIGHT" 
    },
    {
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 1200,
      "rateLimitType": "ORDERS"
    }
  ],
  "serverTime": 1565613908500,
  "assets": [
    {
      "asset": "BTC",
      "marginAvailable": true,
      "autoAssetExchange": "-0.10"
    },
    {
      "asset": "USDT",
      "marginAvailable": true,
      "autoAssetExchange": "0"
    },
    {
      "asset": "BNB",
      "marginAvailable": false,
      "autoAssetExchange": null
    }
  ],
  "symbols": [
    {
      "symbol": "BLZUSDT",
      "pair": "BLZUSDT",
      "contractType": "PERPETUAL",
      "deliveryDate": 4133404800000,
      "onboardDate": 1598252400000,
      "status": "TRADING",
      "maintMarginPercent": "2.5000",
      "requiredMarginPercent": "5.0000",
      "baseAsset": "BLZ", 
      "quoteAsset": "USDT",
      "marginAsset": "USDT",
      "pricePrecision": 5,
      "quantityPrecision": 0,
      "baseAssetPrecision": 8,
      "quotePrecision": 8, 
      "underlyingType": "COIN",
      "underlyingSubType": ["STORAGE"],
      "settlePlan": 0,
      "triggerProtect": "0.15",
      "filters": [
        {
          "filterType": "PRICE_FILTER",
          "maxPrice": "300",
          "minPrice": "0.0001", 
          "tickSize": "0.0001"
        },
        {
          "filterType": "LOT_SIZE", 
          "maxQty": "10000000",
          "minQty": "1",
          "stepSize": "1"
        },
        {
          "filterType": "MARKET_LOT_SIZE",
          "maxQty": "590119",
          "minQty": "1",
          "stepSize": "1"
        },
        {
          "filterType": "MAX_NUM_ORDERS",
          "limit": 200
        },
        {
          "filterType": "MIN_NOTIONAL",
          "notional": "5.0"
        },
        {
          "filterType": "PERCENT_PRICE",
          "multiplierUp": "1.1500",
          "multiplierDown": "0.8500",
          "multiplierDecimal": "4"
        }
      ],
      "orderTypes": [
        "LIMIT",
        "MARKET",
        "STOP",
        "STOP_MARKET",
        "TAKE_PROFIT",
        "TAKE_PROFIT_MARKET",
        "TRAILING_STOP_MARKET" 
      ],
      "timeInForce": [
        "GTC", 
        "IOC", 
        "FOK", 
        "GTX" 
      ],
      "liquidationFee": "0.010000",
      "marketTakeBound": "0.30"
    }
  ],
  "timezone": "UTC" 
}
```

## Delist Schedule

**API Description:** The Futures team will update the `deliveryDate` in the `GET /fapi/v1/exchangeInfo` endpoint to the delisting time after the delisting announcement is published. Please refer to Exchange Info to check the delisting information of contract trading pairs in advance.

## Order Book

**API Description:** Query symbol orderbook

* **HTTP Request:** `GET /fapi/v1/depth`
* **Note:** Retail Price Improvement (RPI) orders are not visible and excluded in the response message.
* **Request Weight:** Adjusted based on the limit
  * Limits: `5, 10, 20, 50` = `2`
  * Limit: `100` = `5`
  * Limit: `500` = `10`
  * Limit: `1000` = `20`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `limit` | `INT` | NO | Default 500; Valid limits: `[5, 10, 20, 50, 100, 500, 1000]` |

### Response Example
```json
{
  "lastUpdateId": 1027024,
  "E": 1589436922972,   // Message output time
  "T": 1589436922959,   // Transaction time
  "bids": [
    [
      "4.00000000",     // PRICE
      "431.00000000"    // QTY
    ]
  ],
  "asks": [
    [
      "4.00000200",
      "12.00000000"
    ]
  ]
}
```

## RPI Order Book

**API Description:** Query symbol orderbook with RPI orders

* **HTTP Request:** `GET /fapi/v1/rpiDepth`
* **Note:** RPI(Retail Price Improvement) orders are included and aggreated in the response message. Crossed price levels are hidden and invisible.
* **Request Weight:** Adjusted based on the limit:
  * Limit `1000` = `20`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `limit` | `INT` | NO | Default 1000; Valid limits: `[1000]` |

### Response Example
```json
{
  "lastUpdateId": 1027024,
  "E": 1589436922972,   // Message output time
  "T": 1589436922959,   // Transaction time
  "bids": [
    [
      "4.00000000",     // PRICE
      "431.00000000"    // QTY
    ]
  ],
  "asks": [
    [
      "4.00000200",
      "12.00000000"
    ]
  ]
}
```

## Recent Trades List

**API Description:** Get recent market trades

* **HTTP Request:** `GET /fapi/v1/trades`
* **Request Weight:** 5

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `limit` | `INT` | NO | Default 500; max 1000. |

> **Note:** Market trades means trades filled in the order book. Only market trades will be returned, which means the insurance fund trades and ADL trades won't be returned.

### Response Example
```json
[
  {
    "id": 28457,
    "price": "4.00000100",
    "qty": "12.00000000",
    "quoteQty": "48.00",
    "time": 1499865549590,
    "isBuyerMaker": true,
    "isRPITrade": true
  }
]
```

## Old Trades Lookup (MARKET_DATA)

**API Description:** Get older market historical trades.

* **HTTP Request:** `GET /fapi/v1/historicalTrades`
* **Request Weight:** 20

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `limit` | `INT` | NO | Default 100; max 500. |
| `fromId` | `LONG` | NO | TradeId to fetch from. Default gets most recent trades. |

> **Note:** Market trades means trades filled in the order book. Only market trades will be returned, which means the insurance fund trades and ADL trades won't be returned. Only supports data from within the last one month.

### Response Example
```json
[
  {
    "id": 28457,
    "price": "4.00000100",
    "qty": "12.00000000",
    "quoteQty": "8000.00",
    "time": 1499865549590,
    "isBuyerMaker": true,
    "isRPITrade": true
  }
]
```

## Compressed/Aggregate Trades List

**API Description:** Get compressed, aggregate market trades. Market trades that fill in 100ms with the same price and the same taking side will have the quantity aggregated.

* **HTTP Request:** `GET /fapi/v1/aggTrades`
* **Note:** Retail Price Improvement (RPI) orders are aggregated and without special tags to be distinguished.
* **Request Weight:** 20

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `fromId` | `LONG` | NO | ID to get aggregate trades from INCLUSIVE. |
| `startTime` | `LONG` | NO | Timestamp in ms to get aggregate trades from INCLUSIVE. |
| `endTime` | `LONG` | NO | Timestamp in ms to get aggregate trades until INCLUSIVE. |
| `limit` | `INT` | NO | Default 500; max 1000. |

> **Notes:**
> * Support querying futures trade histories that are not older than 24 hours
> * If both `startTime` and `endTime` are sent, time between `startTime` and `endTime` must be less than 1 hour.
> * If `fromId`, `startTime`, and `endTime` are not sent, the most recent aggregate trades will be returned.
> * Only market trades will be aggregated and returned, which means the insurance fund trades and ADL trades won't be aggregated.
> * Sending both `startTime`/`endTime` and `fromId` might cause response timeout, please send either `fromId` or `startTime`/`endTime`.

### Response Example
```json
[
  {
    "a": 26129,         // Aggregate tradeId
    "p": "0.01633102",  // Price
    "q": "4.70443515",  // Quantity
    "nq": "100",        // Normal quantity without the trades involving RPI orders
    "f": 27781,         // First tradeId
    "l": 27781,         // Last tradeId
    "T": 1498793709153, // Timestamp
    "m": true           // Was the buyer the maker?
  }
]
```

## Kline/Candlestick Data

**API Description:** Kline/candlestick bars for a symbol. Klines are uniquely identified by their open time.

* **HTTP Request:** `GET /fapi/v1/klines`
* **Request Weight:** based on parameter LIMIT
  * `[1, 100)` = `1`
  * `[100, 500)` = `2`
  * `[500, 1000]` = `5`
  * `> 1000` = `10`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | After CM migration, accepts both UM and CM symbols. |
| `interval` | `ENUM` | YES | |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |
| `limit` | `INT` | NO | Default 500; max 1500. |

> **Note:** If `startTime` and `endTime` are not sent, the most recent klines are returned.

### Response Example
```json
[
  [
    1499040000000,      // Open time
    "0.01634790",       // Open
    "0.80000000",       // High
    "0.01575800",       // Low
    "0.01577100",       // Close
    "148976.11427815",  // Volume
    1499644799999,      // Close time
    "2434.19055334",    // Quote asset volume
    308,                // Number of trades
    "1756.87402397",    // Taker buy base asset volume
    "28.46694368",      // Taker buy quote asset volume
    "17928899.62484339" // Ignore.
  ]
]
```

## Continuous Contract Kline/Candlestick Data

**API Description:** Kline/candlestick bars for a specific contract type. Klines are uniquely identified by their open time.

* **HTTP Request:** `GET /fapi/v1/continuousKlines`
* **Request Weight:** based on parameter LIMIT
  * `[1, 100)` = `1`
  * `[100, 500)` = `2`
  * `[500, 1000]` = `5`
  * `> 1000` = `10`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `pair` | `STRING` | YES | After CM migration, accepts both UM and CM pair values. |
| `contractType` | `ENUM` | YES | `PERPETUAL`, `CURRENT_QUARTER`, `NEXT_QUARTER`, `TRADIFI_PERPETUAL` |
| `interval` | `ENUM` | YES | |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |
| `limit` | `INT` | NO | Default 500; max 1500. |

> **Note:** If `startTime` and `endTime` are not sent, the most recent klines are returned.

### Response Example
```json
[
  [
    1607444700000,      // Open time
    "18879.99",         // Open
    "18900.00",         // High
    "18878.98",         // Low
    "18896.13",         // Close (or latest price)
    "492.363",          // Volume
    1607444759999,      // Close time
    "9302145.66080",    // Quote asset volume
    1874,               // Number of trades
    "385.983",          // Taker buy volume
    "7292402.33267",    // Taker buy quote asset volume
    "0"                 // Ignore.
  ]
]
```

## Index Price Kline/Candlestick Data

**API Description:** Kline/candlestick bars for the index price of a pair. Klines are uniquely identified by their open time.

* **HTTP Request:** `GET /fapi/v1/indexPriceKlines`
* **Request Weight:** based on parameter LIMIT
  * `[1, 100)` = `1`
  * `[100, 500)` = `2`
  * `[500, 1000]` = `5`
  * `> 1000` = `10`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `pair` | `STRING` | YES | After CM migration, accepts both UM and CM pair values. |
| `interval` | `ENUM` | YES | |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |
| `limit` | `INT` | NO | Default 500; max 1500. |

> **Note:** If `startTime` and `endTime` are not sent, the most recent klines are returned.

### Response Example
```json
[
  [
    1591256400000,      // Open time
    "9653.69440000",    // Open
    "9653.69640000",    // High
    "9651.38600000",    // Low
    "9651.55200000",    // Close (or latest price)
    "0",                // Ignore
    1591256459999,      // Close time
    "0",                // Ignore
    60,                 // Ignore
    "0",                // Ignore
    "0"                 // Ignore
  ]
]
```

## Mark Price Kline/Candlestick Data

**API Description:** Kline/candlestick bars for the mark price of a symbol. Klines are uniquely identified by their open time.

* **HTTP Request:** `GET /fapi/v1/markPriceKlines`
* **Request Weight:** based on parameter LIMIT
  * `[1, 100)` = `1`
  * `[100, 500)` = `2`
  * `[500, 1000]` = `5`
  * `> 1000` = `10`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | After CM migration, accepts both UM and CM symbols. |
| `interval` | `ENUM` | YES | |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |
| `limit` | `INT` | NO | Default 500; max 1500. |

> **Note:** If `startTime` and `endTime` are not sent, the most recent klines are returned.

### Response Example
```json
[
  [
    1591256460000,          // Open time
    "9653.29201333",        // Open
    "9654.56401333",        // High
    "9653.07367333",        // Low
    "9653.07367333",        // Close (or latest price)
    "0",                    // Ignore
    1591256519999,          // Close time
    "0",                    // Ignore
    60,                     // Ignore
    "0",                    // Ignore
    "0",                    // Ignore
    "0"                     // Ignore
  ]
]
```

## Premium index Kline Data

**API Description:** Premium index kline bars of a symbol. Klines are uniquely identified by their open time.

* **HTTP Request:** `GET /fapi/v1/premiumIndexKlines`
* **Request Weight:** based on parameter LIMIT
  * `[1, 100)` = `1`
  * `[100, 500)` = `2`
  * `[500, 1000]` = `5`
  * `> 1000` = `10`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | After CM migration, accepts both UM and CM symbols. |
| `interval` | `ENUM` | YES | |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |
| `limit` | `INT` | NO | Default 500; max 1500. |

> **Note:** If `startTime` and `endTime` are not sent, the most recent klines are returned.

### Response Example
```json
[
  [
    1691603820000,          // Open time
    "-0.00042931",          // Open
    "-0.00023641",          // High
    "-0.00059406",          // Low
    "-0.00043659",          // Close
    "0",                    // Ignore
    1691603879999,          // Close time
    "0",                    // Ignore
    12,                     // Ignore
    "0",                    // Ignore
    "0",                    // Ignore
    "0"                     // Ignore
  ]
]
```

## Mark Price

**API Description:** Mark Price and Funding Rate

* **HTTP Request:** `GET /fapi/v1/premiumIndex`
* **Request Weight:** 1 with symbol, 10 without symbol

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | |

### Response Example
Response (with symbol):
```json
{
  "symbol": "BTCUSDT",
  "markPrice": "11793.63104562",          // mark price
  "indexPrice": "11781.80495970",         // index price
  "estimatedSettlePrice": "11781.16138815", // Estimated Settle Price, only useful in the last hour before the settlement starts.
  "lastFundingRate": "0.00038246",        // This is the Latest funding rate
  "interestRate": "0.00010000",
  "nextFundingTime": 1597392000000,
  "time": 1597370495002
}
```

Response (when symbol not sent):
```json
[
  {
    "symbol": "BTCUSDT",
    "markPrice": "11793.63104562",
    "indexPrice": "11781.80495970",
    "estimatedSettlePrice": "11781.16138815",
    "lastFundingRate": "0.00038246",
    "interestRate": "0.00010000",
    "nextFundingTime": 1597392000000,
    "time": 1597370495002
  }
]
```

## Get Funding Rate History

**API Description:** Get Funding Rate History

* **HTTP Request:** `GET /fapi/v1/fundingRate`
* **Request Weight:** share 500/5min/IP rate limit with `GET /fapi/v1/fundingInfo`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | |
| `startTime` | `LONG` | NO | Timestamp in ms to get funding rate from INCLUSIVE. |
| `endTime` | `LONG` | NO | Timestamp in ms to get funding rate until INCLUSIVE. |
| `limit` | `INT` | NO | Default 100; max 1000 |

> **Notes:**
> * If `startTime` and `endTime` are not sent, the most recent 200 records are returned.
> * If the number of data between `startTime` and `endTime` is larger than limit, return as `startTime + limit`.
> * In ascending order.

### Response Example
```json
[
  {
    "symbol": "BTCUSDT",
    "fundingRate": "-0.03750000",
    "fundingTime": 1570608000000,
    "markPrice": "34287.54619963"   // mark price associated with a particular funding fee charge
  },
  {
    "symbol": "BTCUSDT",
    "fundingRate": "0.00010000",
    "fundingTime": 1570636800000,
    "markPrice": "34287.54619963" 
  }
]
```

## Get Funding Rate Info

**API Description:** Query funding rate info for symbols that had FundingRateCap/ FundingRateFloor / fundingIntervalHours adjustment

* **HTTP Request:** `GET /fapi/v1/fundingInfo`
* **Request Weight:** 0
  * Share 500/5min/IP rate limit with `GET /fapi/v1/fundingRate`

### Response Example
```json
[
  {
    "symbol": "BLZUSDT",
    "adjustedFundingRateCap": "0.02500000",
    "adjustedFundingRateFloor": "-0.02500000",
    "fundingIntervalHours": 8,
    "disclaimer": false   // ignore
  }
]
```

## 24hr Ticker Price Change Statistics

**API Description:** 24 hour rolling window price change statistics. Careful when accessing this with no symbol.

* **HTTP Request:** `GET /fapi/v1/ticker/24hr`
* **Request Weight:**
  * 1 for a single symbol
  * 40 when the symbol parameter is omitted

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | If the symbol is not sent, tickers for all symbols will be returned in an array. |

### Response Example
Response:
```json
{
  "symbol": "BTCUSDT",
  "priceChange": "-94.99999800",
  "priceChangePercent": "-95.960",
  "weightedAvgPrice": "0.29628482",
  "lastPrice": "4.00000200",
  "lastQty": "200.00000000",
  "openPrice": "99.00000000",
  "highPrice": "100.00000000",
  "lowPrice": "0.10000000",
  "volume": "8913.30000000",
  "quoteVolume": "15.30000000",
  "openTime": 1499783499040,
  "closeTime": 1499869899040,
  "firstId": 28385,   // First tradeId
  "lastId": 28460,    // Last tradeId
  "count": 76         // Trade count
}
```

Response (array):
```json
[
  {
    "symbol": "BTCUSDT",
    "priceChange": "-94.99999800",
    "priceChangePercent": "-95.960",
    "weightedAvgPrice": "0.29628482",
    "lastPrice": "4.00000200",
    "lastQty": "200.00000000",
    "openPrice": "99.00000000",
    "highPrice": "100.00000000",
    "lowPrice": "0.10000000",
    "volume": "8913.30000000",
    "quoteVolume": "15.30000000",
    "openTime": 1499783499040,
    "closeTime": 1499869899040,
    "firstId": 28385,   // First tradeId
    "lastId": 28460,    // Last tradeId
    "count": 76         // Trade count
  }
]
```

## Symbol Price Ticker (Deprecated)

**API Description:** Latest price for a symbol or symbols.

* **HTTP Request:** `GET /fapi/v1/ticker/price`
* **Request Weight:**
  * 1 for a single symbol
  * 2 when the symbol parameter is omitted

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | If the symbol is not sent, prices for all symbols will be returned in an array. |

### Response Example
```json
{
  "symbol": "BTCUSDT",
  "price": "6000.01",
  "time": 1589437530011   // Transaction time
}
```

## Symbol Price Ticker V2

**API Description:** Latest price for a symbol or symbols.

* **HTTP Request:** `GET /fapi/v2/ticker/price`
* **Request Weight:**
  * 1 for a single symbol
  * 2 when the symbol parameter is omitted

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | If the symbol is not sent, prices for all symbols will be returned in an array. |

> **Note:** The field `X-MBX-USED-WEIGHT-1M` in response header is not accurate from this endpoint, please ignore.

### Response Example
```json
{
  "symbol": "BTCUSDT",
  "price": "6000.01",
  "time": 1589437530011   // Transaction time
}
```

## Symbol Order Book Ticker

**API Description:** Best price/qty on the order book for a symbol or symbols.

* **HTTP Request:** `GET /fapi/v1/ticker/bookTicker`
* **Note:** Retail Price Improvement(RPI) orders are not visible and excluded in the response message.
* **Request Weight:**
  * 2 for a single symbol
  * 5 when the symbol parameter is omitted

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | If the symbol is not sent, bookTickers for all symbols will be returned in an array. |

> **Note:** The field `X-MBX-USED-WEIGHT-1M` in response header is not accurate from this endpoint, please ignore.

### Response Example
```json
{
  "symbol": "BTCUSDT",
  "bidPrice": "4.00000000",
  "bidQty": "431.00000000",
  "askPrice": "4.00000200",
  "askQty": "9.00000000",
  "time": 1589437530011   // Transaction time
}
```

## Quarterly Contract Settlement Price

**API Description:** Latest price for a symbol or symbols.

* **HTTP Request:** `GET /futures/data/delivery-price`
* **Request Weight:** 0

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `pair` | `STRING` | YES | e.g BTCUSDT |

### Response Example
```json
[
  {
    "deliveryTime": 1695945600000,
    "deliveryPrice": 27103.00000000
  },
  {
    "deliveryTime": 1688083200000,
    "deliveryPrice": 30733.60000000
  },
  {
    "deliveryTime": 1680220800000,
    "deliveryPrice": 27814.20000000
  },
  {
    "deliveryTime": 1648166400000,
    "deliveryPrice": 44066.30000000
  }
]
```

## Open Interest

**API Description:** Get present open interest of a specific symbol.

* **HTTP Request:** `GET /fapi/v1/openInterest`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |

### Response Example
```json
{
  "openInterest": "10659.509", 
  "symbol": "BTCUSDT",
  "time": 1589437530011   // Transaction time
}
```

## Open Interest Statistics

**API Description:** Open Interest Statistics

* **HTTP Request:** `GET /futures/data/openInterestHist`
* **Request Weight:** 0

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `period` | `ENUM` | YES | `"5m"`,`"15m"`,`"30m"`,`"1h"`,`"2h"`,`"4h"`,`"6h"`,`"12h"`,`"1d"` |
| `limit` | `LONG` | NO | default 30, max 500 |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |

> **Notes:**
> * If `startTime` and `endTime` are not sent, the most recent data is returned.
> * Only the data of the latest 1 month is available.
> * IP rate limit 1000 requests/5min

### Response Example
```json
[
  { 
    "symbol":"BTCUSDT",
    "sumOpenInterest":"20403.63700000",  // total open interest 
    "sumOpenInterestValue": "150570784.07809979",   // total open interest value
    "CMCCirculatingSupply": "165880.538", // circulating supply provided by CMC
    "timestamp":"1583127900000"
  },     
  { 
    "symbol":"BTCUSDT",
    "sumOpenInterest":"20401.36700000",
    "sumOpenInterestValue":"149940752.14464448",
    "CMCCirculatingSupply": "165900.14853",
    "timestamp":"1583128200000"    
  }   
]
```

## Top Trader Long/Short Ratio (Positions)

**API Description:** The proportion of net long and net short positions to total open positions of the top 20% users with the highest margin balance. 
* Long Position % = Long positions of top traders / Total open positions of top traders 
* Short Position % = Short positions of top traders / Total open positions of top traders 
* Long/Short Ratio (Positions) = Long Position % / Short Position %

* **HTTP Request:** `GET /futures/data/topLongShortPositionRatio`
* **Request Weight:** 0

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `period` | `ENUM` | YES | `"5m"`,`"15m"`,`"30m"`,`"1h"`,`"2h"`,`"4h"`,`"6h"`,`"12h"`,`"1d"` |
| `limit` | `LONG` | NO | default 30, max 500 |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |

> **Notes:**
> * If `startTime` and `endTime` are not sent, the most recent data is returned.
> * Only the data of the latest 30 days is available.
> * IP rate limit 1000 requests/5min

### Response Example
```json
[
  { 
    "symbol":"BTCUSDT",
    "longShortRatio":"1.4342",// long/short position ratio of top traders
    "longAccount": "0.5891", // long positions ratio of top traders
    "shortAccount":"0.4108", // short positions ratio of top traders
    "timestamp":"1583139600000"
  },
  {
    "symbol":"BTCUSDT",
    "longShortRatio":"1.4337",
    "longAccount": "0.3583", 
    "shortAccount":"0.6417", 	                
    "timestamp":"1583139900000"
  }   
]
```

## Top Trader Long/Short Ratio (Accounts)

**API Description:** The proportion of net long and net short accounts to total accounts of the top 20% users with the highest margin balance. Each account is counted once only. 
* Long Account % = Accounts of top traders with net long positions / Total accounts of top traders with open positions 
* Short Account % = Accounts of top traders with net short positions / Total accounts of top traders with open positions 
* Long/Short Ratio (Accounts) = Long Account % / Short Account %

* **HTTP Request:** `GET /futures/data/topLongShortAccountRatio`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `period` | `ENUM` | YES | `"5m"`,`"15m"`,`"30m"`,`"1h"`,`"2h"`,`"4h"`,`"6h"`,`"12h"`,`"1d"` |
| `limit` | `LONG` | NO | default 30, max 500 |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |

> **Notes:**
> * If `startTime` and `endTime` are not sent, the most recent data is returned.
> * Only the data of the latest 30 days is available.
> * IP rate limit 1000 requests/5min

### Response Example
```json
[
  { 
    "symbol":"BTCUSDT",
    "longShortRatio":"1.8105",  // long/short account num ratio of top traders
    "longAccount": "0.6442",   // long account num ratio of top traders 
    "shortAccount":"0.3558",   // long account num ratio of top traders 
    "timestamp":"1583139600000"
  }, 
  {     
    "symbol":"BTCUSDT",
    "longShortRatio":"0.5576",
    "longAccount": "0.3580", 
    "shortAccount":"0.6420", 	                
    "timestamp":"1583139900000"         
  }  
]
```

## Long/Short Ratio

**API Description:** Query symbol Long/Short Ratio

* **HTTP Request:** `GET /futures/data/globalLongShortAccountRatio`
* **Request Weight:** 0

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `period` | `ENUM` | YES | `"5m"`,`"15m"`,`"30m"`,`"1h"`,`"2h"`,`"4h"`,`"6h"`,`"12h"`,`"1d"` |
| `limit` | `LONG` | NO | default 30, max 500 |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |

> **Notes:**
> * If `startTime` and `endTime` are not sent, the most recent data is returned.
> * Only the data of the latest 30 days is available.
> * IP rate limit 1000 requests/5min

### Response Example
```json
[
  { 
    "symbol":"BTCUSDT",  // long/short account num ratio of all traders
    "longShortRatio":"0.1960",  //long account num ratio of all traders
    "longAccount": "0.6622",   // short account num ratio of all traders
    "shortAccount":"0.3378", 
    "timestamp":"1583139600000"
  },
  {
    "symbol":"BTCUSDT",
    "longShortRatio":"1.9559",
    "longAccount": "0.6617", 
    "shortAccount":"0.3382", 	                
    "timestamp":"1583139900000"
  }   
]
```

## Taker Buy/Sell Volume

**API Description:** Taker Buy/Sell Volume

* **HTTP Request:** `GET /futures/data/takerlongshortRatio`
* **Request Weight:** 0

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `period` | `ENUM` | YES | `"5m"`,`"15m"`,`"30m"`,`"1h"`,`"2h"`,`"4h"`,`"6h"`,`"12h"`,`"1d"` |
| `limit` | `LONG` | NO | default 30, max 500 |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |

> **Notes:**
> * If `startTime` and `endTime` are not sent, the most recent data is returned.
> * Only the data of the latest 30 days is available.
> * IP rate limit 1000 requests/5min

### Response Example
```json
[
  { 
    "buySellRatio":"1.5586",
    "buyVol": "387.3300", 
    "sellVol":"248.5030", 
    "timestamp":"1585614900000"
  },
  { 
    "buySellRatio":"1.3104",
    "buyVol": "343.9290", 
    "sellVol":"248.5030", 	                
    "timestamp":"1583139900000"        
  }    
]
```

## Basis

**API Description:** Query future basis

* **HTTP Request:** `GET /futures/data/basis`
* **Request Weight:** 0

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `pair` | `STRING` | YES | BTCUSDT |
| `contractType` | `ENUM` | YES | `CURRENT_QUARTER`, `NEXT_QUARTER`, `PERPETUAL` |
| `period` | `ENUM` | YES | `"5m"`,`"15m"`,`"30m"`,`"1h"`,`"2h"`,`"4h"`,`"6h"`,`"12h"`,`"1d"` |
| `limit` | `LONG` | NO | Default 30, Max 500 |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |

> **Notes:**
> * If `startTime` and `endTime` are not sent, the most recent data is returned.
> * Only the data of the latest 30 days is available.

### Response Example
```json
[  
  {
    "indexPrice": "34400.15945055",
    "contractType": "PERPETUAL",
    "basisRate": "0.0004",
    "futuresPrice": "34414.10",
    "annualizedBasisRate": "",
    "basis": "13.94054945",
    "pair": "BTCUSDT",
    "timestamp": 1698742800000
  }
]
```

## Composite Index Symbol Information

**API Description:** Query composite index symbol information

* **HTTP Request:** `GET /fapi/v1/indexInfo`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | Only for composite index symbols |

### Response Example
```json
[
  { 
    "symbol": "DEFIUSDT",
    "time": 1589437530011,    // Current time
    "component": "baseAsset", //Component asset
    "baseAssetList":[
      {
        "baseAsset":"BAL",
        "quoteAsset": "USDT",
        "weightInQuantity":"1.04406228",
        "weightInPercentage":"0.02783900"
      },
      {
        "baseAsset":"BAND",
        "quoteAsset": "USDT",
        "weightInQuantity":"3.53782729",
        "weightInPercentage":"0.03935200"
      }
    ]
  }
]
```

## Asset Index

**CM-UM Integration (Effective 2026-06-30):** Renamed from Multi-Assets Mode Asset Index. The response now additionally pushes COIN-M settlement-asset price index entries (e.g., BTCUSD, ETHUSD, BNBUSD). The endpoint path `/fapi/v1/assetIndex` is unchanged.

**API Description:** Asset index price.

* **HTTP Request:** `GET /fapi/v1/assetIndex`
* **Request Weight:** 1 for a single symbol; 10 when the symbol parameter is omitted

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | Asset pair |

### Response Example
Response (with symbol):
```json
{
  "symbol": "ADAUSD",
  "time": 1635740268004,
  "index": "1.92957370",
  "bidBuffer": "0.10000000", 
  "askBuffer": "0.10000000", 
  "bidRate": "1.73661633",
  "askRate": "2.12253107",
  "autoExchangeBidBuffer": "0.05000000",
  "autoExchangeAskBuffer": "0.05000000",
  "autoExchangeBidRate": "1.83309501",
  "autoExchangeAskRate": "2.02605238"
}
```

Response (without symbol):
```json
[
  {
    "symbol": "ADAUSD",
    "time": 1635740268004,
    "index": "1.92957370",
    "bidBuffer": "0.10000000", 
    "askBuffer": "0.10000000", 
    "bidRate": "1.73661633",
    "askRate": "2.12253107",
    "autoExchangeBidBuffer": "0.05000000",
    "autoExchangeAskBuffer": "0.05000000",
    "autoExchangeBidRate": "1.83309501",
    "autoExchangeAskRate": "2.02605238"
  }
]
```
