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

## Query Index Price Constituents

**API Description:** Query index price constituents

* **HTTP Request:** `GET /fapi/v1/constituents`
* **Request Weight:** 2
* **Note:** Prices from constituents of TradFi perps will be hidden and displayed as -1.

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |

### Response Example
```json
{
  "symbol": "BTCUSDT",
  "time": 1745401553408,
  "constituents": [
    {
      "exchange": "binance",
      "symbol": "BTCUSDT",
      "price": "94057.03000000",
      "weight": "0.51282051"
    },
    {
      "exchange": "coinbase",
      "symbol": "BTC-USDT",
      "price": "94140.58000000",
      "weight": "0.15384615"
    },
    {
      "exchange": "gateio",
      "symbol": "BTC_USDT",
      "price": "94060.10000000",
      "weight": "0.02564103"
    },
    {
      "exchange": "kucoin",
      "symbol": "BTC-USDT",
      "price": "94096.70000000",
      "weight": "0.07692308"
    },
    {
      "exchange": "mxc",
      "symbol": "BTCUSDT",
      "price": "94057.02000000",
      "weight": "0.07692308"
    },
    {
      "exchange": "bitget",
      "symbol": "BTCUSDT",
      "price": "94064.03000000",
      "weight": "0.07692308"
    },
    {
      "exchange": "bybit",
      "symbol": "BTCUSDT",
      "price": "94067.90000000",
      "weight": "0.07692308"
    }
  ]
}
```

## Query Insurance Fund Balance Snapshot

**API Description:** Query Insurance Fund Balance Snapshot

* **HTTP Request:** `GET /fapi/v1/insuranceBalance`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | |

### Response Example
Response (pass symbol):
```json
{
  "symbols":[
    "BNBUSDT",
    "BTCUSDT",
    "BTCUSDT_250627",
    "BTCUSDT_250926",
    "ETHBTC",
    "ETHUSDT",
    "ETHUSDT_250627",
    "ETHUSDT_250926"
  ],
  "assets":[
    {
      "asset":"USDC",
      "marginBalance":"299999998.6497832",
      "updateTime":1745366402000
    },
    {
      "asset":"USDT",
      "marginBalance":"793930579.315848",
      "updateTime":1745366402000
    },
    {
      "asset":"BTC",
      "marginBalance":"61.73143554",
      "updateTime":1745366402000
    },
    {
      "asset":"BNFCR",
      "marginBalance":"633223.99396922",
      "updateTime":1745366402000
    }
  ]
}
```

Response (not pass symbol):
```json
[
  {
    "symbols":[
      "ADAUSDT",
      "BCHUSDT",
      "DOTUSDT",
      "EOSUSDT",
      "ETCUSDT",
      "LINKUSDT",
      "LTCUSDT",
      "TRXUSDT",
      "XLMUSDT",
      "XMRUSDT",
      "XRPUSDT"
    ],
    "assets":[
      {
        "asset":"USDT",
        "marginBalance":"314151411.06482935",
        "updateTime":1745366402000
      }
    ]
  },
  {
    "symbols":[
      "ACTUSDT",
      "MUBARAKUSDT",
      "OMUSDT",
      "TSTUSDT"
    ],
    "assets":[
      {
        "asset":"USDT",
        "marginBalance":"5166686.84431694",
        "updateTime":1745366402000
      }
    ]
  }
]
```

## ADL Risk

**API Description:** Query the symbol-level ADL risk rating. The ADL risk rating measures the likelihood of ADL during liquidation, and the rating takes into account the insurance fund balance, position concentration on the symbol, order book depth, price volatility, average leverage, unrealized PnL, and margin utilization at the symbol level. The rating can be high, medium and low, and is updated every 30 minutes.

* **HTTP Request:** `GET /fapi/v1/symbolAdlRisk`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | |

### Response Example
Response (with symbol):
```json
{
  "symbol": "BTCUSDT",
  "adlRisk": "low",  // ADL Risk rating
  "updateTime": 1597370495002
}
```

Response (when symbol not sent):
```json
[
  {
    "symbol": "BTCUSDT",
    "adlRisk": "low",  // ADL Risk rating
    "updateTime": 1597370495002
  },
  {
    "symbol": "ETHUSDT",
    "adlRisk": "high", // ADL Risk rating
    "updateTime": 1597370495004
  }
]
```

## Trading Schedule

**API Description:** Trading session schedules for the underlying assets of TradFi Perps are provided for a one-week period forward and one-week period backward starting from the day prior to the query time, covering the U.S. equity market, Korean equity market and the commodity market.

**Session types per market:**
* U.S. equity market: `"PRE_MARKET"`, `"REGULAR"`, `"AFTER_MARKET"`, `"OVERNIGHT"`, `"NO_TRADING"`.
* Commodity market: `"REGULAR"`, `"NO_TRADING"`.
* Korean equity market: `"REGULAR"`, `"NO_TRADING"`.

* **HTTP Request:** `GET /fapi/v1/tradingSchedule`
* **Request Weight:** 5

### Request Parameters
* NONE

### Response Example
```json
{
  "updateTime": 1761286643918,
  "marketSchedules": {
    "EQUITY": {
      "sessions": [
        {
          "startTime": 1761177600000,
          "endTime": 1761206400000,
          "type": "OVERNIGHT"
        },
        {
          "startTime": 1761206400000,
          "endTime": 1761226200000,
          "type": "PRE_MARKET"
        }
      ]
    },
    "COMMODITY": {
      "sessions": [
        {
          "startTime": 1761724800000,
          "endTime": 1761744600000,
          "type": "NO_TRADING"
        },
        {
          "startTime": 1761744600000,
          "endTime": 1761768000000,
          "type": "REGULAR"
        }
      ]
    },
    "KR_EQUITY": {
      "sessions": [
        {
          "startTime": 1779958800000,
          "endTime": 1780009200000,
          "type": "NO_TRADING"
        },
        {
          "startTime": 1780009200000,
          "endTime": 1780030800000,
          "type": "REGULAR"
        }
      ]
    }
  }
}
```

## Order Book

**API Description:** Get current order book. Note that this request returns limited market depth. If you need to continuously monitor order book updates, please consider using Websocket Market Streams:
* `<symbol>@depth<levels>`
* `<symbol>@depth`

You can use depth request together with `<symbol>@depth` streams to maintain a local order book.

* **Method:** `depth`
* **Note:** Retail Price Improvement(RPI) orders are not visible and excluded in the response message.

### Request Example
```json
{
    "id": "51e2affb-0aba-4821-ba75-f2625006eb43",
    "method": "depth",
    "params": {
      "symbol": "BTCUSDT"
    }
}
```

* **Request Weight:** Adjusted based on the limit:
  * 5, 10, 20, 50 = `2`
  * 100 = `5`
  * 500 = `10`
  * 1000 = `20`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `limit` | `INT` | NO | Default 500; Valid limits:[5, 10, 20, 50, 100, 500, 1000] |

### Response Example
```json
{
  "id": "51e2affb-0aba-4821-ba75-f2625006eb43",
  "status": 200,
  "result": {
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
  },
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 5
    }
  ]
}
```

## Symbol Price Ticker

**API Description:** Latest price for a symbol or symbols.

* **Method:** `ticker.price`

### Request Example
```json
{
    "id": "9d32157c-a556-4d27-9866-66760a174b57",
    "method": "ticker.price",
    "params": {
        "symbol": "BTCUSDT"
    }
}
```

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
  "id": "9d32157c-a556-4d27-9866-66760a174b57",
  "status": 200,
  "result": {
    "symbol": "BTCUSDT",
    "price": "6000.01",
    "time": 1589437530011   // Transaction time
  },
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 2
    }
  ]
}
```

OR (array)
```json
{
  "id": "9d32157c-a556-4d27-9866-66760a174b57",
  "status": 200,
  "result": [
    {
      "symbol": "BTCUSDT",
      "price": "6000.01",
      "time": 1589437530011
    }
  ],
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 2
    }
  ]
}
```

## Symbol Order Book Ticker

**API Description:** Best price/qty on the order book for a symbol or symbols.

* **Method:** `ticker.book`
* **Note:** Retail Price Improvement(RPI) orders are not visible and excluded in the response message.

### Request Example
```json
{
    "id": "9d32157c-a556-4d27-9866-66760a174b57",
    "method": "ticker.book",
    "params": {
        "symbol": "BTCUSDT"
    }
}
```

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
  "id": "9d32157c-a556-4d27-9866-66760a174b57",
  "status": 200,
  "result": {
    "lastUpdateId": 1027024,
    "symbol": "BTCUSDT",
    "bidPrice": "4.00000000",
    "bidQty": "431.00000000",
    "askPrice": "4.00000200",
    "askQty": "9.00000000",
    "time": 1589437530011   // Transaction time
  },
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 2
    }
  ]
}
```

OR (array)
```json
{
  "id": "9d32157c-a556-4d27-9866-66760a174b57",
  "status": 200,
  "result": [
    {
      "lastUpdateId": 1027024,
      "symbol": "BTCUSDT",
      "bidPrice": "4.00000000",
      "bidQty": "431.00000000",
      "askPrice": "4.00000200",
      "askQty": "9.00000000",
      "time": 1589437530011
    }
  ],
  "rateLimits": [
    {
      "rateLimitType": "REQUEST_WEIGHT",
      "interval": "MINUTE",
      "intervalNum": 1,
      "limit": 2400,
      "count": 2
    }
  ]
}
```

## New Order (TRADE)

**API Description:** Send in a new order.

* **HTTP Request:** `POST /fapi/v1/order`
* **Request Weight:** 1 on 10s order rate limit(`X-MBX-ORDER-COUNT-10S`); 1 on 1min order rate limit(`X-MBX-ORDER-COUNT-1M`); 0 on IP rate limit(`x-mbx-used-weight-1m`)

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `side` | `ENUM` | YES | `BUY`, `SELL` |
| `positionSide` | `ENUM` | NO | Default `BOTH` for One-way Mode; `LONG` or `SHORT` for Hedge Mode. It must be sent in Hedge Mode. |
| `type` | `ENUM` | YES | `LIMIT`, `MARKET`, `STOP`, `STOP_MARKET`, `TAKE_PROFIT`, `TAKE_PROFIT_MARKET`, `TRAILING_STOP_MARKET` |
| `timeInForce` | `ENUM` | NO | |
| `quantity` | `DECIMAL` | NO | |
| `reduceOnly` | `STRING` | NO | `"true"` or `"false"`. default `"false"`. Cannot be sent in Hedge Mode. |
| `price` | `DECIMAL` | NO | |
| `newClientOrderId` | `STRING` | NO | A unique id among open orders. Automatically generated if not sent. Can only be string following the rule: `^[\.A-Z\:/a-z0-9_-]{1,36}$` |
| `newOrderRespType` | `ENUM` | NO | `"ACK"`, `"RESULT"`, default `"ACK"` |
| `priceMatch` | `ENUM` | NO | only avaliable for LIMIT/STOP/TAKE_PROFIT order; can be set to `OPPONENT`/ `OPPONENT_5`/ `OPPONENT_10`/ `OPPONENT_20` : `/QUEUE`/ `QUEUE_5`/ `QUEUE_10`/ `QUEUE_20`; Can't be passed together with price. |
| `selfTradePreventionMode` | `ENUM` | NO | `EXPIRE_TAKER`: expire taker order when STP triggers / `EXPIRE_MAKER`: expire taker order when STP triggers / `EXPIRE_BOTH`: expire both orders when STP triggers; default `EXPIRE_MAKER` |
| `goodTillDate` | `LONG` | NO | order cancel time for `timeInForce` GTD, mandatory when timeInforce set to GTD; order the timestamp only retains second-level precision, ms part will be ignored; The goodTillDate timestamp must be greater than the current time plus 600 seconds and smaller than 253402300799000. |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes on Type-specific mandatory parameters:**
> * `LIMIT`: `timeInForce`, `quantity`, `price`
> * `MARKET`: `quantity`
> 
> * If `newOrderRespType` is sent as `RESULT`:
>   * `MARKET` order: the final `FILLED` result of the order will be returned directly.
>   * `LIMIT` order with special `timeInForce`: the final status result of the order (`FILLED` or `EXPIRED`) will be returned directly.
> * `selfTradePreventionMode` is only effective when `timeInForce` set to `IOC` or `GTC` or `GTD`.
> * In extreme market conditions, `timeInForce GTD` order auto cancel time might be delayed comparing to `goodTillDate`.

### Response Example
```json
{
  "clientOrderId": "testOrder",
  "cumQty": "0",
  "cumQuote": "0",          // Will be removed after CM migration
  "executedQty": "0",
  "orderId": 22542179,
  "avgPrice": "0.00000",    // Will be removed after CM migration
  "origQty": "10",
  "price": "0",
  "reduceOnly": false,
  "side": "BUY",
  "positionSide": "SHORT",
  "status": "NEW",
  "stopPrice": "0",         // ignored for LIMIT / MARKET orders
  "closePosition": false,   // if Close-All
  "symbol": "BTCUSDT",
  "timeInForce": "GTD",
  "type": "LIMIT",
  "origType": "LIMIT",
  "updateTime": 1566818724722,
  "workingType": "CONTRACT_PRICE",
  "priceProtect": false,             // if conditional order trigger is protected	
  "priceMatch": "NONE",              // price match mode
  "selfTradePreventionMode": "NONE", // self trading preventation mode
  "goodTillDate": 1693207680000      // order pre-set auot cancel time for TIF GTD order
}
```

## Place Multiple Orders (TRADE)

**API Description:** Place Multiple Orders

* **HTTP Request:** `POST /fapi/v1/batchOrders`
* **Request Weight:** 5 on 10s order rate limit(`X-MBX-ORDER-COUNT-10S`); 1 on 1min order rate limit(`X-MBX-ORDER-COUNT-1M`); 5 on IP rate limit(`x-mbx-used-weight-1m`)

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `batchOrders` | `LIST<JSON>` | YES | order list. Max 5 orders. |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

Where `batchOrders` is the list of order parameters in JSON.
Example: `/fapi/v1/batchOrders?batchOrders=[{"type":"LIMIT","timeInForce":"GTC","symbol":"BTCUSDT","side":"BUY","price":"10001","quantity":"0.001"}]`

**Batch Orders Parameter Rules** (same as New Order)
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `side` | `ENUM` | YES | |
| `positionSide` | `ENUM` | NO | Default `BOTH` for One-way Mode; `LONG` or `SHORT` for Hedge Mode. It must be sent with Hedge Mode. |
| `type` | `ENUM` | YES | |
| `timeInForce` | `ENUM` | NO | |
| `quantity` | `DECIMAL` | YES | |
| `reduceOnly` | `STRING` | NO | `"true"` or `"false"`. default `"false"`. |
| `price` | `DECIMAL` | NO | |
| `newClientOrderId` | `STRING` | NO | A unique id among open orders. Automatically generated if not sent. Can only be string following the rule: `^[\.A-Z\:/a-z0-9_-]{1,36}$` |
| `newOrderRespType` | `ENUM` | NO | `"ACK"`, `"RESULT"`, default `"ACK"` |
| `priceMatch` | `ENUM` | NO | only avaliable for LIMIT/STOP/TAKE_PROFIT order; can be set to `OPPONENT`/ `OPPONENT_5`/ `OPPONENT_10`/ `OPPONENT_20` : `/QUEUE`/ `QUEUE_5`/ `QUEUE_10`/ `QUEUE_20`; Can't be passed together with price. |
| `selfTradePreventionMode` | `ENUM` | NO | `EXPIRE_TAKER` / `EXPIRE_MAKER` / `EXPIRE_BOTH`; default `NONE` |
| `goodTillDate` | `LONG` | NO | order cancel time for `timeInForce` GTD. |

