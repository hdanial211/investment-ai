# 🧠 INVESTMENT AI — PROJECT MEMORY FILE
> Dikemas kini: 2026-06-22 | Versi Semasa: **v5.3.57**
> GitHub: https://github.com/hdanial211/investment-ai
> Lokasi Projek: `e:\PROJECTS\SEMUA PROJECT\INVESTMENT AI`

---

## 📁 STRUKTUR PROJEK

```
INVESTMENT AI/
├── backend/                    ← Python FastAPI + Bot Engine
│   ├── live_engine.py          ★ ENJIN UTAMA BOT (WebSocket + Order Logic)
│   ├── shared.py               ★ State global bot (bot_state.json loader)
│   ├── api.py                  ★ FastAPI server (port 8000)
│   ├── hata_api.py             ★ Wrapper Hata Exchange API
│   ├── bot_state.json          ★ Memori bot (layers, PnL, settings per coin)
│   ├── config.py               Settings umum
│   ├── features/
│   │   └── indicators.py       Kiraan EMA, RSI, MACD, BB, VWAP, dll.
│   ├── backtest/
│   │   └── dca_engine.py       Enjin backtesting DCA
│   ├── models/                 XGBoost .pkl models (per coin)
│   └── .env                    API keys (JANGAN share/commit)
├── frontend/
│   └── src/
│       ├── App.jsx             ★ Dashboard React utama
│       ├── App.css             Styling dashboard
│       └── BacktestSimulator.jsx  Tab simulator backtest
├── Start_Bot.bat               ★ Cara start bot (double-click ini)
├── models/                     XGBoost + PPO LSTM models
└── data/                       CSV historical data (COIN_USDT_1m.csv)
```

---

## 🚀 CARA START BOT

