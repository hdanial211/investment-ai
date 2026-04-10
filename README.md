# Bitcoin Investment AI - README

## 🚀 Quick Start

### 1. Setup Backend
```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### 2. Setup Frontend
```powershell
cd frontend
npm run dev
```

### 3. Setup MCP Server
```powershell
cd mcp-server
pip install -r requirements.txt
python server.py
```

---

## 📁 Struktur Project

```
INVESTMENT AI/
├── .env                    ← API Keys (RAHSIA!)
├── .gitignore
├── backend/
│   ├── main.py             ← FastAPI server (port 8000)
│   ├── config.py           ← Settings dari .env
│   ├── requirements.txt
│   ├── exchange/
│   │   └── luno_client.py  ← Luno API wrapper
│   ├── strategy/
│   │   ├── signal_engine.py   ← RSI + MA signals
│   │   └── decision_maker.py  ← BUY/SELL/HOLD logic
│   ├── scheduler/
│   │   └── daily_job.py    ← 8:00 AM daily job
│   ├── notifications/
│   │   └── telegram_bot.py ← Telegram alerts
│   └── database/
│       └── models.py       ← SQLite models
├── frontend/               ← Next.js dashboard (port 3000)
└── mcp-server/
    └── server.py           ← MCP tools untuk AI control
```

---

## ⚙️ Configuration (.env)

Edit file `.env` untuk tukar settings:

| Variable | Default | Keterangan |
|----------|---------|-----------|
| `LUNO_API_KEY` | your key | API Key dari Luno |
| `LUNO_API_SECRET` | your secret | API Secret dari Luno |
| `TELEGRAM_BOT_TOKEN` | - | Dari @BotFather |
| `TELEGRAM_CHAT_ID` | - | Your Telegram chat ID |
| `DAILY_AMOUNT_MYR` | 5.0 | RM invest setiap hari |
| `BUY_THRESHOLD_PCT` | 1.5 | % jatuh sebelum beli |
| `SELL_THRESHOLD_PCT` | 2.0 | % naik sebelum jual |
| `SCHEDULE_TIME` | 08:00 | Waktu run harian |
| `MAX_CAPITAL_MYR` | 100.0 | Modal maksimum |

---

## 📲 Setup Telegram

1. Pergi ke Telegram, cari **@BotFather**
2. Taip `/newbot`, ikut arahan
3. Copy **Bot Token** → letak dalam `.env`
4. Pergi ke `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Hantar mesej ke bot anda, refresh link tu
6. Copy **chat_id** → letak dalam `.env`

---

## 🤖 MCP Server Tools

| Tool | Fungsi |
|------|--------|
| `get_bot_status` | Status ON/OFF + next run |
| `get_price` | Harga BTC/MYR semasa |
| `get_balance` | Baki RM dan BTC |
| `get_portfolio` | Nilai portfolio + P&L |
| `get_signal` | Signal BUY/SELL/HOLD |
| `get_trades` | History trades |
| `get_stats` | Statistik trading |
| `update_settings` | Tukar settings |
| `toggle_bot` | ON/OFF bot |
| `trigger_trade_now` | Jalankan bot sekarang |

---

## ⚠️ Disclaimer

Trading cryptocurrency melibatkan risiko tinggi. Bot ini tidak menjamin keuntungan. 
Guna hanya wang yang anda sanggup risiko. Buat due diligence sebelum invest.