> **Notes:**
> * Batch orders are processed concurrently, and the order of matching is not guaranteed.
> * The order of returned contents for batch orders is the same as the order of the order list.

### Response Example
```json
[
  {
    "clientOrderId": "testOrder",
    "cumQty": "0",
    "cumQuote": "0",     // Will be removed after CM migration
    "executedQty": "0",
    "orderId": 22542179,
    "avgPrice": "0.00000",     // Will be removed after CM migration
    "origQty": "10",
    "price": "0",
    "reduceOnly": false,
    "side": "BUY",
    "positionSide": "SHORT",
    "status": "NEW",
    "stopPrice": "0",
    "closePosition": false,
    "symbol": "BTCUSDT",
    "timeInForce": "GTC",
    "type": "TRAILING_STOP_MARKET",
    "origType": "TRAILING_STOP_MARKET",
    "updateTime": 1566818724722,
    "workingType": "CONTRACT_PRICE",
    "priceProtect": false,             // if conditional order trigger is protected	
    "priceMatch": "NONE",              // price match mode
    "selfTradePreventionMode": "NONE", // self trading preventation mode
    "goodTillDate": 1693207680000      // order pre-set auto cancel time for TIF GTD order
  },
  {
    "code": -2022, 
    "msg": "ReduceOnly Order is rejected."
  }
]
```

## Modify Order (TRADE)

**API Description:** Order modify function, currently only LIMIT order modification is supported, modified orders will be reordered in the match queue.

* **HTTP Request:** `PUT /fapi/v1/order`
* **Request Weight:** 1 on 10s order rate limit(`X-MBX-ORDER-COUNT-10S`); 1 on 1min order rate limit(`X-MBX-ORDER-COUNT-1M`); 0 on IP rate limit(`x-mbx-used-weight-1m`)

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `orderId` | `LONG` | NO | |
| `origClientOrderId` | `STRING` | NO | |
| `symbol` | `STRING` | YES | |
| `side` | `ENUM` | YES | `SELL`, `BUY` |
| `quantity` | `DECIMAL` | YES | Order quantity, cannot be sent with `closePosition=true` |
| `price` | `DECIMAL` | YES | |
| `priceMatch` | `ENUM` | NO | only avaliable for LIMIT/STOP/TAKE_PROFIT order; can be set to `OPPONENT`/ `OPPONENT_5`/ `OPPONENT_10`/ `OPPONENT_20` : `/QUEUE`/ `QUEUE_5`/ `QUEUE_10`/ `QUEUE_20`; Can't be passed together with price. |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes:**
> * Either `orderId` or `origClientOrderId` must be sent, and the `orderId` will prevail if both are sent.
> * Both `quantity` and `price` must be sent, which is different from dapi modify order endpoint.
> * When the new `quantity` or `price` doesn't satisfy `PRICE_FILTER` / `PERCENT_FILTER` / `LOT_SIZE`, amendment will be rejected and the order will stay as it is.
> * However the order will be cancelled by the amendment in the following situations:
>   * when the order is in partially filled status and the new quantity <= `executedQty`
>   * When the order is `GTX` and the new price will cause it to be executed immediately
> * One order can only be modified for less than 10000 times.

### Response Example
```json
{
  "orderId": 20072994037,
  "symbol": "BTCUSDT",
  "pair": "BTCUSDT",
  "status": "NEW",
  "clientOrderId": "LJ9R4QZDihCaS8UAOOLpgW",
  "price": "30005",
  "avgPrice": "0.0",     // Will be removed after CM migration
  "origQty": "1",
  "executedQty": "0",
  "cumQty": "0",
  "cumBase": "0",
  "timeInForce": "GTC",
  "type": "LIMIT",
  "reduceOnly": false,
  "closePosition": false,
  "side": "BUY",
  "positionSide": "LONG",
  "stopPrice": "0",
  "workingType": "CONTRACT_PRICE",
  "priceProtect": false,
  "origType": "LIMIT",
  "priceMatch": "NONE",              // price match mode
  "selfTradePreventionMode": "NONE", // self trading preventation mode
  "goodTillDate": 0,                 // order pre-set auot cancel time for TIF GTD order
  "updateTime": 1629182711600
}
```

## Modify Multiple Orders (TRADE)

**API Description:** Modify Multiple Orders (TRADE)

* **HTTP Request:** `PUT /fapi/v1/batchOrders`
* **Request Weight:** 5 on 10s order rate limit(`X-MBX-ORDER-COUNT-10S`); 1 on 1min order rate limit(`X-MBX-ORDER-COUNT-1M`); 5 on IP rate limit(`x-mbx-used-weight-1m`);

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `batchOrders` | `list<JSON>` | YES | order list. Max 5 orders. |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

Where `batchOrders` is the list of order parameters in JSON:

| Name | Type | Mandatory | Description |
|---|---|---|---|
| `orderId` | `LONG` | NO | |
| `origClientOrderId` | `STRING` | NO | |
| `symbol` | `STRING` | YES | |
| `side` | `ENUM` | YES | `SELL`, `BUY` |
| `quantity` | `DECIMAL` | YES | Order quantity, cannot be sent with `closePosition=true` |
| `price` | `DECIMAL` | YES | |
| `priceMatch` | `ENUM` | NO | only avaliable for LIMIT/STOP/TAKE_PROFIT order; can be set to `OPPONENT`/ `OPPONENT_5`/ `OPPONENT_10`/ `OPPONENT_20` : `/QUEUE`/ `QUEUE_5`/ `QUEUE_10`/ `QUEUE_20`; Can't be passed together with price. |
| `stopPrice` | `DECIMAL` | NO | stop price, only `STOP`, `STOP_MARKET`, `TAKE_PROFIT`, `TAKE_PROFIT_MARKET` need |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes:**
> * Parameter rules are same with Modify Order.
> * Batch modify orders are processed concurrently, and the order of matching is not guaranteed.
> * The order of returned contents for batch modify orders is the same as the order of the order list.
> * One order can only be modified for less than 10000 times.

### Response Example
```json
[
  {
    "orderId": 20072994037,
    "symbol": "BTCUSDT",
    "pair": "BTCUSDT",
    "status": "NEW",
    "clientOrderId": "LJ9R4QZDihCaS8UAOOLpgW",
    "price": "30005",
    "avgPrice": "0.0",     // Will be removed after CM migration
    "origQty": "1",
    "executedQty": "0",
    "cumQty": "0",
    "cumBase": "0",
    "timeInForce": "GTC",
    "type": "LIMIT",
    "reduceOnly": false,
    "closePosition": false,
    "side": "BUY",
    "positionSide": "LONG",
    "stopPrice": "0",
    "workingType": "CONTRACT_PRICE",
    "priceProtect": false,
    "origType": "LIMIT",
    "priceMatch": "NONE",              // price match mode
    "selfTradePreventionMode": "NONE", // self trading preventation mode
    "goodTillDate": 0,                 // order pre-set auot cancel time for TIF GTD order
    "updateTime": 1629182711600
  },
  {
    "code": -2022, 
    "msg": "ReduceOnly Order is rejected."
  }
]
```

## Get Order Modify History (USER_DATA)

**API Description:** Get order modification history

* **HTTP Request:** `GET /fapi/v1/orderAmendment`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `orderId` | `LONG` | NO | |
| `origClientOrderId` | `STRING` | NO | |
| `startTime` | `LONG` | NO | Timestamp in ms to get modification history from INCLUSIVE |
| `endTime` | `LONG` | NO | Timestamp in ms to get modification history until INCLUSIVE |
| `limit` | `INT` | NO | Default 50; max 100 |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes:**
> * Either `orderId` or `origClientOrderId` must be sent, and the `orderId` will prevail if both are sent.
> * Order modify history longer than 3 months is not avaliable.

### Response Example
```json
[
    {
        "amendmentId": 5363,	// Order modification ID
        "symbol": "BTCUSDT",
        "pair": "BTCUSDT",
        "orderId": 20072994037,
        "clientOrderId": "LJ9R4QZDihCaS8UAOOLpgW",
        "time": 1629184560899,	// Order modification time
        "amendment": {
            "price": {
                "before": "30004",
                "after": "30003.2"
            },
            "origQty": {
                "before": "1",
                "after": "1"
            },
            "count": 3	// Order modification count, representing the number of times the order has been modified
        }
    },
    {
        "amendmentId": 5361,
        "symbol": "BTCUSDT",
        "pair": "BTCUSDT",
        "orderId": 20072994037,
        "clientOrderId": "LJ9R4QZDihCaS8UAOOLpgW",
        "time": 1629184533946,
        "amendment": {
            "price": {
                "before": "30005",
                "after": "30004"
            },
            "origQty": {
                "before": "1",
                "after": "1"
            },
            "count": 2
        }
    },
    {
        "amendmentId": 5325,
        "symbol": "BTCUSDT",
        "pair": "BTCUSDT",
        "orderId": 20072994037,
        "clientOrderId": "LJ9R4QZDihCaS8UAOOLpgW",
        "time": 1629182711787,
        "amendment": {
            "price": {
                "before": "30002",
                "after": "30005"
            },
            "origQty": {
                "before": "1",
                "after": "1"
            },
            "count": 1
        }
    }
]
```

## Cancel Order (TRADE)

**API Description:** Cancel an active order.

* **HTTP Request:** `DELETE /fapi/v1/order`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `orderId` | `LONG` | NO | |
| `origClientOrderId` | `STRING` | NO | |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Note:** Either `orderId` or `origClientOrderId` must be sent.

### Response Example
```json
{
  "clientOrderId": "myOrder1",
  "cumQty": "0",
  "cumQuote": "0",          // Will be removed after CM migration
  "executedQty": "0",
  "orderId": 283194212,
  "origQty": "11",
  "origType": "TRAILING_STOP_MARKET",
  "price": "0",
  "avgPrice": "0.00",       // Will be removed after CM migration
  "reduceOnly": false,
  "side": "BUY",
  "positionSide": "SHORT",
  "status": "CANCELED",
  "stopPrice": "9300",      // please ignore when order type is TRAILING_STOP_MARKET
  "closePosition": false,   // if Close-All
  "symbol": "BTCUSDT",
  "timeInForce": "GTC",
  "type": "TRAILING_STOP_MARKET",
  "activatePrice": "9020",  // activation price, only return with TRAILING_STOP_MARKET order
  "priceRate": "0.3",       // callback rate, only return with TRAILING_STOP_MARKET order
  "updateTime": 1571110484038,
  "workingType": "CONTRACT_PRICE",
  "priceProtect": false,             // if conditional order trigger is protected	
  "priceMatch": "NONE",              // price match mode
  "selfTradePreventionMode": "NONE", // self trading preventation mode
  "goodTillDate": 1693207680000      // order pre-set auot cancel time for TIF GTD order
}
```

## Cancel Multiple Orders (TRADE)

**API Description:** Cancel Multiple Orders

* **HTTP Request:** `DELETE /fapi/v1/batchOrders`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `orderIdList` | `LIST<LONG>` | NO | max length 10, e.g. `[1234567,2345678]` |
| `origClientOrderIdList` | `LIST<STRING>` | NO | max length 10, e.g. `["my_id_1","my_id_2"]`, encode the double quotes. No space after comma. |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Note:** Either `orderIdList` or `origClientOrderIdList` must be sent.

### Response Example
```json
[
  {
    "clientOrderId": "myOrder1",
    "cumQty": "0",
    "cumQuote": "0",          // Will be removed after CM migration
    "executedQty": "0",
    "orderId": 283194212,
    "origQty": "11",
    "origType": "TRAILING_STOP_MARKET",
    "price": "0",
    "reduceOnly": false,
    "side": "BUY",
    "positionSide": "SHORT",
    "status": "CANCELED",
    "stopPrice": "9300",      // please ignore when order type is TRAILING_STOP_MARKET
    "closePosition": false,   // if Close-All
    "symbol": "BTCUSDT",
    "timeInForce": "GTC",
    "type": "TRAILING_STOP_MARKET",
    "activatePrice": "9020",  // activation price, only return with TRAILING_STOP_MARKET order
    "priceRate": "0.3",       // callback rate, only return with TRAILING_STOP_MARKET order
    "updateTime": 1571110484038,
    "workingType": "CONTRACT_PRICE",
    "priceProtect": false,             // if conditional order trigger is protected	
    "priceMatch": "NONE",              // price match mode
    "selfTradePreventionMode": "NONE", // self trading preventation mode
    "goodTillDate": 1693207680000      // order pre-set auot cancel time for TIF GTD order
  },
  {
    "code": -2011,
    "msg": "Unknown order sent."
  }
]
```

## Cancel All Open Orders (TRADE)

**API Description:** Cancel All Open Orders

* **HTTP Request:** `DELETE /fapi/v1/allOpenOrders`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
{
  "code": 200, 
  "msg": "The operation of cancel all open order is done."
}
```

## Auto-Cancel All Open Orders (TRADE)

**API Description:** Cancel all open orders of the specified symbol at the end of the specified countdown. The endpoint should be called repeatedly as heartbeats so that the existing countdown time can be canceled and replaced by a new one.

**Example usage:**
* Call this endpoint at 30s intervals with an `countdownTime` of 120000 (120s).
* If this endpoint is not called within 120 seconds, all your orders of the specified symbol will be automatically canceled.
* If this endpoint is called with an `countdownTime` of 0, the countdown timer will be stopped.

> **Note:** The system will check all countdowns approximately every 10 milliseconds, so please note that sufficient redundancy should be considered when using this function. We do not recommend setting the countdown time to be too precise or too small.

* **HTTP Request:** `POST /fapi/v1/countdownCancelAll`
* **Request Weight:** 10

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `countdownTime` | `LONG` | YES | countdown time, 1000 for 1 second. 0 to cancel the timer |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
{
  "symbol": "BTCUSDT", 
  "countdownTime": "100000"
}
```

## Query Order (USER_DATA)

**API Description:** Check an order's status.

> **Note:** These orders will not be found:
> * order status is `CANCELED` or `EXPIRED` AND order has NO filled trade AND created time + 3 days < current time
> * order create time + 90 days < current time

* **HTTP Request:** `GET /fapi/v1/order`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `orderId` | `LONG` | NO | |
| `origClientOrderId` | `STRING` | NO | |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes:**
> * Either `orderId` or `origClientOrderId` must be sent.
> * `orderId` is self-increment for each specific symbol.

### Response Example
```json
{
  "avgPrice": "0.00000",
  "clientOrderId": "abc",
  "cumQuote": "0",
  "executedQty": "0",
  "orderId": 1917641,
  "origQty": "0.40",
  "origType": "TRAILING_STOP_MARKET",
  "price": "0",
  "reduceOnly": false,
  "side": "BUY",
  "positionSide": "SHORT",
  "status": "NEW",
  "stopPrice": "9300",    // please ignore when order type is TRAILING_STOP_MARKET
  "closePosition": false,   // if Close-All
  "symbol": "BTCUSDT",
  "time": 1579276756075,    // order time
  "timeInForce": "GTC",
  "type": "TRAILING_STOP_MARKET",
  "activatePrice": "9020",   // activation price, only return with TRAILING_STOP_MARKET order
  "priceRate": "0.3",     // callback rate, only return with TRAILING_STOP_MARKET order
  "updateTime": 1579276756075,  // update time
  "workingType": "CONTRACT_PRICE",
  "priceProtect": false            // if conditional order trigger is protected
}
```