**Double-click `Start_Bot.bat`** — ini akan buka 2 terminal:
1. **Terminal 1**: Backend Python (`uvicorn api:app --reload --port 8000`)
2. **Terminal 2**: Frontend Vite (`npm run dev` → http://localhost:5173)

> ⚠️ JANGAN tutup terminal. Minimize sahaja.
> Live engine berjalan **di dalam** backend (bukan proses berasingan).

---

## ⚙️ SENI BINA SISTEM (v5.3.0)

### Aliran Bot Penuh

```
Start_Bot.bat
    → uvicorn api:app (port 8000)
        → api.py @startup → start live_engine.run() dalam thread

live_engine.py:
    1. startup_recovery()     ← Sync semua layers dengan Hata API (bila restart)
    2. update_hata_prices_loop() ← Background task (setiap 60 saat)
    3. Binance WebSocket       ← Candle 1 minit untuk semua 5 coins
```

### Loop 60 Saat (`update_hata_prices_loop`)
1. Fetch harga Hata MYR untuk 5 coins
2. Fetch baki wallet Hata (available + frozen MYR)
3. Kira kadar pertukaran USDT/MYR (dari Hata ETH vs Binance ETH)
4. **Semak semua PENDING orders** (BUY + SELL) untuk semua 5 coins:
   - PENDING_BUY filled → place LIMIT SELL
   - PENDING_BUY > 5 min → auto-cancel (guna `time.time()`)
   - PENDING_SELL filled → catat PnL + **auto-layer baru di entry×0.99**
5. Compute system status (lokal, tanpa API luar)

### Signal XGBoost (setiap candle 1 min)
- Confidence > 60% → cuba place Limit BUY
- **Syarat cegah double-buy**: jangan beli jika ada PENDING_BUY aktif
- **Syarat layering**: harga semasa mesti ≤ last_entry × 0.99 (1% bawah)
- Semak max_layers (ikut risk level)

### Auto-DCA Layer (`_place_next_layer`)
- Dicetuskan bila PENDING_SELL fill
- Letak terus Limit BUY di `last_entry × 0.99`
- Berlaku untuk **semua 5 coins** (ETH, BTC, SOL, XRP, LTC)
- TP% ikut risk level coin berkenaan

### Startup Recovery (`startup_recovery`)
- Jalan **sekali sahaja** masa bot start
- Check semua layers dalam `bot_state.json` vs Hata API
- Fill yang terlepas → place SELL
- Cancelled → buang layer
- Stuck > 5 min → auto-cancel
- Missing `created_at` → patch dengan masa sekarang

---

## 💰 COINS & STRATEGI

| Coin | Max Layers | Risk Level | TP% | Gap Entry |
|------|-----------|------------|-----|-----------|
| ETH  | 3 | 3 (Agresif) | 0.5% | 1% |
| BTC  | 3 | 3 (Agresif) | 0.5% | 1% |
| SOL  | 3 | 3 (Agresif) | 0.5% | 1% |
| XRP  | 3 | 3 (Agresif) | 0.5% | 1% |
| LTC  | 3 | 3 (Agresif) | 0.5% | 1% |

**Risk Level:**
- Level 1: DCA Asas, max 6 layers, TP 1.5%, gap 2%
- Level 2: Scalp & Run, max 5 layers, TP 0.4%, gap 0.5%
- Level 3: Heavy Scalping, max 3 layers, TP 0.5%, gap 1%

---

## 🔌 API KEYS & CONFIG

**File**: `backend/.env`
```
HATA_API_KEY=<semak dalam backend/.env>
HATA_API_SECRET=<semak dalam backend/.env>
GROQ_API_KEY=<tidak dipakai lagi sejak v5.3.0>
```

**Hata Exchange API:**
- Base URL: `https://my-api.hata.io`
- Auth: `X-API-KEY` + `Signature` (HMAC-SHA256)
- POST requests: signature guna raw JSON (sorted keys, no spaces)
- GET requests: signature guna URL-encoded query string

**Endpoints Hata yang dipakai:**
```
GET  /orderbook/sapi/balance          → Baki wallet
GET  /orderbook/sapi/order            → Status order
GET  /orderbook/api/v2/exchange-info  → Harga semua pasangan MYR
POST /orderbook/sapi/orders/create    → Buat order baru
POST /orderbook/sapi/orders/cancel    → Cancel order
```

**Decimal scaling Hata (wajib ikut):**
```python
COIN_SCALES = {
    "BTC": {"qty": 5, "price": 0},
    "ETH": {"qty": 4, "price": 0},
    "SOL": {"qty": 3, "price": 1},
    "LTC": {"qty": 3, "price": 1},
    "XRP": {"qty": 1, "price": 3}
}
```

---

## 📊 STRUKTUR `bot_state.json`

```json
{
  "ETH": {
    "current_price": 7050.0,
    "last_signal": 0,
    "confidence": 40.76,
    "layers": [
      {
        "id": 1,
        "entry_price": 7000.0,
        "amount_myr": 30.0,
        "quantity": 0.004285,
        "take_profit": 7035.0,
        "status": "PENDING_SELL",      ← PENDING_BUY / PENDING_SELL / OPEN
        "buy_order_id": "241439511",
        "sell_order_id": "241473090",
        "hata_buy_res": {...},
        "hata_sell_res": {...},
        "created_at": 1750000000.0     ← Unix timestamp (time.time())
      }
    ],
    "total_pnl": 0.5,
    "trade_amount_myr": 30.0,
    "risk_level": 3,
    "is_auto": true
  }
}
```

---

## 🌐 FRONTEND DASHBOARD

**URL**: http://localhost:5173
**Framework**: React + Vite
**API polling**: setiap 1 saat ke `GET http://localhost:8000/api/state`

### API Endpoints Backend
```
GET  /api/state              → Semua state (global + coins)
POST /api/toggle-auto        → On/Off auto trading per coin
POST /api/set-risk-level     → Set risk level 1/2/3
POST /api/set-amount         → Set saiz trade per lapis (RM)
POST /api/manual-buy         → Manual buy sekarang
POST /api/panic-sell         → Sell semua posisi coin tertentu
WS   /api/backtest-stream    → Streaming hasil backtest
```

### Panel Dashboard
1. **Coin Selector Bar** — 5 coins dengan harga, confidence, bilangan layers
2. **Paparan Pasaran** — Harga Hata MYR + AI confidence meter
3. **Posisi Layering** — Jadual semua layers aktif
4. **Status Akaun & PnL** — Baki Hata, frozen, PnL semua coins
5. **⚙️ Status Sistem Bot (Autonomi)** — Status lokal (Safe/Warning/Action Required)
6. **Kawalan Eksekusi** — Toggle auto, set amount, risk level, manual buy, panic sell

---

## 🧬 AI MODEL

**Type**: XGBoost (scikit-learn API)
**File**: `models/xgboost_scalping_{COIN}_1y.pkl`
**Trigger**: Setiap candle 1 minit dari Binance WebSocket (bila candle tutup `kline['x'] == True`)
**Input features**: EMA_9, EMA_21, EMA_Trend, RSI_14, Volume_ROC, BB, MACD, STOCH, ATR, VWAP
**Output**: `predict_proba()` → probability class 1 (Golden Entry)
**Threshold**: > 0.60 (60%) = signal BUY

**Binance WebSocket URL:**
```
wss://stream.binance.com:9443/stream?streams=btcusdt@kline_1m/ethusdt@kline_1m/solusdt@kline_1m/xrpusdt@kline_1m/ltcusdt@kline_1m
```

---

## 🐛 BUG HISTORY & PENYELESAIAN

| Versi | Masalah | Penyelesaian |
|-------|---------|--------------|
| v5.2.3 | Double process conflict (engine jalan 2x) | Consolidate — engine jalan dalam 1 thread di api.py |
| v5.2.4 | XRP layer hilang dari memori | Reconstruct layer, terus place SELL |
| v5.2.5 | Tiada AI Guardian | Tambah Groq (kemudian dibuang semula) |
| v5.2.6 | Pesanan beli tersangkut | Auto-cancel selepas 5 minit |
| v5.2.7 | Layer lama tiada `created_at` | Patch dengan `time.time()` bila detected |
| v5.3.0 | Bot bergantung Groq AI | Buang Groq, guna logik sistem sendiri sepenuhnya |
| v5.3.2 | Sell retry stuck due to precision mismatch and Taker fee deduction | Rounded buy qty in state, dynamic fee extraction from trades, float truncation and balance capping |
| v5.3.3 | Logger output is not colored in terminal | Created custom formatter to color WARNING, ERROR, and CRITICAL messages in RED |
| v5.3.4 | Tiada sistem Auto-Healing & Pemantauan | Membina monitor_healing.py untuk memeriksa kesihatan backend/frontend secara automatik, membersihkan proses tergantung dan memulakan semula perkhidmatan |
| v5.3.5 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengemaskini fail status bot_state.json |
| v5.3.6 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengemaskini fail status bot_state.json |
| v5.3.7 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengemaskini fail status bot_state.json |
| v5.3.8 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengemaskini fail status bot_state.json |
| v5.3.9 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengemaskini fail status bot_state.json |
| v5.3.10 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengemaskini fail status bot_state.json |
| v5.3.11 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengemaskini fail status bot_state.json |
| v5.3.12 | Pemantau berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengemaskini fail status bot_state.json |
| v5.3.13 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 4 pasangan dagangan pada Hata Exchange |
| v5.3.14 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 4 pasangan dagangan pada Hata Exchange |
| v5.3.15 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 5 pasangan dagangan pada Hata Exchange |
| v5.3.16 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 5 pasangan dagangan pada Hata Exchange |
| v5.3.17 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 5 pasangan dagangan pada Hata Exchange |
| v5.3.18 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan penutupan posisi LTC yang mencapai sasaran take-profit |
| v5.3.19 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 3 pasangan dagangan terbuka (BTC, SOL, XRP) |
| v5.3.20 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 4 pasangan dagangan terbuka (BTC, SOL, XRP, LTC) |
| v5.3.21 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 3 pasangan dagangan terbuka (BTC, SOL, XRP) |
| v5.3.22 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan pembatalan pesanan LTC yang tergantung |
| v5.3.23 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 4 pasangan dagangan terbuka (BTC, SOL, XRP, LTC) |
| v5.3.24 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 4 pasangan dagangan terbuka (BTC, SOL, XRP, LTC) |
| v5.3.25 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 4 pasangan dagangan terbuka (BTC, SOL, XRP, LTC) |
| v5.3.26 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan penutupan posisi SOL yang mencapai sasaran take-profit |
| v5.3.27 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 3 pasangan dagangan terbuka (BTC, XRP, LTC) |
| v5.3.28 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 3 pasangan dagangan terbuka (BTC, XRP, LTC) |
| v5.3.29 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 3 pasangan dagangan terbuka (BTC, XRP, LTC) dengan LTC separa terisi |
| v5.3.30 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan penutupan posisi LTC yang mencapai sasaran take-profit |
| v5.3.31 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 2 pasangan dagangan terbuka (BTC, XRP) |
| v5.3.32 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan pembatalan pesanan LTC yang tersangkut serta status aktif bagi 2 pasangan dagangan terbuka (BTC, XRP) |
| v5.3.33 | Pemantauan berkala (Hourly monitor) & Optimasi Healing | Menjalankan pemantauan status sistem, mengoptimumkan check_port & URL backend dalam monitor_healing.py dengan IP 127.0.0.1 untuk mengelakkan kelengahan DNS, menambah socket lock (single-instance) untuk mengelakkan proses bertindih, serta memantau status pesanan LTC, BTC, XRP. |
| v5.3.34 | Perlumbaan Auto-Healing (Race Condition Startup) | Menambah semakan is_backend_running dan is_frontend_running serta polling 10 saat sebelum proses dimatikan dalam monitor_healing.py bagi mengelakkan restart loop semasa startup. |
| v5.3.35 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi 4 pasangan dagangan terbuka (ETH, BTC, XRP, LTC) |
| v5.3.36 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.37 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) dengan kemasukan posisi SOL yang baharu |
| v5.3.38 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif yang stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.39 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik, mengesahkan pembatalan pesanan XRP yang tersangkut serta status aktif yang stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.40 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan kemasukan lapisan DCA kedua bagi LTC |
| v5.3.41 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik, mengesahkan penambahan lapisan DCA (PENDING_BUY) baharu untuk XRP serta status aktif bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.42 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan penutupan posisi untung (TP) bagi LTC (Lapisan 2) dan ETH (Lapisan 1), serta pengisian BTC (Lapisan 1) |
| v5.3.43 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik, mengesahkan pembatalan pesanan BTC yang tersangkut serta status aktif bagi 4 pasangan dagangan terbuka (ETH, SOL, XRP, LTC) |
| v5.3.44 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) dengan kemasukan posisi BTC yang baharu |
| v5.3.45 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif yang stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.46 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan kemasukan lapisan DCA kedua bagi XRP |
| v5.3.47 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.48 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.49 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.50 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.51 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.52 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif bagi kesemua 5 pasangan dagangan terbuka dengan status XRP (Lapisan 2) separa terisi (0.3/6.4 Qty) |
| v5.3.53 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.54 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.55 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.56 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik dan mengesahkan status aktif stabil bagi kesemua 5 pasangan dagangan terbuka (ETH, BTC, SOL, XRP, LTC) |
| v5.3.57 | Pemantauan berkala (Hourly monitor) | Menjalankan pemantauan status sistem dagangan kripto secara automatik, mengesahkan penutupan posisi untung (TP) XRP (Lapisan 2) dan pembukaan lapisan DCA (PENDING_BUY) baharu bagi XRP (Lapisan 3) serta LTC (Lapisan 2) |

