# 🧠 Investment AI — Agent Memory File
# Baca file ini sebelum buat sebarang perubahan pada projek.
# Versi semasa: **v5.5.9** | Dikemas kini: 2026-07-02

## Lokasi Projek
`e:\PROJECTS\SEMUA PROJECT\INVESTMENT AI`
GitHub: https://github.com/hdanial211/investment-ai

## Exchange
**Hata.io (MY)** — `https://my-api.hata.io`
- Maker fee: **0.00%** (limit order masuk order book dulu)
- Taker fee: **0.25%** (order fill terus / market order)
- Coins: BTC, ETH, SOL, XRP, LTC (semua pair dengan MYR)
- API wrapper: `backend/hata_api.py`

## Architecture Ringkas
```
Binance WS (candle data) → process_kline() → ML XGBoost signal
                                                ↓
                                    Hata API → place_limit_order()
                                                ↓
                                    check_orders() loop (60s)
                                                ↓
                                    Grid Paired Orders logic
```

## Cara Start Bot
Double-click `Start_Bot.bat` atau:
- Backend: `uvicorn api:app --reload --port 8000` (dalam folder `backend/`)
- Frontend: `npm run dev` (dalam folder `frontend/`)
- Dashboard: http://localhost:5173

## ★ SISTEM SEMASA: Grid Paired Orders (v5.5.x)

### Konsep Utama
Setiap layer ada **sell sendiri** (bukan consolidated). Semua orders pre-placed = MAKER = 0% fee.

### Flow Penuh
```
ML signal fires → First entry BUY (mungkin taker kalau cepat)
Entry fills → TERUS place:
   ├── SELL @ (entry × (1 + grid_gap_pct))   → MAKER 0%
   └── BUY standby @ (entry × (1 - grid_gap_pct))  → MAKER 0%

Kalau standby BUY fills (Layer 2):
   ├── Keep Layer 1 SELL (biar dia)
   ├── ADD Layer 2 SELL @ (layer2_entry × (1 + gap))
   └── UPDATE standby BUY 1 step below Layer 2

Kalau SELL fills (Layer N done):
   ├── Remove that layer
   ├── Cancel old standby BUY
   └── Place NEW standby BUY below LOWEST remaining layer
       (re-anchor standby mengikut posisi semasa)

Kalau SEMUA layers sold:
   └── Cancel standby BUY, reset, cari ML signal baharu
```

### Fee Handling
Sama seperti sistem lama — guna `_extract_hata_exec_data()`:
- Baca fee sebenar dari Hata API `trades[]`
- `net_qty = exec_qty - fee_qty`
- `sell_price = (actual_cost / net_qty) × (1 + gap_pct)`
- Ini **automatically** recover buy fees dalam sell price
- Semua subsequent sells = MAKER 0%

### Key Functions (live_engine.py)
| Function | Tujuan |
|---|---|
| `_grid_place_layer_sell()` | Place SELL untuk satu layer dengan fee recovery |
| `_grid_update_standby_buy()` | Cancel old standby, place new standby BUY below lowest layer |
| `_check_grid_orders()` | Check semua individual sells + standby buy (dipanggil tiap 60s) |
| `_extract_hata_exec_data()` | Baca actual exec qty, fee dari Hata API trades[] |
| `_smart_pending_buy_check()` | Cancel+replace PENDING_BUY jika harga naik >5min; hold jika turun |
| `_sync_trade_history()` | Sync PnL dari Hata API `/orderbook/sapi/trades/history` per coin |

### State Per Coin (shared.py)
```json
{
  "layers": [...],           // Array layers, setiap layer ada sell_order_id sendiri
  "standby_buy_order_id": "xxx",   // Single cascade standby BUY
  "standby_buy_price": 980.0,
  "grid_gap_pct": 0.01,      // Configurable per coin (default 1%)
  "system_mode": "grid",     // "grid" = new, "dca" = old system
  "trade_amount_myr": 50.0,  // Per coin, set dari frontend
  "is_auto": true,
  "tp_pct": 0.005            // Legacy, grid guna grid_gap_pct
}
```

### Global State (shared.py)
```json
{
  "frozen_myr": 45.0         // RM yang sedang 'dipesan' untuk order pending
                             // Lifecycle: +amount bila order placed, -amount bila fills/cancel
}
```