## All Orders (USER_DATA)

**API Description:** Get all account orders; active, canceled, or filled.

> **Note:** These orders will not be found:
> * order status is `CANCELED` or `EXPIRED` AND order has NO filled trade AND created time + 3 days < current time
> * order create time + 90 days < current time

* **HTTP Request:** `GET /fapi/v1/allOrders`
* **Request Weight:** 5

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `orderId` | `LONG` | NO | |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | |
| `limit` | `INT` | NO | Default 500; max 1000. |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes:**
> * If `orderId` is set, it will get orders >= that `orderId`. Otherwise most recent orders are returned.
> * The query time period must be less then 7 days (default as the recent 7 days).

### Response Example
```json
[
  {
    "avgPrice": "0.00000",
    "clientOrderId": "abc",
    "cumQuote": "0",
    "executedQty": "0",
    "orderId": 1917641,
    "origQty": "0.40",
    "origType": "TRAILING_STOP_MARKET",
    "price": "0",
    "reduceOnly": false,
    "side": "BUY",
    "positionSide": "SHORT",
    "status": "NEW",
    "stopPrice": "9300",        // please ignore when order type is TRAILING_STOP_MARKET
    "closePosition": false,     // if Close-All
    "symbol": "BTCUSDT",
    "time": 1579276756075,      // order time
    "timeInForce": "GTC",
    "type": "TRAILING_STOP_MARKET",
    "activatePrice": "9020",    // activation price, only return with TRAILING_STOP_MARKET order
    "priceRate": "0.3",         // callback rate, only return with TRAILING_STOP_MARKET order
    "updateTime": 1579276756075,    // update time
    "workingType": "CONTRACT_PRICE",
    "priceProtect": false,              // if conditional order trigger is protected	
    "priceMatch": "NONE",              // price match mode
    "selfTradePreventionMode": "NONE", // self trading preventation mode
    "goodTillDate": 0      // order pre-set auot cancel time for TIF GTD order
  }
]
```

## Current All Open Orders (USER_DATA)

**API Description:** Get all open orders on a symbol.

* **HTTP Request:** `GET /fapi/v1/openOrders`
* **Request Weight:** 1 for a single symbol; 40 when the symbol parameter is omitted
* **Note:** Careful when accessing this with no symbol.

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | If the symbol is not sent, orders for all symbols will be returned in an array. |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
[
  {
    "avgPrice": "0.00000",
    "clientOrderId": "abc",
    "cumQuote": "0",
    "executedQty": "0",
    "orderId": 1917641,
    "origQty": "0.40",
    "origType": "TRAILING_STOP_MARKET",
    "price": "0",
    "reduceOnly": false,
    "side": "BUY",
    "positionSide": "SHORT",
    "status": "NEW",
    "stopPrice": "9300",        // please ignore when order type is TRAILING_STOP_MARKET
    "closePosition": false,     // if Close-All
    "symbol": "BTCUSDT",
    "time": 1579276756075,      // order time
    "timeInForce": "GTC",
    "type": "TRAILING_STOP_MARKET",
    "activatePrice": "9020",    // activation price, only return with TRAILING_STOP_MARKET order
    "priceRate": "0.3",         // callback rate, only return with TRAILING_STOP_MARKET order
    "updateTime": 1579276756075,    // update time
    "workingType": "CONTRACT_PRICE",
    "priceProtect": false,            // if conditional order trigger is protected	
    "priceMatch": "NONE",              // price match mode
    "selfTradePreventionMode": "NONE", // self trading preventation mode
    "goodTillDate": 0      // order pre-set auot cancel time for TIF GTD order
  }
]
```

## Change Margin Type (TRADE)

**API Description:** Change symbol level margin type

* **HTTP Request:** `POST /fapi/v1/marginType`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `marginType` | `ENUM` | YES | `ISOLATED`, `CROSSED` |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
{
  "code": 200,
  "msg": "success"
}
```

## Change Position Mode (TRADE)

**API Description:** Change user's position mode (Hedge Mode or One-way Mode ) on EVERY symbol.

> **Note:** After CM migration, UM and CM share the same `dualSidePosition` setting. Calling this endpoint flips both UM and CM at once. If either side has any open order or open position, the change is rejected:
> * `-4067` (open orders exist)
> * `-4068` (open position exists)

* **HTTP Request:** `POST /fapi/v1/positionSide/dual`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `dualSidePosition` | `STRING` | YES | `"true"`: Hedge Mode; `"false"`: One-way Mode |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
{
  "code": 200,
  "msg": "success"
}
```

## Change Initial Leverage (TRADE)

**API Description:** Change user's initial leverage of specific symbol market.

* **HTTP Request:** `POST /fapi/v1/leverage`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `leverage` | `INT` | YES | target initial leverage: int from 1 to 125 |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
{
  "leverage": 21,
  "maxNotionalValue": "1000000",
  "symbol": "BTCUSDT"
}
```

## Change Multi-Assets Mode (TRADE)

**API Description:** Change user's Multi-Assets mode (Multi-Assets Mode or Single-Asset Mode) on Every symbol.

* **HTTP Request:** `POST /fapi/v1/multiAssetsMargin`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `multiAssetsMargin` | `STRING` | YES | `"true"`: Multi-Assets Mode; `"false"`: Single-Asset Mode |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
{
  "code": 200,
  "msg": "success"
}
```

## Modify Isolated Position Margin (TRADE)

**API Description:** Modify Isolated Position Margin

* **HTTP Request:** `POST /fapi/v1/positionMargin`
* **Request Weight:** 1
* **Note:** Only for isolated symbol

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `positionSide` | `ENUM` | NO | Default `BOTH` for One-way Mode ; `LONG` or `SHORT` for Hedge Mode. It must be sent with Hedge Mode. |
| `amount` | `DECIMAL` | YES | |
| `type` | `INT` | YES | 1: Add position margin, 2: Reduce position margin |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
{
  "msg": "Successfully modify position margin.",
  "type": 1
}
```

## Position Information V3 (USER_DATA)

**API Description:** Get current position information(only symbol that has position or open orders will be returned).

* **HTTP Request:** `GET /fapi/v3/positionRisk`
* **Request Weight:** 5
* **Note:** Please use with user data stream `ACCOUNT_UPDATE` to meet your timeliness and accuracy needs.

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example

For One-way position mode:
```json
[
  {
        "symbol": "ADAUSDT",                  // symbol
        "positionSide": "BOTH",               // position side
        "positionAmt": "30",                  // position amount, positive for long, negative for short
        "entryPrice": "0.385",                // entry price
        "breakEvenPrice": "0.385077",         // break-even price
        "markPrice": "0.41047590",            // current mark price
        "unRealizedProfit": "0.76427700",     // unrealized profit
        "liquidationPrice": "0",              // liquidation price
        "isolatedMargin": "0",                // isolated margin
        "notional": "12.31427700",            // notional value of position
        "marginAsset": "USDT",                // margin asset
        "isolatedWallet": "0",                // isolated wallet (if isolated position)
        "initialMargin": "0.61571385",        // initial margin required with current mark price
        "maintMargin": "0.08004280",          // maintenance margin required
        "positionInitialMargin": "0.61571385",// initial margin required for positions with current mark price
        "openOrderInitialMargin": "0",        // initial margin required for open orders with current mark price
        "adl": 2,                             // auto-deleverage ranking
        "bidNotional": "0",                   // ignore
        "askNotional": "0",                   // ignore
        "updateTime": 1720736417660           // update time
  }
]
```

For Hedge position mode:
```json
[
  {
        "symbol": "ADAUSDT",                  // symbol
        "positionSide": "LONG",               // position side
        "positionAmt": "30",                  // position amount, positive for long, negative for short
        "entryPrice": "0.385",                // entry price
        "breakEvenPrice": "0.385077",         // break-even price
        "markPrice": "0.41047590",            // current mark price
        "unRealizedProfit": "0.76427700",     // unrealized profit
        "liquidationPrice": "0",              // liquidation price
        "isolatedMargin": "0",                // isolated margin
        "notional": "12.31427700",            // notional value of position
        "marginAsset": "USDT",                // margin asset
        "isolatedWallet": "0",                // isolated wallet (if isolated position)
        "initialMargin": "0.61571385",        // initial margin required with current mark price
        "maintMargin": "0.08004280",          // maintenance margin required
        "positionInitialMargin": "0.61571385",// initial margin required for positions with current mark price
        "openOrderInitialMargin": "0",        // initial margin required for open orders with current mark price
        "adl": 2,                             // auto-deleverage ranking
        "bidNotional": "0",                   // ignore
        "askNotional": "0",                   // ignore
        "updateTime": 1720736417660           // update time
  },
  {
        "symbol": "COMPUSDT",                 // symbol
        "positionSide": "SHORT",              // position side
        "positionAmt": "-1.000",              // position amount, positive for long, negative for short
        "entryPrice": "70.92841",             // entry price
        "breakEvenPrice": "70.900038636",     // break-even price
        "markPrice": "49.72023376",           // current mark price
        "unRealizedProfit": "21.20817624",    // unrealized profit
        "liquidationPrice": "2260.56757210",  // liquidation price
        "isolatedMargin": "0",                // isolated margin
        "notional": "-49.72023376",           // notional value of position
        "marginAsset": "USDT",                // margin asset
        "isolatedWallet": "0",                // isolated wallet (if isolated position)
        "initialMargin": "2.48601168",        // initial margin required with current mark price
        "maintMargin": "0.49720233",          // maintenance margin required
        "positionInitialMargin": "2.48601168",// initial margin required for positions with current mark price
        "openOrderInitialMargin": "0",        // initial margin required for open orders with current mark price
        "adl": 2,                             // auto-deleverage ranking
        "bidNotional": "0",                   // ignore
        "askNotional": "0",                   // ignore
        "updateTime": 1708943511656           // update time
  }
]
```

## Position ADL Quantile Estimation (USER_DATA)

**API Description:** Position ADL Quantile Estimation

Values update every 30s. Values 0, 1, 2, 3, 4 shows the queue position and possibility of ADL from low to high.
* For positions of the symbol are in One-way Mode or isolated margined in Hedge Mode, `"LONG"`, `"SHORT"`, and `"BOTH"` will be returned to show the positions' adl quantiles of different position sides.
* If the positions of the symbol are crossed margined in Hedge Mode:
  * `"HEDGE"` as a sign will be returned instead of `"BOTH"`;
  * A same value caculated on unrealized pnls on long and short sides' positions will be shown for `"LONG"` and `"SHORT"` when there are positions in both of long and short sides.

* **HTTP Request:** `GET /fapi/v1/adlQuantile`
* **Request Weight:** 5

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | NO | |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
[
  {
    "symbol": "ETHUSDT", 
    "adlQuantile": 
      {
        // if the positions of the symbol are crossed margined in Hedge Mode, "LONG" and "SHORT" will be returned a same quantile value, and "HEDGE" will be returned instead of "BOTH".
        "LONG": 3,  
        "SHORT": 3, 
        "HEDGE": 0   // only a sign, ignore the value
      }
    },
  {
    "symbol": "BTCUSDT", 
      }
  }
 ]