---

## 📋 PERATURAN PENTING

1. **Auto-cancel**: PENDING_BUY > 5 minit → cancel automatik (check setiap 60 saat)
2. **Anti double-buy**: Jangan beli baru jika ada PENDING_BUY aktif untuk coin yang sama
3. **1% gap rule**: Untuk layer baru, harga mesti ≤ last_entry × 0.99
4. **Auto-DCA**: PENDING_SELL fill → terus letak BUY baru di entry × 0.99
5. **Startup recovery**: Bot check Hata API untuk semua layers bila restart
6. **Tidak pakai Groq**: Sistem sepenuhnya autonomi, tanpa API AI luar
7. **Confidence threshold**: > 60% untuk trigger entry baru
8. **Sell quantity**: Dihitung secara dinamik berdasarkan trade fill & fi Hata. Jika baki kurang, bot akan auto-cap (truncate) mengikut baki sedia ada.
9. **Auto-healing & Pemantauan**: Memantau backend (port 8000) dan frontend (port 5173) secara berkala dan memulakan semula perkhidmatan jika dikesan terhenti.

---

## 🔮 PERKARA YANG BOLEH DIPERTINGKATKAN (FUTURE IDEAS)

- [ ] Trailing stop loss untuk PENDING_SELL
- [ ] Dashboard stats: win rate, avg hold time
- [ ] Notifikasi Telegram bila order fill
- [ ] Backtest semula dengan logik 1% DCA baru
- [ ] Cancel PENDING_SELL jika harga jatuh jauh dari TP (stop loss layer)

---

## 📝 CARA GUNA FILE INI DALAM CHAT BARU

Paste arahan ini dalam chat baru:
```
Saya ada projek Investment AI crypto trading bot.
Sila baca file memori projek ini dahulu sebelum buat apa-apa:
e:\PROJECTS\SEMUA PROJECT\INVESTMENT AI\PROJECT_MEMORY.md

Kemudian [nyatakan permintaan anda di sini]
```
