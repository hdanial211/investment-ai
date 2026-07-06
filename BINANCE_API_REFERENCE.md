# Binance Spot API Reference — Investment AI Project
> **Sumber rasmi**: https://developers.binance.com/en
> 
> Dokumen ini hanya merangkumi endpoint yang digunakan oleh projek ini.
> Binance digunakan **HANYA sebagai sumber data candle** — semua trading dilakukan di Hata.io.
> Tiada API Key diperlukan (semua endpoint public).

---

## 1. REST API — Klines (Candlestick Data)

**Guna di**: `live_engine.py` → `prefetch_historical_data()`

```
GET https://api.binance.com/api/v3/klines
```

### Parameters

| Param | Type | Wajib | Keterangan |
|---|---|---|---|
| `symbol` | STRING | ✅ | Trading pair, e.g. `BTCUSDT`, `ETHUSDT` |
| `interval` | ENUM | ✅ | Timeframe: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, dll |
| `limit` | INT | ❌ | Default: 500, Max: **1000** |
| `startTime` | LONG | ❌ | Timestamp dalam milliseconds |
| `endTime` | LONG | ❌ | Timestamp dalam milliseconds |
| `timeZone` | STRING | ❌ | Default: `0` (UTC) |

### Response

Array of arrays (ascending order, oldest first):

```json
[
  [
    1499040000000,      // [0] Open time (ms)
    "0.01634790",       // [1] Open price
    "0.80000000",       // [2] High price
    "0.01575800",       // [3] Low price
    "0.01577100",       // [4] Close price
    "148976.11427815",  // [5] Volume (base asset)
    1499644799999,      // [6] Close time (ms)
    "2434.19055334",    // [7] Quote asset volume
    308,                // [8] Number of trades
    "1756.87402397",    // [9] Taker buy base volume
    "28.46694368",      // [10] Taker buy quote volume
    "0"                 // [11] Ignore
  ]
]
```

### Cara Guna Dalam Projek

```python
# live_engine.py — prefetch 150 candles sebelum WS connect
url = f"https://api.binance.com/api/v3/klines?symbol={sym.upper()}&interval=1m&limit=150"
res = requests.get(url, timeout=10)
data = res.json()

for k in data:
    klines_dict[coin_id].append({
        'timestamp': pd.to_datetime(k[0], unit='ms'),
        'open': float(k[1]),
        'high': float(k[2]),
        'low': float(k[3]),
        'close': float(k[4]),
        'volume': float(k[5])
    })
```

**Weight**: 2 per request

---

## 2. REST API — Ticker Price

**Guna di**: `live_engine.py` → fallback harga semasa (MYR conversion)

```
GET https://api.binance.com/api/v3/ticker/price
```

### Parameters

| Param | Type | Wajib | Keterangan |
|---|---|---|---|
| `symbol` | STRING | ❌ | Satu symbol, e.g. `ETHUSDT`. Tanpa param = semua symbols |

### Response

```json
{
  "symbol": "ETHUSDT",
  "price": "3500.50000000"
}
```

### Cara Guna Dalam Projek

```python
# Fallback price check (kalau Hata price tak available)
bin_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=5).json()
price_usd = float(bin_res["price"])
```

**Weight**: 1 (single symbol), 2 (all symbols)

---

## 3. WebSocket — Live Kline Stream

**Guna di**: `live_engine.py` → `start_live_engine()` — sumber utama live candle data

### Combined Stream URL

```
wss://stream.binance.com:9443/stream?streams=btcusdt@kline_1m/ethusdt@kline_1m/solusdt@kline_1m/xrpusdt@kline_1m/ltcusdt@kline_1m
```

### Format

- Stream name mesti **lowercase**: `btcusdt`, bukan `BTCUSDT`
- Combined stream wraps data dalam object:

```json
{
  "stream": "btcusdt@kline_1m",
  "data": {
    "e": "kline",
    "E": 1672515782136,
    "s": "BTCUSDT",
    "k": {
      "t": 1672515780000,    // Kline start time
      "T": 1672515839999,    // Kline close time
      "s": "BTCUSDT",        // Symbol
      "i": "1m",             // Interval
      "f": 100,              // First trade ID
      "L": 200,              // Last trade ID
      "o": "16700.00",       // Open price
      "c": "16705.50",       // Close price
      "h": "16710.00",       // High price
      "l": "16695.00",       // Low price
      "v": "1.234",          // Base asset volume
      "n": 100,              // Number of trades
      "x": true,             // ★ Is this kline CLOSED? (penting!)
      "q": "20598.25",       // Quote asset volume
      "V": "0.678",          // Taker buy base volume
      "Q": "11328.10",       // Taker buy quote volume
      "B": "0"               // Ignore
    }
  }
}
```

### Field Penting untuk AI