```

## Get Position Margin Change History (TRADE)

**API Description:** Get Position Margin Change History

* **HTTP Request:** `GET /fapi/v1/positionMargin/history`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `type` | `INT` | NO | 1: Add position margin, 2: Reduce position margin |
| `startTime` | `LONG` | NO | |
| `endTime` | `LONG` | NO | Default current time if not pass |
| `limit` | `INT` | NO | Default: 500 |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes:**
> * Support querying future histories that are not older than 30 days
> * The time between `startTime` and `endTime` can't be more than 30 days

### Response Example
```json
[
  {
    "symbol": "BTCUSDT",
    "type": 1,
    "deltaType": "USER_ADJUST",
    "amount": "23.36332311",
    "asset": "USDT",
    "time": 1578047897183,
    "positionSide": "BOTH"
  },
  {
    "symbol": "BTCUSDT",
    "type": 1, 
    "deltaType": "USER_ADJUST",
    "amount": "100",
    "asset": "USDT",
    "time": 1578047900425,
    "positionSide": "LONG" 
  }
]
```

## Test Order (TRADE)

**API Description:** Testing order request, this order will not be submitted to matching engine

* **HTTP Request:** `POST /fapi/v1/order/test`

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `side` | `ENUM` | YES | |
| `positionSide` | `ENUM` | NO | Default `BOTH` for One-way Mode ; `LONG` or `SHORT` for Hedge Mode. It must be sent in Hedge Mode. |
| `type` | `ENUM` | YES | |
| `timeInForce` | `ENUM` | NO | |
| `quantity` | `DECIMAL` | NO | Cannot be sent with `closePosition=true`(Close-All) |
| `reduceOnly` | `STRING` | NO | `"true"` or `"false"`. default `"false"`. Cannot be sent in Hedge Mode; cannot be sent with `closePosition=true` |
| `price` | `DECIMAL` | NO | |
| `newClientOrderId` | `STRING` | NO | A unique id among open orders. Automatically generated if not sent. Can only be string following the rule: `^[\.A-Z\:/a-z0-9_-]{1,36}$` |
| `stopPrice` | `DECIMAL` | NO | Used with `STOP`/`STOP_MARKET` or `TAKE_PROFIT`/`TAKE_PROFIT_MARKET` orders. |
| `closePosition` | `STRING` | NO | `true`, `false`; Close-All, used with `STOP_MARKET` or `TAKE_PROFIT_MARKET`. |
| `activationPrice` | `DECIMAL` | NO | Used with `TRAILING_STOP_MARKET` orders, default as the latest price(supporting different workingType) |
| `callbackRate` | `DECIMAL` | NO | Used with `TRAILING_STOP_MARKET` orders, min 0.1, max 5 where 1 for 1% |
| `workingType` | `ENUM` | NO | stopPrice triggered by: `"MARK_PRICE"`, `"CONTRACT_PRICE"`. Default `"CONTRACT_PRICE"` |
| `priceProtect` | `STRING` | NO | `"true"` or `"false"`, default `"false"`. Used with `STOP`/`STOP_MARKET` or `TAKE_PROFIT`/`TAKE_PROFIT_MARKET` orders. |
| `newOrderRespType` | `ENUM` | NO | `"ACK"`, `"RESULT"`, default `"ACK"` |
| `priceMatch` | `ENUM` | NO | only avaliable for LIMIT/STOP/TAKE_PROFIT order; can be set to `OPPONENT`/ `OPPONENT_5`/ `OPPONENT_10`/ `OPPONENT_20` : `/QUEUE`/ `QUEUE_5`/ `QUEUE_10`/ `QUEUE_20`; Can't be passed together with price. |
| `selfTradePreventionMode` | `ENUM` | NO | `NONE`: No STP / `EXPIRE_TAKER`: expire taker order when STP triggers / `EXPIRE_MAKER`: expire taker order when STP triggers / `EXPIRE_BOTH`: expire both orders when STP triggers; default `NONE` |
| `goodTillDate` | `LONG` | NO | order cancel time for `timeInForce` GTD, mandatory when timeInforce set to GTD; order the timestamp only retains second-level precision, ms part will be ignored; The goodTillDate timestamp must be greater than the current time plus 600 seconds and smaller than 253402300799000. |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes on Type-specific mandatory parameters:**
> * `LIMIT`: `timeInForce`, `quantity`, `price`
> * `MARKET`: `quantity`
> * `STOP`/`TAKE_PROFIT`: `quantity`, `price`, `stopPrice`
> * `STOP_MARKET`/`TAKE_PROFIT_MARKET`: `stopPrice`
> * `TRAILING_STOP_MARKET`: `callbackRate`
> 
> * Order with type `STOP`, parameter `timeInForce` can be sent (default `GTC`).
> * Order with type `TAKE_PROFIT`, parameter `timeInForce` can be sent (default `GTC`).
> 
> **Condition orders will be triggered when:**
> * If parameter `priceProtect` is sent as `true`:
>   * when price reaches the stopPrice, the difference rate between "MARK_PRICE" and "CONTRACT_PRICE" cannot be larger than the "triggerProtect" of the symbol
>   * "triggerProtect" of a symbol can be got from `GET /fapi/v1/exchangeInfo`
> * `STOP`, `STOP_MARKET`:
>   * BUY: latest price ("MARK_PRICE" or "CONTRACT_PRICE") >= stopPrice
>   * SELL: latest price ("MARK_PRICE" or "CONTRACT_PRICE") <= stopPrice
> * `TAKE_PROFIT`, `TAKE_PROFIT_MARKET`:
>   * BUY: latest price ("MARK_PRICE" or "CONTRACT_PRICE") <= stopPrice
>   * SELL: latest price ("MARK_PRICE" or "CONTRACT_PRICE") >= stopPrice
> * `TRAILING_STOP_MARKET`:
>   * BUY: the lowest price after order placed <= activationPrice, and the latest price >= the lowest price * (1 + callbackRate)
>   * SELL: the highest price after order placed >= activationPrice, and the latest price <= the highest price * (1 - callbackRate)
>   * For `TRAILING_STOP_MARKET`, if you got such error code: `{"code": -2021, "msg": "Order would immediately trigger."}` means that the parameters you send do not meet the following requirements:
>     * BUY: `activationPrice` should be smaller than latest price.
>     * SELL: `activationPrice` should be larger than latest price.
> 
> **Other Rules:**
> * If `newOrderRespType` is sent as `RESULT`:
>   * `MARKET` order: the final `FILLED` result of the order will be return directly.
>   * `LIMIT` order with special `timeInForce`: the final status result of the order (`FILLED` or `EXPIRED`) will be returned directly.
> * `STOP_MARKET`, `TAKE_PROFIT_MARKET` with `closePosition=true`:
>   * Follow the same rules for condition orders.
>   * If triggered, close all current long position(if SELL) or current short position(if BUY).
>   * Cannot be used with `quantity` paremeter
>   * Cannot be used with `reduceOnly` parameter
>   * In Hedge Mode, cannot be used with BUY orders in LONG position side. and cannot be used with SELL orders in SHORT position side
> * `selfTradePreventionMode` is only effective when `timeInForce` set to `IOC` or `GTC` or `GTD`.
> * In extreme market conditions, `timeInForce GTD` order auto cancel time might be delayed comparing to `goodTillDate`.

### Response Example
```json
{
  "clientOrderId": "testOrder",
  "cumQty": "0",
  "cumQuote": "0",
  "executedQty": "0",
  "orderId": 22542179,
  "avgPrice": "0.00000",
  "origQty": "10",
  "price": "0",
  "reduceOnly": false,
  "side": "BUY",
  "positionSide": "SHORT",
  "status": "NEW",
  "stopPrice": "9300",        // please ignore when order type is TRAILING_STOP_MARKET
  "closePosition": false,     // if Close-All
  "symbol": "BTCUSDT",
  "timeInForce": "GTD",
  "type": "TRAILING_STOP_MARKET",
  "origType": "TRAILING_STOP_MARKET",
  "activatePrice": "9020",    // activation price, only return with TRAILING_STOP_MARKET order
  "priceRate": "0.3",         // callback rate, only return with TRAILING_STOP_MARKET order
  "updateTime": 1566818724722,
  "workingType": "CONTRACT_PRICE",
  "priceProtect": false,      // if conditional order trigger is protected	
  "priceMatch": "NONE",              // price match mode
  "selfTradePreventionMode": "NONE", // self trading preventation mode
  "goodTillDate": 1693207680000      // order pre-set auot cancel time for TIF GTD order
}
```

## New Algo Order (TRADE)

**API Description:** Send in a new algo (conditional) order. Use this endpoint to place TP/SL (Take Profit / Stop Loss) and trailing stop orders on USD-M Futures. Supported order types under `algoType=CONDITIONAL` are `STOP_MARKET`, `TAKE_PROFIT_MARKET`, `STOP`, `TAKE_PROFIT`, and `TRAILING_STOP_MARKET`.

* **HTTP Request:** `POST /fapi/v1/algoOrder`
* **Request Weight:** 1 on 10s order rate limit(`X-MBX-ORDER-COUNT-10S`); 1 on 1min order rate limit(`X-MBX-ORDER-COUNT-1M`); 0 on IP rate limit(`x-mbx-used-weight-1m`)

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `algoType` | `ENUM` | YES | Only support `CONDITIONAL` |
| `symbol` | `STRING` | YES | |
| `side` | `ENUM` | YES | |
| `positionSide` | `ENUM` | NO | Default `BOTH` for One-way Mode ; `LONG` or `SHORT` for Hedge Mode. It must be sent in Hedge Mode. |
| `type` | `ENUM` | YES | For CONDITIONAL algoType, `STOP_MARKET`/`TAKE_PROFIT_MARKET`/`STOP`/`TAKE_PROFIT`/`TRAILING_STOP_MARKET` as order type |
| `timeInForce` | `ENUM` | NO | `IOC` or `GTC` or `FOK` or `GTX`, default `GTC` |
| `quantity` | `DECIMAL` | NO | Cannot be sent with `closePosition=true`(Close-All) |
| `price` | `DECIMAL` | NO | |
| `triggerPrice` | `DECIMAL` | NO | |
| `workingType` | `ENUM` | NO | triggerPrice triggered by: `MARK_PRICE`, `CONTRACT_PRICE`. Default `CONTRACT_PRICE` |
| `priceMatch` | `ENUM` | NO | only avaliable for LIMIT/STOP/TAKE_PROFIT order; can be set to `OPPONENT`/ `OPPONENT_5`/ `OPPONENT_10`/ `OPPONENT_20` : `/QUEUE`/ `QUEUE_5`/ `QUEUE_10`/ `QUEUE_20`; Can't be passed together with price. |
| `closePosition` | `STRING` | NO | `true`, `false`; Close-All, used with `STOP_MARKET` or `TAKE_PROFIT_MARKET`. |
| `priceProtect` | `STRING` | NO | `"true"` or `"false"`, default `"false"`. Used with `STOP_MARKET` or `TAKE_PROFIT_MARKET` order. when price reaches the triggerPrice, the difference rate between "MARK_PRICE" and "CONTRACT_PRICE" cannot be larger than the Price Protection Threshold of the symbol. |
| `reduceOnly` | `STRING` | NO | `"true"` or `"false"`. default `"false"`. Cannot be sent in Hedge Mode; cannot be sent with `closePosition=true` |
| `activatePrice` | `DECIMAL` | NO | Used with `TRAILING_STOP_MARKET` orders, default as the latest price(supporting different workingType) |
| `callbackRate` | `DECIMAL` | NO | Used with `TRAILING_STOP_MARKET` orders, min 0.1, max 10 where 1 for 1% |
| `clientAlgoId` | `STRING` | NO | A unique id among open orders. Automatically generated if not sent. Can only be string following the rule: `^[\.A-Z\:/a-z0-9_-]{1,36}$` |
| `newOrderRespType` | `ENUM` | NO | `"ACK"`, `"RESULT"`, default `"ACK"` |
| `selfTradePreventionMode` | `ENUM` | NO | `EXPIRE_TAKER`/ `EXPIRE_MAKER`/ `EXPIRE_BOTH`; default `NONE` |
| `goodTillDate` | `LONG` | NO | order cancel time for `timeInForce` GTD. |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes:**
> * Algo order with type `STOP`, parameter `timeInForce` can be sent (default `GTC`).
> * Algo order with type `TAKE_PROFIT`, parameter `timeInForce` can be sent (default `GTC`).
> 
> **Condition orders will be triggered when:**
> * If parameter `priceProtect` is sent as `true`:
>   * when price reaches the `triggerPrice`, the difference rate between "MARK_PRICE" and "CONTRACT_PRICE" cannot be larger than the "triggerProtect" of the symbol
>   * "triggerProtect" of a symbol can be got from `GET /fapi/v1/exchangeInfo`
> * `STOP`, `STOP_MARKET`:
>   * BUY: latest price ("MARK_PRICE" or "CONTRACT_PRICE") >= triggerPrice
>   * SELL: latest price ("MARK_PRICE" or "CONTRACT_PRICE") <= triggerPrice
> * `TAKE_PROFIT`, `TAKE_PROFIT_MARKET`:
>   * BUY: latest price ("MARK_PRICE" or "CONTRACT_PRICE") <= triggerPrice
>   * SELL: latest price ("MARK_PRICE" or "CONTRACT_PRICE") >= triggerPrice
> * `TRAILING_STOP_MARKET`:
>   * BUY: the lowest price after order placed <= activatePrice, and the latest price >= the lowest price * (1 + callbackRate)
>   * SELL: the highest price after order placed >= activatePrice, and the latest price <= the highest price * (1 - callbackRate)
>   * For `TRAILING_STOP_MARKET`, if you got such error code: `{"code": -2021, "msg": "Order would immediately trigger."}` means that the parameters you send do not meet the following requirements:
>     * BUY: `activatePrice` should be smaller than latest price.
>     * SELL: `activatePrice` should be larger than latest price.
> 
> * `STOP_MARKET`, `TAKE_PROFIT_MARKET` with `closePosition=true`:
>   * Follow the same rules for condition orders.
>   * If triggered, close all current long position (if SELL) or current short position (if BUY).
>   * Cannot be used with `quantity` paremeter
>   * Cannot be used with `reduceOnly` parameter
>   * In Hedge Mode, cannot be used with BUY orders in LONG position side. and cannot be used with SELL orders in SHORT position side
> * `selfTradePreventionMode` is only effective when `timeInForce` set to `IOC` or `GTC` or `GTD`.

### Response Example
```json
{
   "algoId": 2146760,
   "clientAlgoId": "6B2I9XVcJpCjqPAJ4YoFX7",
   "algoType": "CONDITIONAL",
   "orderType": "TAKE_PROFIT",
   "symbol": "BNBUSDT",
   "side": "SELL",
   "positionSide": "BOTH",
   "timeInForce": "GTC",
   "quantity": "0.01",
   "algoStatus": "NEW",
   "triggerPrice": "750.000",
   "price": "750.000",
   "icebergQuantity": null,
   "selfTradePreventionMode": "EXPIRE_MAKER",
   "workingType": "CONTRACT_PRICE",
   "priceMatch": "NONE",
   "closePosition": false,
   "priceProtect": false,
   "reduceOnly": false,
   "activatePrice": "", //TRAILING_STOP_MARKET order
   "callbackRate": "",  //TRAILING_STOP_MARKET order
   "createTime": 1750485492076,
   "updateTime": 1750485492076,
   "triggerTime": 0,
   "goodTillDate": 0
}
```

## Cancel Algo Order (TRADE)

**API Description:** Cancel an active algo (conditional) order, including TP/SL (Take Profit / Stop Loss) and trailing stop orders on USD-M Futures.

* **HTTP Request:** `DELETE /fapi/v1/algoOrder`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `algoId` | `LONG` | NO | |
| `clientAlgoId` | `STRING` | NO | |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Note:** Either `algoId` or `clientAlgoId` must be sent.

### Response Example
```json
{
   "algoId": 2146760,
   "clientAlgoId": "6B2I9XVcJpCjqPAJ4YoFX7",
   "code": "200",
   "msg": "success"
}
```

## Cancel All Algo Open Orders (TRADE)

**API Description:** Cancel all open algo (conditional) orders on a symbol, including TP/SL (Take Profit / Stop Loss) and trailing stop orders on USD-M Futures.

* **HTTP Request:** `DELETE /fapi/v1/algoOpenOrders`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `symbol` | `STRING` | YES | |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
{
  "code": 200, 
  "msg": "The operation of cancel all open order is done."
}
```

## Query Algo Order (USER_DATA)

**API Description:** Check the status of an algo (conditional) order, such as TP/SL (Take Profit / Stop Loss) or trailing stop orders on USD-M Futures.

> **Note:** These orders will not be found:
> * order status is `CANCELED` or `EXPIRED` AND order has NO filled trade AND created time + 3 days < current time
> * order create time + 90 days < current time

* **HTTP Request:** `GET /fapi/v1/algoOrder`
* **Request Weight:** 1

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `algoId` | `LONG` | NO | |
| `clientAlgoId` | `STRING` | NO | |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

> **Notes:**
> * Either `algoId` or `clientAlgoId` must be sent.
> * `algoId` is self-increment for each specific symbol

### Response Example
```json
{
   "algoId": 2146760,
   "clientAlgoId": "6B2I9XVcJpCjqPAJ4YoFX7",
   "algoType": "CONDITIONAL",
   "orderType": "TAKE_PROFIT",
   "symbol": "BNBUSDT",
   "side": "SELL",
   "positionSide": "BOTH",
   "timeInForce": "GTC",
   "quantity": "0.01",
   "algoStatus": "CANCELED",
   "actualOrderId": "",    // "" if not triggered; orderId if triggered
   "actualPrice": "0.00000",   // 0 if not triggered; average price if filled/partially filled
   "actualType": "LIMIT",  // optional field only when triggered
   "actualQty": "0.01",    // optional field only when filled/partially filled
   "triggerPrice": "750.000",
   "price": "750.000",
   "icebergQuantity": null,
   "tpOrderType": "",
   "selfTradePreventionMode": "EXPIRE_MAKER",
   "workingType": "CONTRACT_PRICE",
   "priceMatch": "NONE",
   "closePosition": false,
   "priceProtect": false,
   "reduceOnly": false,
   "createTime": 1750485492076,
   "updateTime": 1750514545091,
   "triggerTime": 0,
   "goodTillDate": 0
}
```

## Current All Algo Open Orders (USER_DATA)

**API Description:** Get all open algo (conditional) orders on a symbol, including TP/SL (Take Profit / Stop Loss) and trailing stop orders on USD-M Futures.

* **HTTP Request:** `GET /fapi/v1/openAlgoOrders`
* **Request Weight:** 1 for a single symbol; 40 when the symbol parameter is omitted
* **Note:** Careful when accessing this with no symbol.

### Request Parameters
| Name | Type | Mandatory | Description |
|---|---|---|---|
| `algoType` | `STRING` | NO | |
| `symbol` | `STRING` | NO | If the symbol is not sent, orders for all symbols will be returned in an array. |
| `algoId` | `LONG` | NO | |
| `recvWindow` | `LONG` | NO | |
| `timestamp` | `LONG` | YES | |

