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