| Field | Guna |
|---|---|
| `k.x` | **Kline closed?** — hanya proses candle bila `x == true` |
| `k.o` | Open price → feature `open` |
| `k.h` | High price → feature `high` |
| `k.l` | Low price → feature `low` |
| `k.c` | Close price → feature `close` + current price |
| `k.v` | Volume → feature `volume` |
| `k.t` | Timestamp → feature `timestamp` |

### Cara Guna Dalam Projek

```python
WS_URL = "wss://stream.binance.com:9443/stream?streams=" + "/".join([f"{s}@kline_1m" for s in SYMBOLS])

# Dalam on_message():
msg = json.loads(raw)
kline = msg["data"]["k"]

if kline["x"]:  # ★ Hanya bila candle TUTUP
    process_kline(coin_id, {
        'timestamp': pd.to_datetime(kline['t'], unit='ms'),
        'open': float(kline['o']),
        'high': float(kline['h']),
        'low': float(kline['l']),
        'close': float(kline['c']),
        'volume': float(kline['v'])
    })
```

### WebSocket Rules

| Rule | Detail |
|---|---|
| Max connection | **24 jam** — lepas tu auto disconnect |
| Ping/Pong | Server hantar `ping` setiap **20 saat**, client mesti reply `pong` |
| Reconnect | Implement exponential backoff (5s, 10s, 20s...) |
| Symbols | Mesti **lowercase** dalam stream name |

---

## 4. CCXT — Historical Data Download

**Guna di**: `data/binance_proxy.py` → download data untuk AI training

### Setup

```python
import ccxt
exchange = ccxt.binance()  # No API key needed (public data)
```

### Fetch OHLCV

```python
ohlcv = exchange.fetch_ohlcv(
    symbol='BTC/USDT',    # Format: BASE/QUOTE
    timeframe='1m',        # Supported: 1m, 5m, 15m, 1h, 4h, 1d
    since=timestamp_ms,    # Start timestamp (milliseconds)
    limit=1000             # Max per request: 1000
)
```

### Response Format

```python
# Each element: [timestamp, open, high, low, close, volume]
[
    [1499040000000, 0.01634, 0.80000, 0.01575, 0.01577, 148976.11],
    [1499040060000, 0.01577, 0.01580, 0.01570, 0.01578, 52300.45],
    ...
]
```

### Pagination (untuk download banyak data)

```python
all_ohlcv = []
since = start_timestamp

while since < exchange.milliseconds():
    ohlcv = exchange.fetch_ohlcv(symbol, '1m', since, 1000)
    if not ohlcv:
        break
    since = ohlcv[-1][0] + 1  # Next batch starts after last candle
    all_ohlcv.extend(ohlcv)
    time.sleep(exchange.rateLimit / 1000)  # Respect rate limit
```

---

## 5. Rate Limits

| Jenis | Had | Keterangan |
|---|---|---|
| IP Weight | **6,000 / minit** | Semua REST request dikira weight |
| Klines | Weight **2** | Per request |
| Ticker Price | Weight **1** | Single symbol |
| WebSocket | **24 jam** max | Auto disconnect, perlu reconnect |
| CCXT rateLimit | `exchange.rateLimit` ms | Built-in, auto managed |

### Monitoring

```
Response Header: X-MBX-USED-WEIGHT-1M: <current_weight>
```

### Error Codes

| HTTP Code | Maksud | Tindakan |
|---|---|---|
| 429 | Rate limit exceeded | Stop, tunggu `Retry-After` header |
| 418 | IP auto-banned | Ban 2 min — 3 hari. JANGAN spam lagi |
| 5XX | Server error | Retry dengan exponential backoff |

---

## 6. Symbols Yang Digunakan

| Binance Symbol | Coin ID | Pair Hata |
|---|---|---|
| `BTCUSDT` | BTC | BTC_MYR |
| `ETHUSDT` | ETH | ETH_MYR |
| `SOLUSDT` | SOL | SOL_MYR |
| `XRPUSDT` | XRP | XRP_MYR |
| `LTCUSDT` | LTC | LTC_MYR |

**NOTA**: Binance = data USD, Hata = trading MYR. Harga Binance hanya untuk candle/AI features, BUKAN untuk order execution.

---

## 7. Files Yang Guna Binance API

| File | Endpoint | Tujuan |
|---|---|---|
| `backend/live_engine.py` | WebSocket Kline + REST Klines + Ticker Price | Live candle data + prefetch + fallback price |
| `backend/data/binance_proxy.py` | CCXT `fetch_ohlcv` | Download historical data untuk training |
| `backend/train_all.py` | (via binance_proxy) | Auto download + train semua coins |
| `backend/models/ai_model.py` | (guna CSV dari binance_proxy) | Initial model training |