### Response Example
```json
[
   {
       "algoId": 2148627,
       "clientAlgoId": "MRumok0dkhrP4kCm12AHaB",
       "algoType": "CONDITIONAL",
       "orderType": "TAKE_PROFIT",
       "symbol": "BNBUSDT",
       "side": "SELL",
       "positionSide": "BOTH",
       "timeInForce": "GTC",
       "quantity": "0.01",
       "algoStatus": "NEW",
       "actualOrderId": "",
       "actualPrice": "0.00000",
       "triggerPrice": "750.000",
       "price": "750.000",
       "icebergQuantity": null,
       "tpTriggerPrice": "0.000",
       "tpPrice": "0.000",
       "slTriggerPrice": "0.000",
       "slPrice": "0.000",
       "tpOrderType": "",
       "selfTradePreventionMode": "EXPIRE_MAKER",
       "workingType": "CONTRACT_PRICE",
       "priceMatch": "NONE",
       "closePosition": false,
       "priceProtect": false,
       "reduceOnly": false,
       "createTime": 1750514941540,
       "updateTime": 1750514941540,
       "triggerTime": 0,
       "goodTillDate": 0
   }
]
```

# Websocket Streams

## Websocket Market Streams

The connection method for Websocket is:
* **Base Url:** `wss://fstream.binance.com`

Three routed endpoints are available based on data type:
* **Public** (high-frequency public market data): `wss://fstream.binance.com/public`
* **Market** (regular market data): `wss://fstream.binance.com/market`
* **Private** (user data): `wss://fstream.binance.com/private`

Two access modes are supported:
* **ws mode**: streams are composed in the URL path — `/ws/<streamName>`
* **stream mode**: streams are passed via query parameters — `/stream?streams=<streamName1>/<streamName2>/<streamName3>`

**Examples:**
* `wss://fstream.binance.com/market/ws/bnbusdt@aggTrade`
* `wss://fstream.binance.com/public/ws/bnbusdt@depth/ethusdt@depth`
* `wss://fstream.binance.com/market/stream?streams=bnbusdt@aggTrade/btcusdt@markPrice`

> **Important:** Connections that do not include a routed path (`/public`, `/market`, or `/private`) will only receive data from the Public endpoint. Streams belonging to `/market` or `/private` will not push data on unrouted connections. For example, `wss://fstream.binance.com/ws/btcusdt@depth` will continue to work (since `@depth` belongs to `/public`), but `wss://fstream.binance.com/ws/btcusdt@markPrice` will not (since `@markPrice` belongs to `/market`).

### General Notes
* Combined stream events are wrapped as follows: `{"stream":"<streamName>","data":<rawPayload>}`
* All symbols for streams are lowercase.
* A single connection is only valid for 24 hours; expect to be disconnected at the 24 hour mark.
* The websocket server will send a ping frame every 3 minutes. If the websocket server does not receive a pong frame back from the connection within a 10 minute period, the connection will be disconnected. Unsolicited pong frames are allowed (the client can send pong frames at a frequency higher than every 15 minutes to maintain the connection).
* WebSocket connections have a limit of 10 incoming messages per second.
* A connection that goes beyond the limit will be disconnected; IPs that are repeatedly disconnected may be banned.
* A single connection can listen to a maximum of 1024 streams.
* Considering the possible data latency from RESTful endpoints during an extremely volatile market, it is highly recommended to get the order status, position, etc from the Websocket user data stream.

## Important WebSocket Change Notice — Base URL Split & Migration

**Background:**
Due to sustained heavy traffic, the WebSocket URL structure is upgraded by introducing a root plus dedicated entry points for Public / Market / Private traffic. This separation improves stability, scalability, and operational isolation across different data types.

### What's New
3 new WebSocket base URLs (Root + routed paths):
* **Public** (high-frequency public market data): `wss://fstream.binance.com/public`
* **Market** (regular market data): `wss://fstream.binance.com/market`
* **Private** (user data): `wss://fstream.binance.com/private`

Two access modes are supported:
* **ws mode**: streams are composed in the URL path
* **stream mode**: streams are passed via query (e.g., `?streams=`) — private uses `listenKey`/`events`

> **Note:** Combined streams remain supported. Private supports `listenKey` + `events` subscription (multiple listenKeys and multiple events).

### Subscription Examples

**Public / Market: combined subscriptions**
* ws mode (path-based):
  * `wss://fstream.binance.com/public/ws/bnbusdt@depth/ethusdt@depth`
  * `wss://fstream.binance.com/market/ws/btcusdt@aggTrade/ethusdt@aggTrade`
* stream mode (query-based):
  * `wss://fstream.binance.com/market/stream?streams=bnbusdt@aggTrade/btcusdt@markPrice`
  * `wss://fstream.binance.com/public/stream?streams=btcusdt@depth/ethusdt@depth`

**Private: listenKey & events**
* ws mode (listenKey + events):
  * `wss://fstream.binance.com/private/ws?listenKey=<listenKey1>&events=ORDER_TRADE_UPDATE/ACCOUNT_UPDATE`
* stream mode (multiple listenKeys + events):
  * `wss://fstream.binance.com/private/stream?listenKey=<listenKey1>&events=ORDER_TRADE_UPDATE&listenKey=<listenKey2>&events=ACCOUNT_UPDATE`

*`JSON SUBSCRIBE` is also supported; params may include market/public streams and listenKey event items.*

### Endpoint & Stream Mapping (Excerpt)

**Public (high-frequency public data)**
* Individual Symbol Book Ticker: `<symbol>@bookTicker`
* All Book Tickers: `!bookTicker`
* Partial Book Depth: `<symbol>@depth<levels>` (supports `@500ms` / `@100ms`)
* Diff. Book Depth: `<symbol>@depth` (supports `@500ms` / `@100ms`)

**Market (regular market data)**
* Aggregate Trades: `<symbol>@aggTrade`
* Mark Price: `<symbol>@markPrice` or `<symbol>@markPrice@1s`
* Mark Price (All market): `!markPrice@arr` or `!markPrice@arr@1s`
* Kline/Candlestick: `<symbol>@kline_<interval>`
* Continuous Kline: `<pair>_<contractType>@continuousKline_<interval>`
* Mini Ticker: `<symbol>@miniTicker`; All: `!miniTicker@arr`
* Ticker: `<symbol>@ticker`; All: `!ticker@arr`
* Liquidations: `<symbol>@forceOrder`; All: `!forceOrder@arr`
* Composite Index: `<symbol>@compositeIndex`
* Contract Info: `!contractInfo`
* Multi-Assets Mode Asset Index: `!assetIndex@arr` or `<assetSymbol>@assetIndex`

### Compatibility & Migration Guidance
* **Deadline:** Legacy URLs will remain available until **2026-04-23**, after which they will be permanently decommissioned. Users are strongly encouraged to migrate to the new `/public`, `/market`, `/private` endpoints before this date.
* After the upgrade, any connections not migrated will **ONLY** be able to receive data from `wss://fstream.binance.com/public`. Channels under `/market` and `/private` will stop pushing data.
* **Recommended migration order:**
  1. High-frequency order book & core public feeds → `/public`
  2. Regular market feeds (markPrice/kline/ticker, etc.) → `/market`
  3. User data feeds (listenKey-based) → `/private`
* **Client / SDK recommendations:**
  * Split connections by traffic type (separate public/market/private sessions) to reduce per-connection load and jitter.
  * For combined subscriptions, prefer stream mode (`?streams=`; private uses `listenKey`/`events`).

## Live Subscribing/Unsubscribing to streams

The following data can be sent through the websocket instance in order to subscribe/unsubscribe from streams. The `id` used in the JSON payloads is an unsigned INT used as an identifier to uniquely identify the messages going back and forth.

### Subscribe to a stream
**Request**
```json
{    
  "method": "SUBSCRIBE",    
  "params": [   
    "btcusdt@aggTrade",    
    "btcusdt@depth"     
  ],    
  "id": 1   
}
```
**Response**
```json
{
  "result": null,
  "id": 1
}
```

### Unsubscribe to a stream
**Request**
```json
{   
  "method": "UNSUBSCRIBE",    
  "params": [    
    "btcusdt@depth"   
  ],    
  "id": 312   
}
```
**Response**
```json
{
  "result": null,
  "id": 312
}
```

### Listing Subscriptions
**Request**
```json
{   
  "method": "LIST_SUBSCRIPTIONS",    
  "id": 3   
}     
```
**Response**
```json
{
  "result": [
    "btcusdt@aggTrade"
  ],
  "id": 3
}
```

### Setting Properties
Currently, the only property can be set is to set whether combined stream payloads are enabled are not. The combined property is set to false when connecting using `/ws/` ("raw streams") and true when connecting using `/stream/`.

**Request**
```json
{    
  "method": "SET_PROPERTY",    
  "params": [   
    "combined",    
    true   
  ],    
  "id": 5   
}
```
**Response**
```json
{
  "result": null,
  "id": 5
}
```

### Retrieving Properties
**Request**
```json
{   
  "method": "GET_PROPERTY",    
  "params": [   
    "combined"   
  ],    
  "id": 2   
}   
```
**Response**
```json
{
  "result": true, // Indicates that combined is set to true.
  "id": 2
}
```

### Error Messages
| Error Message | Description |
|---|---|
| `{"code": 0, "msg": "Unknown property"}` | Parameter used in the SET_PROPERTY or GET_PROPERTY was invalid |
| `{"code": 1, "msg": "Invalid value type: expected Boolean"}` | Value should only be `true` or `false` |
| `{"code": 2, "msg": "Invalid request: property name must be a string"}` | Property name provided was invalid |
| `{"code": 2, "msg": "Invalid request: request ID must be an unsigned integer"}` | Parameter id had to be provided or the value provided in the id parameter is an unsupported type |
| `{"code": 2, "msg": "Invalid request: unknown variant %s, expected one of SUBSCRIBE, UNSUBSCRIBE, LIST_SUBSCRIPTIONS, SET_PROPERTY, GET_PROPERTY at line 1 column 28"}` | Possible typo in the provided method or provided method was neither of the expected values |
| `{"code": 2, "msg": "Invalid request: too many parameters"}` | Unnecessary parameters provided in the data |
| `{"code": 2, "msg": "Invalid request: property name must be a string"}` | Property name was not provided |
| `{"code": 2, "msg": "Invalid request: missing field method at line 1 column 73"}` | `method` was not provided in the data |
| `{"code": 3, "msg": "Invalid JSON: expected value at line %s column %s"}` | JSON data sent has incorrect syntax. |

## Aggregate Trade Streams

**Stream Description:** The Aggregate Trade Streams push market trade information that is aggregated for fills with same price and taking side every 100 milliseconds. Only market trades will be aggregated, which means the insurance fund trades and ADL trades won't be aggregated.

* **URL PATH:** `/market`
* **Stream Name:** `<symbol>@aggTrade`
* **Update Speed:** 100ms
* **Note:** Retail Price Improvement(RPI) orders are aggregated into field `q` and without special tags to be distinguished.