### Layer Structure
```json
{
  "id": 1,
  "entry_price": 990.0,
  "amount_myr": 30.0,        // Ikut setting individu per coin
  "quantity": 6.27,
  "exec_qty": 6.27,
  "fee_qty": 0.01,
  "net_qty": 6.26,           // Selepas fee
  "actual_cost_myr": 30.23,
  "fee_myr": 0.12,
  "fee_role": "taker",       // "maker" atau "taker" dari Hata API
  "status": "HOLDING",
  "buy_order_id": "abc123",
  "sell_order_id": "def456",   // Individual sell untuk layer ni
  "sell_target_price": 1000.0,
  "created_at": 1234567890
}
```

## ★ SISTEM LAMA (BACKUP): DCA Consolidated Sell
File: `backend/live_engine_old_system.py`

### Perbezaan Utama
| | Old DCA System | New Grid System |
|---|---|---|
| Sell | 1 consolidated untuk SEMUA layers | **1 sell per layer** |
| TP target | avg_entry + tp_pct | **entry + grid_gap_pct per layer** |
| Cascade | Place PENDING_BUY selepas sell fill | **Standby BUY active sepanjang masa** |
| Fee | Kadang taker | **Semua MAKER 0%** |
| Recovery | Partial recover sukar | **Setiap layer recover sendiri** |

## API Endpoints Penting
| Method | Endpoint | Tujuan |
|---|---|---|
| GET | `/api/state` | Semua coin state |
| POST | `/api/toggle-auto` | On/off auto trading per coin |
| POST | `/api/set-amount` | Set trade amount per coin |
| POST | `/api/set-risk-level` | Set risk level (1-3) |
| POST | `/api/set-tp` | Set TP% per coin |
| POST | `/api/set-grid-gap` | Set grid gap% per coin |
| POST | `/api/sync-history` | Sync trade history dari Hata API |
| POST | `/api/ml-retrain` | Manual retrain ML model |

## Perkara JANGAN Buat
1. Jangan pakai market orders — selalu limit orders (MAKER = 0%)
2. Jangan hardcode fee — baca dari Hata API trades[]
3. Jangan beli baharu kalau ada PENDING_BUY aktif untuk coin yang sama
4. Jangan commit .env file
5. Versi commit: tulis `v_._._ ` depan message
6. Jangan guna endpoint `/orderbook/sapi/trades` (lama/404) — guna `/orderbook/sapi/trades/history`
7. Jangan simpan fee_role sebagai 'unknown' — infer dari fee_qty kalau API tak return is_maker

## Files Kritikal
| File | Tujuan |
|---|---|
| `backend/live_engine.py` | ★ Enjin utama bot |
| `backend/shared.py` | State global + load/save |
| `backend/api.py` | FastAPI endpoints |
| `backend/hata_api.py` | Hata exchange wrapper (endpoint betul: `/orderbook/sapi/trades/history`) |
| `backend/bot_state.json` | Memori bot (layers, PnL) |
| `frontend/src/App.jsx` | Dashboard React |
| `backend/live_engine_old_system.py` | Backup sistem lama |
| `scratch/test_daily_report_direct.py` | ★ Daily PnL report → Telegram |

## Daily Telegram Report
- **Script**: `scratch/test_daily_report_direct.py`
- **Jadual**: 11:00 PM setiap hari (Antigravity scheduled task)
- **Endpoint Hata**: `GET /orderbook/sapi/trades/history`
  - Params wajib: `pair_name` (e.g. `ETHMYR`), `page`, `rows` (max 100)
  - Params opsional: `start_time`, `end_time` (Unix timestamp dalam saat)
- **Telegram**:
  - Bot: `Crypto_Hakim_Bot`
  - Token: `8880063318:AAHeAoJ1E4m1BTJVmTJEKVz5TbNTwW9K98k`
  - Chat ID: `-1003819849481` (Group: SAHAM SIGNAL)

## Cara Guna File Ini Dalam Chat Baru
```
Saya ada projek Investment AI crypto trading bot.
Sila baca file memori projek ini dahulu sebelum buat apa-apa:
e:\PROJECTS\SEMUA PROJECT\INVESTMENT AI\PROJECT_MEMORY.md

Dan juga:
e:\PROJECTS\SEMUA PROJECT\INVESTMENT AI\.agents\AGENTS.md

Kemudian [nyatakan permintaan anda di sini]
```