### Response Example
```json
{
  "e": "aggTrade",  // Event type
  "E": 123456789,   // Event time
  "s": "BTCUSDT",   // Symbol
  "a": 5933014,     // Aggregate trade ID
  "p": "0.001",     // Price
  "q": "100",       // Quantity with all the market trades
  "nq": "100",      // Normal quantity without the trades involving RPI orders
  "f": 100,         // First trade ID
  "l": 105,         // Last trade ID
  "T": 123456785,   // Trade time
  "m": true,        // Is the buyer the market maker?
  "st": 1           // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, the payload is appended with a new `st` field (1 = UM, 2 = CM).

## Mark Price Stream

**Stream Description:** Mark price and funding rate for a single symbol pushed every 3 seconds or every second.

* **URL PATH:** `/market`
* **Stream Name:** `<symbol>@markPrice` or `<symbol>@markPrice@1s`
* **Update Speed:** 3000ms or 1000ms

### Response Example
```json
{
  "e": "markPriceUpdate",     // Event type
  "E": 1562305380000,         // Event time
  "s": "BTCUSDT",             // Symbol
  "p": "11794.15000000",      // Mark price
  "ap": "11794.15000000",     // Mark price moving average
  "i": "11784.62659091",      // Index price
  "P": "11784.25641265",      // Estimated Settle Price, only useful in the last hour before the settlement starts
  "r": "0.00038167",          // Funding rate
  "T": 1562306400000,         // Next funding time
  "st": 1                     // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, the payload is appended with a new `st` field (1 = UM, 2 = CM); both fstream and dstream may subscribe to either UM or CM symbols on this stream.

## Mark Price Stream for All market

**Stream Description:** Mark price and funding rate for all symbols pushed every 3 seconds or every second.

* **URL PATH:** `/market`
* **Stream Name:** `!markPrice@arr` or `!markPrice@arr@1s`
* **Update Speed:** 3000ms or 1000ms
* **Note:** TradFi symbols will be pushed through a seperate message.

### Response Example
```json
[ 
  {
    "e": "markPriceUpdate",     // Event type
    "E": 1562305380000,         // Event time
    "s": "BTCUSDT",             // Symbol
    "p": "11185.87786614",      // Mark price
    "ap": "11185.87786614",     // Mark price moving average
    "i": "11784.62659091",      // Index price
    "P": "11784.25641265",      // Estimated Settle Price, only useful in the last hour before the settlement starts
    "r": "0.00030000",          // Funding rate
    "T": 1562306400000,         // Next funding time
    "st": 1                     // (After CM migration) Symbol type: 1 = UM, 2 = CM
  }
]
```
> **Note:** After CM migration, the payload is appended with a new `st` field (1 = UM, 2 = CM); both fstream and dstream may subscribe to either UM or CM symbols on this stream.

## Kline/Candlestick Streams

**Stream Description:** The Kline/Candlestick Stream push updates to the current klines/candlestick every 250 milliseconds (if existing).
Kline/Candlestick chart intervals: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`, `1M` (m -> minutes; h -> hours; d -> days; w -> weeks; M -> months)

* **URL PATH:** `/market`
* **Stream Name:** `<symbol>@kline_<interval>`
* **Update Speed:** 250ms

### Response Example
```json
{
  "e": "kline",     // Event type
  "E": 1638747660000,   // Event time
  "s": "BTCUSDT",    // Symbol
  "k": {
    "t": 1638747660000, // Kline start time
    "T": 1638747719999, // Kline close time
    "s": "BTCUSDT",  // Symbol
    "i": "1m",      // Interval
    "f": 100,       // First trade ID
    "L": 200,       // Last trade ID
    "o": "0.0010",  // Open price
    "c": "0.0020",  // Close price
    "h": "0.0025",  // High price
    "l": "0.0015",  // Low price
    "v": "1000",    // Base asset volume
    "n": 100,       // Number of trades
    "x": false,     // Is this kline closed?
    "q": "1.0000",  // Quote asset volume
    "V": "500",     // Taker buy base asset volume
    "Q": "0.500",   // Taker buy quote asset volume
    "B": "123456"   // Ignore
  }
}
```
> **Note:** After CM migration, both fstream and dstream may subscribe to either UM or CM symbols on this stream.

## Continuous Contract Kline/Candlestick Streams

**Stream Description:** Contract type: `perpetual`, `current_quarter`, `next_quarter`, `tradifi_perpetual`. 
Kline/Candlestick chart intervals: `1s`, `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`, `1M` (s -> seconds; m -> minutes; h -> hours; d -> days; w -> weeks; M -> months)

* **URL PATH:** `/market`
* **Stream Name:** `<pair>_<contractType>@continuousKline_<interval>`
* **Update Speed:** 250ms

### Response Example
```json
{
  "e":"continuous_kline",   // Event type
  "E":1607443058651,        // Event time
  "ps":"BTCUSDT",           // Pair
  "ct":"PERPETUAL",         // Contract type
  "k":{
    "t":1607443020000,      // Kline start time
    "T":1607443079999,      // Kline close time
    "i":"1m",               // Interval
    "f":116467658886,       // First updateId
    "L":116468012423,       // Last updateId
    "o":"18787.00",         // Open price
    "c":"18804.04",         // Close price
    "h":"18804.04",         // High price
    "l":"18786.54",         // Low price
    "v":"197.664",          // volume
    "n": 543,               // Number of trades
    "x":false,              // Is this kline closed?
    "q":"3715253.19494",    // Quote asset volume
    "V":"184.769",          // Taker buy volume
    "Q":"3472925.84746",    // Taker buy quote asset volume
    "B":"0"                 // Ignore
  }
}
```
> **Note:** After CM migration, both fstream and dstream may subscribe to either UM or CM symbols on this stream.

## Individual Symbol Mini Ticker Stream

**Stream Description:** 24hr rolling window mini-ticker statistics for a single symbol. These are NOT the statistics of the UTC day, but a 24hr rolling window from requestTime to 24hrs before.

* **URL PATH:** `/market`
* **Stream Name:** `<symbol>@miniTicker`
* **Update Speed:** 2s

### Response Example
```json
{
  "e": "24hrMiniTicker",  // Event type
  "E": 123456789,         // Event time
  "s": "BTCUSDT",         // Symbol
  "c": "0.0025",          // Close price
  "o": "0.0010",          // Open price
  "h": "0.0025",          // High price
  "l": "0.0010",          // Low price
  "v": "10000",           // Total traded base asset volume
  "q": "18",              // Total traded quote asset volume
  "ps": "BTCUSDT",        // (After CM migration) Pair symbol
  "st": 1                 // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, the payload is appended with a new `st` field (1 = UM, 2 = CM) and a new `ps` field (pair symbol).

## All Market Tickers Streams

**Stream Description:** 24hr rolling window ticker statistics for all symbols. These are NOT the statistics of the UTC day, but a 24hr rolling window from requestTime to 24hrs before. Note that only tickers that have changed will be present in the array.

* **URL PATH:** `/market`
* **Stream Name:** `!ticker@arr`
* **Update Speed:** 1000ms

### Response Example
```json
[
  {
    "e": "24hrTicker",  // Event type
    "E": 123456789,     // Event time
    "s": "BTCUSDT",     // Symbol
    "p": "0.0015",      // Price change
    "P": "250.00",      // Price change percent
    "w": "0.0018",      // Weighted average price
    "c": "0.0025",      // Last price
    "Q": "10",          // Last quantity
    "o": "0.0010",      // Open price
    "h": "0.0025",      // High price
    "l": "0.0010",      // Low price
    "v": "10000",       // Total traded base asset volume
    "q": "18",          // Total traded quote asset volume
    "O": 0,             // Statistics open time
    "C": 86400000,      // Statistics close time
    "F": 0,             // First trade ID
    "L": 18150,         // Last trade Id
    "n": 18151,         // Total number of trades
    "ps": "BTCUSDT",    // (After CM migration) Pair symbol
    "st": 1             // (After CM migration) Symbol type: 1 = UM, 2 = CM
  }
]
```
> **Note:** After CM migration, this stream pushes the merged UM + CM universe (subscribable on both fstream and dstream); each payload is appended with a new `st` field (1 = UM, 2 = CM) and a new `ps` field (pair symbol).

## Individual Symbol Ticker Streams

**Stream Description:** 24hr rolling window ticker statistics for a single symbol. These are NOT the statistics of the UTC day, but a 24hr rolling window from requestTime to 24hrs before.

* **URL PATH:** `/market`
* **Stream Name:** `<symbol>@ticker`
* **Update Speed:** 2000ms

### Response Example
```json
{
  "e": "24hrTicker",  // Event type
  "E": 123456789,     // Event time
  "s": "BTCUSDT",     // Symbol
  "p": "0.0015",      // Price change
  "P": "250.00",      // Price change percent
  "w": "0.0018",      // Weighted average price
  "c": "0.0025",      // Last price
  "Q": "10",          // Last quantity
  "o": "0.0010",      // Open price
  "h": "0.0025",      // High price
  "l": "0.0010",      // Low price
  "v": "10000",       // Total traded base asset volume
  "q": "18",          // Total traded quote asset volume
  "O": 0,             // Statistics open time
  "C": 86400000,      // Statistics close time
  "F": 0,             // First trade ID
  "L": 18150,         // Last trade Id
  "n": 18151,         // Total number of trades
  "ps": "BTCUSDT",    // (After CM migration) Pair symbol
  "st": 1             // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, the payload is appended with a new `st` field (1 = UM, 2 = CM) and a new `ps` field (pair symbol).

## All Market Mini Tickers Stream

**Stream Description:** 24hr rolling window mini-ticker statistics for all symbols. These are NOT the statistics of the UTC day, but a 24hr rolling window from requestTime to 24hrs before. Note that only tickers that have changed will be present in the array.

* **URL PATH:** `/market`
* **Stream Name:** `!miniTicker@arr`
* **Update Speed:** 1000ms

### Response Example
```json
[  
  {
    "e": "24hrMiniTicker",  // Event type
    "E": 123456789,         // Event time
    "s": "BTCUSDT",         // Symbol
    "c": "0.0025",          // Close price
    "o": "0.0010",          // Open price
    "h": "0.0025",          // High price
    "l": "0.0010",          // Low price
    "v": "10000",           // Total traded base asset volume
    "q": "18",               // Total traded quote asset volume
    "ps": "BTCUSDT",              // (After CM migration) Pair symbol
    "st": 1              // (After CM migration) Symbol type: 1 = UM, 2 = CM
  }
]
```
> **Note:** After CM migration, this stream pushes the merged UM + CM universe (subscribable on both fstream and dstream); each payload is appended with a new `st` field (1 = UM, 2 = CM) and a new `ps` field (pair symbol).

## Individual Symbol Book Ticker Streams

**Stream Description:** Pushes any update to the best bid or ask's price or quantity in real-time for a specified symbol.

* **URL PATH:** `/public`
* **Stream Name:** `<symbol>@bookTicker`
* **Update Speed:** Real-time
* **Note:** Retail Price Improvement(RPI) orders are not visible and excluded in the response message.

### Response Example
```json
{
  "e":"bookTicker",         // event type
  "u":400900217,            // order book updateId
  "s":"BNBUSDT",            // symbol
  "ps":"BNBUSDT",           // pair (After CM migration)
  "E": 1568014460893,       // event time
  "T": 1568014460891,       // transaction time
  "b":"25.35190000",        // best bid price
  "B":"31.21000000",        // best bid qty
  "a":"25.36520000",        // best ask price
  "A":"40.66000000",        // best ask qty
  "st": 1                   // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, the payload is appended with a new `st` field (1 = UM, 2 = CM).

## All Book Tickers Stream

**Stream Description:** Pushes any update to the best bid or ask's price or quantity in real-time for all symbols.

* **URL PATH:** `/public`
* **Stream Name:** `!bookTicker`
* **Update Speed:** 5s
* **Note:** Retail Price Improvement(RPI) orders are not visible and excluded in the response message.

### Response Example
```json
{
  "e":"bookTicker",         // event type
  "u":400900217,            // order book updateId
  "E": 1568014460893,       // event time
  "T": 1568014460891,       // transaction time
  "s":"BNBUSDT",            // symbol
  "b":"25.35190000",        // best bid price
  "B":"31.21000000",        // best bid qty
  "a":"25.36520000",        // best ask price
  "A":"40.66000000",        // best ask qty
  "ps": "BTCUSDT",          // (After CM migration) Pair symbol
  "st": 1                   // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, this stream pushes the merged UM + CM universe (subscribable on both fstream and dstream); each payload is appended with a new `st` field (1 = UM, 2 = CM) and a new `ps` field (pair symbol).

## Liquidation Order Streams

**Stream Description:** The Liquidation Order Snapshot Streams push force liquidation order information for specific symbol. For each symbol，only the largest one liquidation order within 1000ms will be pushed as the snapshot. If no liquidation happens in the interval of 1000ms, no stream will be pushed.

* **URL PATH:** `/market`
* **Stream Name:** `<symbol>@forceOrder`
* **Update Speed:** 1000ms

### Response Example
```json
{
    "e":"forceOrder",                   // Event Type
    "E":1568014460893,                  // Event Time
    "o":{
        "s":"BTCUSDT",                   // Symbol
        "S":"SELL",                      // Side
        "o":"LIMIT",                     // Order Type
        "f":"IOC",                       // Time in Force
        "q":"0.014",                     // Original Quantity
        "p":"9910",                      // Price
        "ap":"9910",                     // Average Price
        "X":"FILLED",                    // Order Status
        "l":"0.014",                     // Order Last Filled Quantity
        "z":"0.014",                     // Order Filled Accumulated Quantity
        "T":1568014460893                // Order Trade Time
    }
}
```

## All Market Liquidation Order Streams

**Stream Description:** The All Liquidation Order Snapshot Streams push force liquidation order information for all symbols in the market. For each symbol，only the largest one liquidation order within 1000ms will be pushed as the snapshot. If no liquidation happens in the interval of 1000ms, no stream will be pushed.

* **URL PATH:** `/market`
* **Stream Name:** `!forceOrder@arr`
* **Update Speed:** 1000ms

### Response Example
```json
{
    "e":"forceOrder",                   // Event Type
    "E":1568014460893,                  // Event Time
    "o":{
        "s":"BTCUSDT",                   // Symbol
        "S":"SELL",                      // Side
        "o":"LIMIT",                     // Order Type
        "f":"IOC",                       // Time in Force
        "q":"0.014",                     // Original Quantity
        "p":"9910",                      // Price
        "ap":"9910",                     // Average Price
        "X":"FILLED",                    // Order Status
        "l":"0.014",                     // Order Last Filled Quantity
        "z":"0.014",                     // Order Filled Accumulated Quantity
        "T":1568014460893                // Order Trade Time
    },
    "ps": "BTCUSDT",              // (After CM migration) Pair symbol
    "st": 1              // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, this stream pushes the merged UM + CM universe (subscribable on both fstream and dstream); each payload is appended with a new `st` field (1 = UM, 2 = CM) and a new `ps` field (pair symbol).

## Partial Book Depth Streams

**Stream Description:** Top `<levels>` bids and asks, Valid `<levels>` are 5, 10, or 20.

* **URL PATH:** `/public`
* **Stream Name:** `<symbol>@depth<levels>` OR `<symbol>@depth<levels>@500ms` OR `<symbol>@depth<levels>@100ms`.
* **Update Speed:** 250ms, 500ms or 100ms
* **Note:** Retail Price Improvement(RPI) orders are not visible and excluded in the response message.

### Response Example
```json
{
  "e": "depthUpdate", // Event type
  "E": 1571889248277, // Event time
  "T": 1571889248276, // Transaction time
  "s": "BTCUSDT",
  "U": 390497796,     // First update ID in event
  "u": 390497878,     // Final update ID in event
  "pu": 390497794,    // Final update Id in last stream(ie `u` in last stream)
  "b": [              // Bids to be updated
    [
      "7403.89",      // Price Level to be updated
      "0.002"         // Quantity
    ],
    [
      "7403.90",
      "3.906"
    ],
    [
      "7404.00",
      "1.428"
    ],
    [
      "7404.85",
      "5.239"
    ],
    [
      "7405.43",
      "2.562"
    ]
  ],
  "a": [              // Asks to be updated
    [
      "7405.96",      // Price level to be
      "3.340"         // Quantity
    ],
    [
      "7406.63",
      "4.525"
    ],
    [
      "7407.08",
      "2.475"
    ],
    [
      "7407.15",
      "4.800"
    ],
    [
      "7407.20",
      "0.175"
    ]
  ],
  "ps": "BTCUSDT",              // (After CM migration) Pair symbol
  "st": 1              // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, the payload is appended with a new `st` field (1 = UM, 2 = CM) and a new `ps` field (pair symbol).

## Diff. Book Depth Streams

**Stream Description:** Bids and asks, pushed every 250 milliseconds, 500 milliseconds, 100 milliseconds (if existing)

* **URL PATH:** `/public`
* **Stream Name:** `<symbol>@depth` OR `<symbol>@depth@500ms` OR `<symbol>@depth@100ms`
* **Update Speed:** 250ms, 500ms, 100ms
* **Note:** Retail Price Improvement(RPI) orders are not visible and excluded in the response message.

### Response Example
```json
{
  "e": "depthUpdate", // Event type
  "E": 123456789,     // Event time
  "T": 123456788,     // Transaction time 
  "s": "BTCUSDT",     // Symbol
  "U": 157,           // First update ID in event
  "u": 160,           // Final update ID in event
  "pu": 149,          // Final update Id in last stream(ie `u` in last stream)
  "b": [              // Bids to be updated
    [
      "0.0024",       // Price level to be updated
      "10"            // Quantity
    ]
  ],
  "a": [              // Asks to be updated
    [
      "0.0026",       // Price level to be updated
      "100"          // Quantity
    ]
  ],
  "ps": "BTCUSDT",              // (After CM migration) Pair symbol
  "st": 1              // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, the payload is appended with a new `st` field (1 = UM, 2 = CM) and a new `ps` field (pair symbol).

## RPI Diff. Book Depth Streams

**Stream Description:** Bids and asks including RPI orders, pushed every 500 milliseconds.

* **URL PATH:** `/public`
* **Stream Name:** `<symbol>@rpiDepth@500ms`
* **Update Speed:** 500ms
* **Note:** RPI(Retail Price Improvement) orders are included and aggreated in the response message. When the quantity of a price level to be updated is equal to 0, it means either all quotations for this price have been filled/canceled, or the quantity of crossed RPI orders for this price are hidden

### Response Example
```json
{
  "e": "depthUpdate", // Event type
  "E": 123456789,     // Event time
  "T": 123456788,     // Transaction time 
  "s": "BTCUSDT",     // Symbol
  "U": 157,           // First update ID in event
  "u": 160,           // Final update ID in event
  "pu": 149,          // Final update Id in last stream(ie `u` in last stream)
  "b": [              // Bids to be updated
    [
      "0.0024",       // Price level to be updated
      "10"            // Quantity
    ]
  ],
  "a": [              // Asks to be updated
    [
      "0.0026",       // Price level to be updated
      "100"          // Quantity
    ]
  ],
  "ps": "BTCUSDT",              // (After CM migration) Pair symbol
  "st": 1              // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, the payload is appended with a new `st` field (1 = UM, 2 = CM) and a new `ps` field (pair symbol).

### How to manage a local order book correctly
1. Open a stream to `wss://fstream.binance.com/public/stream?streams=btcusdt@depth`.
2. Buffer the events you receive from the stream. For same price, latest received update covers the previous one.
3. Get a depth snapshot from `https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=1000` .
4. Drop any event where `u` is < `lastUpdateId` in the snapshot.
5. The first processed event should have `U` <= `lastUpdateId` AND `u` >= `lastUpdateId`
   * `U` = `firstUpdateId` (the first update ID) from the WebSocket stream.
   * `u` = `finalUpdateId` (the last update ID) from the WebSocket stream.
   * `lastUpdateId` = the update ID you got from the REST depth snapshot.
6. While listening to the stream, each new event's `pu` should be equal to the previous event's `u`, otherwise initialize the process from step 3.
7. The data in each event is the absolute quantity for a price level.
8. If the quantity is 0, remove the price level.
9. Receiving an event that removes a price level that is not in your local order book can happen and is normal.

## Composite Index Symbol Information Streams

**Stream Description:** Composite index information for index symbols pushed every second.

* **URL PATH:** `/market`
* **Stream Name:** `<symbol>@compositeIndex`
* **Update Speed:** 1000ms

### Response Example
```json
{
  "e":"compositeIndex",     // Event type
  "E":1602310596000,        // Event time
  "s":"DEFIUSDT",           // Symbol
  "p":"554.41604065",       // Price
  "C":"baseAsset",
  "c":[                     // Composition
    {
        "b":"BAL",          // Base asset
        "q":"USDT",         // Quote asset
        "w":"1.04884844",   // Weight in quantity
        "W":"0.01457800",   // Weight in percentage
        "i":"24.33521021"   // Index price
    },
    {
        "b":"BAND",
        "q":"USDT" ,
        "w":"3.53782729",
        "W":"0.03935200",
        "i":"7.26420084"
    }
  ]
}
```

## Contract Info Stream

**Stream Description:** ContractInfo stream pushes when contract info updates(listing/settlement/contract bracket update). `bks` field only shows up when bracket gets updated.

* **URL PATH:** `/market`
* **Stream Name:** `!contractInfo`
* **Update Speed:** Real-time

### Response Example
```json
{
    "e":"contractInfo",          // Event Type
    "E":1669356423908,           // Event Time
    "s":"IOTAUSDT",              // Symbol
    "ct":"PERPETUAL",            // Contract type
    "dt":4133404800000,          // Delivery date time 
    "ot":1569398400000,          // onboard date time 
    "cs":"TRADING",              // Contract status 
    "bks":[
        {
            "bs":1,              // Notional bracket
            "bnf":0,             // Floor notional of this bracket
            "bnc":5000,          // Cap notional of this bracket
            "mmr":0.01,          // Maintenance ratio for this bracket
            "cf":0,              // Auxiliary number for quick calculation 
            "mi":21,             // Min leverage for this bracket
            "ma":50              // Max leverage for this bracket
        },
        {
            "bs":2,
            "bnf":5000,
            "bnc":25000,
            "mmr":0.025,
            "cf":75,
            "mi":11,
            "ma":20
        }
    ],
    "st": 1              // (After CM migration) Symbol type: 1 = UM, 2 = CM
}
```
> **Note:** After CM migration, this stream pushes the merged UM + CM universe (subscribable on both fstream and dstream); each payload is appended with a new `st` field (1 = UM, 2 = CM).

## Asset Index

**CM-UM Integration (Effective 2026-06-30):** Renamed from Multi-Assets Mode Asset Index. The stream `!assetIndex@arr` now additionally pushes COIN-M settlement-asset price index entries (e.g., BTCUSD, ETHUSD, BNBUSD). The on-the-wire stream key is unchanged; existing subscriptions continue to work. See Important CM-UM Integration Notice for details.

**Stream Description:** Asset index price.

* **URL PATH:** `/market`
* **Stream Name:** `!assetIndex@arr` OR `<assetSymbol>@assetIndex`
* **Update Speed:** 1s

### Response Example
```json
[
    {
      "e":"assetIndexUpdate",
      "E":1686749230000,
      "s":"ADAUSD",           // asset index symbol
      "i":"0.27462452",       // index price
      "b":"0.10000000",       // bid buffer
      "a":"0.10000000",       // ask buffer
      "B":"0.24716207",       // bid rate
      "A":"0.30208698",       // ask rate
      "q":"0.05000000",       // auto exchange bid buffer
      "g":"0.05000000",       // auto exchange ask buffer 
      "Q":"0.26089330",       // auto exchange bid rate
      "G":"0.28835575"        // auto exchange ask rate
    },
    {
      "e":"assetIndexUpdate",
      "E":1686749230000,
      "s":"USDTUSD",
      "i":"0.99987691",  
      "b":"0.00010000",
      "a":"0.00010000",
      "B":"0.99977692",
      "A":"0.99997689",
      "q":"0.00010000",
      "g":"0.00010000",
      "Q":"0.99977692",
      "G":"0.99997689"
    }
]
```

## Trading Session Stream

**Stream Description:** Trading session information for the underlying assets of TradFi Perpetual contracts, covering the U.S. equity market, Korean equity market, and the commodity market, is updated every second. Trading session information for different underlying markets is pushed in separate messages.

* **Event type:**
  * `EquityUpdate`: Session types for the U.S. equity market include "PRE_MARKET", "REGULAR", "AFTER_MARKET", "OVERNIGHT", and "NO_TRADING".
  * `CommodityUpdate`: Session types for the commodity market include "REGULAR" and "NO_TRADING".
  * `KR_EquityUpdate`: Session types for the Korean equity market include "REGULAR" and "NO_TRADING".

* **URL PATH:** `/market`
* **Stream Name:** `tradingSession`
* **Update Speed:** 1s

### Response Example
```json
{
  "e": "EquityUpdate",      // Event type, can also be CommodityUpdate or KR_EquityUpdate
  "E": 1765244143062,       // Event time
  "t": 1765242000000,       // Session start time
  "T": 1765270800000,       // Session end time
  "S": "OVERNIGHT"          // Session type
}
```

## Error Codes

Errors consist of two parts: an error code and a message. Codes are universal, but messages can vary.

**Error JSON Payload Example:**
```json
{
  "code": -1121,
  "msg": "Invalid symbol."
}
```

### 10xx - General Server or Network issues

| Code | Message | Description |
|---|---|---|
| `-1000` | `UNKNOWN` | An unknown error occured while processing the request. |
| `-1001` | `DISCONNECTED` | Internal error; unable to process your request. Please try again. |
| `-1002` | `UNAUTHORIZED` | You are not authorized to execute this request. |
| `-1003` | `TOO_MANY_REQUESTS` | Too many requests; current limit is `%s` requests per minute. Please use the websocket for live updates to avoid polling the API.<br>Way too many requests; IP banned until `%s`. Please use the websocket for live updates to avoid bans. |
| `-1004` | `DUPLICATE_IP` | This IP is already on the white list |
| `-1005` | `NO_SUCH_IP` | No such IP has been white listed |
| `-1006` | `UNEXPECTED_RESP` | An unexpected response was received from the message bus. Execution status unknown. |
| `-1007` | `TIMEOUT` | Timeout waiting for response from backend server. Send status unknown; execution status unknown. |
| `-1008` | `Request Throttled` | Server is currently overloaded with other requests. Please try again in a few minutes.<br>Request throttled by system-level protection. Reduce-only/close-position orders are exempt. Please try again. |
| `-1010` | `ERROR_MSG_RECEIVED` | ERROR_MSG_RECEIVED. |
| `-1011` | `NON_WHITE_LIST` | This IP cannot access this route. |
| `-1013` | `INVALID_MESSAGE` | INVALID_MESSAGE. |
| `-1014` | `UNKNOWN_ORDER_COMPOSITION` | Unsupported order combination. |
| `-1015` | `TOO_MANY_ORDERS` | Too many new orders.<br>Too many new orders; current limit is `%s` orders per `%s`. |
| `-1016` | `SERVICE_SHUTTING_DOWN` | This service is no longer available. |
| `-1020` | `UNSUPPORTED_OPERATION` | This operation is not supported. |
| `-1021` | `INVALID_TIMESTAMP` | Timestamp for this request is outside of the recvWindow.<br>Timestamp for this request was 1000ms ahead of the server's time. |
| `-1022` | `INVALID_SIGNATURE` | Signature for this request is not valid. |
| `-1023` | `START_TIME_GREATER_THAN_END_TIME` | Start time is greater than end time. |
| `-1099` | `NOT_FOUND` | Not found, unauthenticated, or unauthorized. |

### 11xx - Request issues

| Code | Message | Description |
|---|---|---|
| `-1100` | `ILLEGAL_CHARS` | Illegal characters found in a parameter.<br>Illegal characters found in parameter `'%s'`; legal range is `'%s'`. |
| `-1101` | `TOO_MANY_PARAMETERS` | Too many parameters sent for this endpoint.<br>Too many parameters; expected `'%s'` and received `'%s'`.<br>Duplicate values for a parameter detected. |
| `-1102` | `MANDATORY_PARAM_EMPTY_OR_MALFORMED` | A mandatory parameter was not sent, was empty/null, or malformed.<br>Mandatory parameter `'%s'` was not sent, was empty/null, or malformed.<br>Param `'%s'` or `'%s'` must be sent, but both were empty/null! |
| `-1103` | `UNKNOWN_PARAM` | An unknown parameter was sent. |
| `-1104` | `UNREAD_PARAMETERS` | Not all sent parameters were read.<br>Not all sent parameters were read; read `'%s'` parameter(s) but was sent `'%s'`. |
| `-1105` | `PARAM_EMPTY` | A parameter was empty.<br>Parameter `'%s'` was empty. |
| `-1106` | `PARAM_NOT_REQUIRED` | A parameter was sent when not required.<br>Parameter `'%s'` sent when not required. |
| `-1108` | `BAD_ASSET` | Invalid asset. |
| `-1109` | `BAD_ACCOUNT` | Invalid account. |
| `-1110` | `BAD_INSTRUMENT_TYPE` | Invalid symbolType. |
| `-1111` | `BAD_PRECISION` | Precision is over the maximum defined for this asset. |
| `-1112` | `NO_DEPTH` | No orders on book for symbol. |
| `-1113` | `WITHDRAW_NOT_NEGATIVE` | Withdrawal amount must be negative. |
| `-1114` | `TIF_NOT_REQUIRED` | TimeInForce parameter sent when not required. |
| `-1115` | `INVALID_TIF` | Invalid timeInForce. |
| `-1116` | `INVALID_ORDER_TYPE` | Invalid orderType. |
| `-1117` | `INVALID_SIDE` | Invalid side. |
| `-1118` | `EMPTY_NEW_CL_ORD_ID` | New client order ID was empty. |
| `-1119` | `EMPTY_ORG_CL_ORD_ID` | Original client order ID was empty. |
| `-1120` | `BAD_INTERVAL` | Invalid interval. |
| `-1121` | `BAD_SYMBOL` | Invalid symbol. |
| `-1122` | `INVALID_SYMBOL_STATUS` | Invalid symbol status. |
| `-1125` | `INVALID_LISTEN_KEY` | This listenKey does not exist. Please use POST /fapi/v1/listenKey to recreate listenKey |
| `-1126` | `ASSET_NOT_SUPPORTED` | This asset is not supported. |
| `-1127` | `MORE_THAN_XX_HOURS` | Lookup interval is too big.<br>More than `%s` hours between startTime and endTime. |
| `-1128` | `OPTIONAL_PARAMS_BAD_COMBO` | Combination of optional parameters invalid. |
| `-1130` | `INVALID_PARAMETER` | Invalid data sent for a parameter.<br>Data sent for parameter `'%s'` is not valid. |
| `-1136` | `INVALID_NEW_ORDER_RESP_TYPE` | Invalid newOrderRespType. |

### 20xx - Processing Issues

| Code | Message | Description |
|---|---|---|
| `-2010` | `NEW_ORDER_REJECTED` | NEW_ORDER_REJECTED |
| `-2011` | `CANCEL_REJECTED` | CANCEL_REJECTED<br>Cancel request failure as open order not found in the orderbook: "Unknown order sent". |
| `-2012` | `CANCEL_ALL_FAIL` | Batch cancel failure. |
| `-2013` | `NO_SUCH_ORDER` | Order does not exist. |
| `-2014` | `BAD_API_KEY_FMT` | API-key format invalid. |
| `-2015` | `REJECTED_MBX_KEY` | Invalid API-key, IP, or permissions for action. |
| `-2016` | `NO_TRADING_WINDOW` | No trading window could be found for the symbol. Try ticker/24hrs instead. |
| `-2017` | `API_KEYS_LOCKED` | API Keys are locked on this account. |
| `-2018` | `BALANCE_NOT_SUFFICIENT` | Balance is insufficient. |
| `-2019` | `MARGIN_NOT_SUFFICIEN` | Margin is insufficient. |
| `-2020` | `UNABLE_TO_FILL` | Unable to fill. |
| `-2021` | `ORDER_WOULD_IMMEDIATELY_TRIGGER` | Order would immediately trigger. |
| `-2022` | `REDUCE_ONLY_REJECT` | ReduceOnly Order is rejected.<br>This indicates the new reduce-only order conflicts with existing open orders; cancel the existing order and resubmit the reduce-only order. |
| `-2023` | `USER_IN_LIQUIDATION` | User in liquidation mode now. |
| `-2024` | `POSITION_NOT_SUFFICIENT` | Position is not sufficient. |
| `-2025` | `MAX_OPEN_ORDER_EXCEEDED` | Reach max open order limit. |
| `-2026` | `REDUCE_ONLY_ORDER_TYPE_NOT_SUPPORTED` | This OrderType is not supported when reduceOnly. |
| `-2027` | `MAX_LEVERAGE_RATIO` | Exceeded the maximum allowable position at current leverage. |
| `-2028` | `MIN_LEVERAGE_RATIO` | Leverage is smaller than permitted: insufficient margin balance. |

### 40xx - Filters and other Issues

| Code | Message | Description |
|---|---|---|
| `-4000` | `INVALID_ORDER_STATUS` | Invalid order status. |
| `-4001` | `PRICE_LESS_THAN_ZERO` | Price less than 0. |
| `-4002` | `PRICE_GREATER_THAN_MAX_PRICE` | Price greater than max price. |
| `-4003` | `QTY_LESS_THAN_ZERO` | Quantity less than zero. |
| `-4004` | `QTY_LESS_THAN_MIN_QTY` | Quantity less than min quantity. |
| `-4005` | `QTY_GREATER_THAN_MAX_QTY` | Quantity greater than max quantity. |
| `-4006` | `STOP_PRICE_LESS_THAN_ZERO` | Stop price less than zero. |
| `-4007` | `STOP_PRICE_GREATER_THAN_MAX_PRICE` | Stop price greater than max price. |
| `-4008` | `TICK_SIZE_LESS_THAN_ZERO` | Tick size less than zero. |
| `-4009` | `MAX_PRICE_LESS_THAN_MIN_PRICE` | Max price less than min price. |
| `-4010` | `MAX_QTY_LESS_THAN_MIN_QTY` | Max qty less than min qty. |
| `-4011` | `STEP_SIZE_LESS_THAN_ZERO` | Step size less than zero. |
| `-4012` | `MAX_NUM_ORDERS_LESS_THAN_ZERO` | Max mum orders less than zero. |
| `-4013` | `PRICE_LESS_THAN_MIN_PRICE` | Price less than min price. |
| `-4014` | `PRICE_NOT_INCREASED_BY_TICK_SIZE` | Price not increased by tick size. |
| `-4015` | `INVALID_CL_ORD_ID_LEN` | Client order id is not valid.<br>Client order id length should not be more than 36 chars |
| `-4016` | `PRICE_HIGHTER_THAN_MULTIPLIER_UP` | Price is higher than mark price multiplier cap. |
| `-4017` | `MULTIPLIER_UP_LESS_THAN_ZERO` | Multiplier up less than zero. |
| `-4018` | `MULTIPLIER_DOWN_LESS_THAN_ZERO` | Multiplier down less than zero. |
| `-4019` | `COMPOSITE_SCALE_OVERFLOW` | Composite scale too large. |
| `-4020` | `TARGET_STRATEGY_INVALID` | Target strategy invalid for orderType `'%s'`,reduceOnly `'%b'`. |
| `-4021` | `INVALID_DEPTH_LIMIT` | Invalid depth limit.<br>`'%s'` is not valid depth limit. |
| `-4022` | `WRONG_MARKET_STATUS` | market status sent is not valid. |
| `-4023` | `QTY_NOT_INCREASED_BY_STEP_SIZE` | Qty not increased by step size. |
| `-4024` | `PRICE_LOWER_THAN_MULTIPLIER_DOWN` | Price is lower than mark price multiplier floor. |
| `-4025` | `MULTIPLIER_DECIMAL_LESS_THAN_ZERO` | Multiplier decimal less than zero. |
| `-4026` | `COMMISSION_INVALID` | Commission invalid.<br>`%s` less than zero.<br>`%s` absolute value greater than `%s` |
| `-4027` | `INVALID_ACCOUNT_TYPE` | Invalid account type. |
| `-4028` | `INVALID_LEVERAGE` | Invalid leverage<br>Leverage `%s` is not valid<br>Leverage `%s` already exist with `%s` |
| `-4029` | `INVALID_TICK_SIZE_PRECISION` | Tick size precision is invalid. |
| `-4030` | `INVALID_STEP_SIZE_PRECISION` | Step size precision is invalid. |
| `-4031` | `INVALID_WORKING_TYPE` | Invalid parameter working type<br>Invalid parameter working type: `%s` |
| `-4032` | `EXCEED_MAX_CANCEL_ORDER_SIZE` | Exceed maximum cancel order size.<br>Invalid parameter working type: `%s` |
| `-4033` | `INSURANCE_ACCOUNT_NOT_FOUND` | Insurance account not found. |
| `-4044` | `INVALID_BALANCE_TYPE` | Balance Type is invalid. |
| `-4045` | `MAX_STOP_ORDER_EXCEEDED` | Reach max stop order limit. |
| `-4046` | `NO_NEED_TO_CHANGE_MARGIN_TYPE` | No need to change margin type. |
| `-4047` | `THERE_EXISTS_OPEN_ORDERS` | Margin type cannot be changed if there exists open orders. |
| `-4048` | `THERE_EXISTS_QUANTITY` | Margin type cannot be changed if there exists position. |
| `-4049` | `ADD_ISOLATED_MARGIN_REJECT` | Add margin only support for isolated position. |
| `-4050` | `CROSS_BALANCE_INSUFFICIENT` | Cross balance insufficient. |
| `-4051` | `ISOLATED_BALANCE_INSUFFICIENT` | Isolated balance insufficient. |
| `-4052` | `NO_NEED_TO_CHANGE_AUTO_ADD_MARGIN` | No need to change auto add margin. |
| `-4053` | `AUTO_ADD_CROSSED_MARGIN_REJECT` | Auto add margin only support for isolated position. |
| `-4054` | `ADD_ISOLATED_MARGIN_NO_POSITION_REJECT` | Cannot add position margin: position is 0. |
| `-4055` | `AMOUNT_MUST_BE_POSITIVE` | Amount must be positive. |
| `-4056` | `INVALID_API_KEY_TYPE` | Invalid api key type. |
| `-4057` | `INVALID_RSA_PUBLIC_KEY` | Invalid api public key |
| `-4058` | `MAX_PRICE_TOO_LARGE` | maxPrice and priceDecimal too large,please check. |
| `-4059` | `NO_NEED_TO_CHANGE_POSITION_SIDE` | No need to change position side. |
| `-4060` | `INVALID_POSITION_SIDE` | Invalid position side. |
| `-4061` | `POSITION_SIDE_NOT_MATCH` | Order's position side does not match user's setting. |
| `-4062` | `REDUCE_ONLY_CONFLICT` | Invalid or improper reduceOnly value. |
| `-4063` | `INVALID_OPTIONS_REQUEST_TYPE` | Invalid options request type |
| `-4064` | `INVALID_OPTIONS_TIME_FRAME` | Invalid options time frame |
| `-4065` | `INVALID_OPTIONS_AMOUNT` | Invalid options amount |
| `-4066` | `INVALID_OPTIONS_EVENT_TYPE` | Invalid options event type |
| `-4067` | `POSITION_SIDE_CHANGE_EXISTS_OPEN_ORDERS` | Position side cannot be changed if there exists open orders. |
| `-4068` | `POSITION_SIDE_CHANGE_EXISTS_QUANTITY` | Position side cannot be changed if there exists position. |
| `-4069` | `INVALID_OPTIONS_PREMIUM_FEE` | Invalid options premium fee |
| `-4070` | `INVALID_CL_OPTIONS_ID_LEN` | Client options id is not valid.<br>Client options id length should be less than 32 chars |
| `-4071` | `INVALID_OPTIONS_DIRECTION` | Invalid options direction |
| `-4072` | `OPTIONS_PREMIUM_NOT_UPDATE` | premium fee is not updated, reject order |
| `-4073` | `OPTIONS_PREMIUM_INPUT_LESS_THAN_ZERO` | input premium fee is less than 0, reject order |
| `-4074` | `OPTIONS_AMOUNT_BIGGER_THAN_UPPER` | Order amount is bigger than upper boundary or less than 0, reject order |
| `-4075` | `OPTIONS_PREMIUM_OUTPUT_ZERO` | output premium fee is less than 0, reject order |
| `-4076` | `OPTIONS_PREMIUM_TOO_DIFF` | original fee is too much higher than last fee |
| `-4077` | `OPTIONS_PREMIUM_REACH_LIMIT` | place order amount has reached to limit, reject order |
| `-4078` | `OPTIONS_COMMON_ERROR` | options internal error |
| `-4079` | `INVALID_OPTIONS_ID` | invalid options id<br>invalid options id: `%s`<br>duplicate options id `%d` for user `%d` |
| `-4080` | `OPTIONS_USER_NOT_FOUND` | user not found<br>user not found with id: `%s` |
| `-4081` | `OPTIONS_NOT_FOUND` | options not found<br>options not found with id: `%s` |
| `-4082` | `INVALID_BATCH_PLACE_ORDER_SIZE` | Invalid number of batch place orders.<br>Invalid number of batch place orders: `%s` |
| `-4083` | `PLACE_BATCH_ORDERS_FAIL` | Fail to place batch orders. |
| `-4084` | `UPCOMING_METHOD` | Method is not allowed currently. Upcoming soon. |
| `-4085` | `INVALID_NOTIONAL_LIMIT_COEF` | Invalid notional limit coefficient |
| `-4086` | `INVALID_PRICE_SPREAD_THRESHOLD` | Invalid price spread threshold |
| `-4087` | `REDUCE_ONLY_ORDER_PERMISSION` | User can only place reduce only order |
| `-4088` | `NO_PLACE_ORDER_PERMISSION` | User can not place order currently |
| `-4104` | `INVALID_CONTRACT_TYPE` | Invalid contract type |
| `-4105` | `SYMBOL_REDUCE_ONLY` | Symbol is under position risk control, only reduce-only order is allowed. |
| `-4106` | `SYMBOL_REDUCE_ONLY_BUY` | Symbol is under position risk control, buy order can only works with reduce-only. |
| `-4107` | `SYMBOL_REDUCE_ONLY_SELL` | Symbol is under position risk control, sell order can only works with reduce-only. |
| `-4109` | `INACTIVE_ACCOUNT` | Inactive account<br>Transfer any amount of asset to future wallet to reactive |
| `-4114` | `INVALID_CLIENT_TRAN_ID_LEN` | clientTranId is not valid<br>Client tran id length should be less than 64 chars |
| `-4115` | `DUPLICATED_CLIENT_TRAN_ID` | clientTranId is duplicated<br>Client tran id should be unique within 7 days |
| `-4116` | `DUPLICATED_CLIENT_ORDER_ID` | clientOrderId is duplicated |
| `-4117` | `STOP_ORDER_TRIGGERING` | stop order is triggering |
| `-4118` | `REDUCE_ONLY_MARGIN_CHECK_FAILED` | ReduceOnly Order Failed. Please check your existing position and open orders<br>This indicates that the new reduce-only order, combined with an existing same-side open order, would create an opposite-side position and lead to insufficient margin; please cancel the open order and try again. |
| `-4120` | `STOP_ORDER_SWITCH_ALGO` | Order type not supported for this endpoint. Please use the Algo Order API endpoints instead. |
| `-4131` | `MARKET_ORDER_REJECT` | The counterparty's best price does not meet the PERCENT_PRICE filter limit |
| `-4135` | `INVALID_ACTIVATION_PRICE` | Invalid activation price |
| `-4137` | `QUANTITY_EXISTS_WITH_CLOSE_POSITION` | Quantity must be zero with closePosition equals true |
| `-4138` | `REDUCE_ONLY_MUST_BE_TRUE` | Reduce only must be true with closePosition equals true |
| `-4139` | `ORDER_TYPE_CANNOT_BE_MKT` | Order type can not be market if it's unable to cancel |
| `-4140` | `INVALID_OPENING_POSITION_STATUS` | Invalid symbol status for opening position |
| `-4141` | `SYMBOL_ALREADY_CLOSED` | Symbol is closed |
| `-4142` | `STRATEGY_INVALID_TRIGGER_PRICE` | REJECT: take profit or stop order will be triggered immediately |
| `-4144` | `INVALID_PAIR` | Invalid pair |
| `-4161` | `ISOLATED_LEVERAGE_REJECT_WITH_POSITION` | Leverage reduction is not supported in Isolated Margin Mode with open positions |
| `-4164` | `MIN_NOTIONAL` | Order's notional must be no smaller than 5.0 (unless you choose reduce only)<br>Order's notional must be no smaller than `%s` (unless you choose reduce only) |
| `-4165` | `INVALID_TIME_INTERVAL` | Invalid time interval<br>Maximum time interval is `%s` days |
| `-4167` | `ISOLATED_REJECT_WITH_JOINT_MARGIN` | Unable to adjust to Multi-Assets mode with symbols of USDⓈ-M Futures under isolated-margin mode. |
| `-4168` | `JOINT_MARGIN_REJECT_WITH_ISOLATED` | Unable to adjust to isolated-margin mode under the Multi-Assets mode. |
| `-4169` | `JOINT_MARGIN_REJECT_WITH_MB` | Unable to adjust Multi-Assets Mode with insufficient margin balance in USDⓈ-M Futures. |
| `-4170` | `JOINT_MARGIN_REJECT_WITH_OPEN_ORDER` | Unable to adjust Multi-Assets Mode with open orders in USDⓈ-M Futures. |
| `-4171` | `NO_NEED_TO_CHANGE_JOINT_MARGIN` | Adjusted asset mode is currently set and does not need to be adjusted repeatedly. |
| `-4172` | `JOINT_MARGIN_REJECT_WITH_NEGATIVE_BALANCE` | Unable to adjust Multi-Assets Mode with a negative wallet balance of margin available asset in USDⓈ-M Futures account. |
| `-4183` | `ISOLATED_REJECT_WITH_JOINT_MARGIN` | Price is higher than stop price multiplier cap.<br>Limit price can't be higher than `%s`. |
| `-4184` | `PRICE_LOWER_THAN_STOP_MULTIPLIER_DOWN` | Price is lower than stop price multiplier floor.<br>Limit price can't be lower than `%s`. |
| `-4189` | `ACCOUNT_REDUCE_ONLY` | Restricted account permission: can only place reduceOnly order on the symbol. |
| `-4192` | `COOLING_OFF_PERIOD` | Trade forbidden due to Cooling-off Period. |
| `-4202` | `ADJUST_LEVERAGE_KYC_FAILED` | Intermediate Personal Verification is required for adjusting leverage over 20x |
| `-4203` | `ADJUST_LEVERAGE_ONE_MONTH_FAILED` | More than 20x leverage is available one month after account registration. |
| `-4205` | `ADJUST_LEVERAGE_X_DAYS_FAILED` | More than 20x leverage is available `%s` days after Futures account registration. |
| `-4206` | `ADJUST_LEVERAGE_KYC_LIMIT` | Users in this country has limited adjust leverage.<br>Users in your location/country can only access a maximum leverage of `%s` |
| `-4208` | `ADJUST_LEVERAGE_ACCOUNT_SYMBOL_FAILED` | Current symbol leverage cannot exceed 20 when using position limit adjustment service. |
| `-4209` | `ADJUST_LEVERAGE_SYMBOL_FAILED` | The max leverage of Symbol is 20x<br>Leverage adjustment failed. Current symbol max leverage limit is `%sx` |
| `-4210` | `STOP_PRICE_HIGHER_THAN_PRICE_MULTIPLIER_LIMIT` | Stop price is higher than price multiplier cap.<br>Stop price can't be higher than `%s` |
| `-4211` | `STOP_PRICE_LOWER_THAN_PRICE_MULTIPLIER_LIMIT` | Stop price is lower than price multiplier floor.<br>Stop price can't be lower than `%s` |
| `-4400` | `TRADING_QUANTITATIVE_RULE` | Futures Trading Quantitative Rules violated, only reduceOnly order is allowed, please try again later. |
| `-4401` | `LARGE_POSITION_SYM_RULE` | Futures Trading Risk Control Rules of large position holding violated, only reduceOnly order is allowed, please reduce the position. . |
| `-4402` | `COMPLIANCE_BLACK_SYMBOL_RESTRICTION` | Dear user, as per our Terms of Use and compliance with local regulations, this feature is currently not available in your region. |
| `-4403` | `ADJUST_LEVERAGE_COMPLIANCE_FAILED` | Dear user, as per our Terms of Use and compliance with local regulations, the leverage can only up to 10x in your region<br>Dear user, as per our Terms of Use and compliance with local regulations, the leverage can only up to `%sx` in your region |

### 50xx - Order Execution Issues

| Code | Message | Description |
|---|---|---|
| `-5021` | `FOK_ORDER_REJECT` | Due to the order could not be filled immediately, the FOK order has been rejected. |
| `-5022` | `GTX_ORDER_REJECT` | Due to the order could not be executed as maker, the Post Only order will be rejected. |
| `-5024` | `MOVE_ORDER_NOT_ALLOWED_SYMBOL_REASON` | Symbol is not in trading status. Order amendment is not permitted. |
| `-5025` | `LIMIT_ORDER_ONLY` | Only limit order is supported. |
| `-5026` | `Exceed_Maximum_Modify_Order_Limit` | Exceed maximum modify order limit. |
| `-5027` | `SAME_ORDER` | No need to modify the order. |
| `-5028` | `ME_RECVWINDOW_REJECT` | Timestamp for this request is outside of the ME recvWindow. |
| `-5029` | `MODIFICATION_MIN_NOTIONAL` | Order's notional must be no smaller than `%s` |
| `-5037` | `INVALID_PRICE_MATCH` | Invalid price match |
| `-5038` | `UNSUPPORTED_ORDER_TYPE_PRICE_MATCH` | Price match only supports order type: LIMIT, STOP AND TAKE_PROFIT |
| `-5039` | `INVALID_SELF_TRADE_PREVENTION_MODE` | Invalid self trade prevention mode |
| `-5040` | `FUTURE_GOOD_TILL_DATE` | The goodTillDate timestamp must be greater than the current time plus 600 seconds and smaller than 253402300799000 (UTC 9999-12-31 23:59:59) |
| `-5041` | `BBO_ORDER_REJECT` | No depth matches this BBO order |
| `-5043` | `Existing_Pending_Modification` | A pending modification already exists for this order. |


