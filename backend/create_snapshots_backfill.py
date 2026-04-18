"""
create_snapshots_backfill.py
1. Create portfolio_snapshots table jika belum ada
2. Backfill historical snapshots guna Luno candles (OHLCV) untuk 7 hari lepas
   → Nilai portfolio = (XBT × harga_BTC_masa_tu) + MYR_cash
   → Ini bagi chart smooth macam Luno

Run sekali sahaja: python create_snapshots_backfill.py
"""
import sys, os, time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.models import Base, Portfolio, Trade, engine, SessionLocal
from exchange.luno_client import LunoClient

# 1. Create table
print("📦 Creating portfolio_snapshots table...")
Base.metadata.create_all(bind=engine)
print("✅ Table created (or already exists)")

client = LunoClient()
db     = SessionLocal()

# 2. Check berapa snapshot dah ada
existing = db.query(Portfolio).count()
print(f"📊 Existing snapshots: {existing}")

# 3. Ambil live balances sekarang
try:
    balances = client.get_balances()
    myr_bal  = balances.get("MYR", 0.0)
    xbt_bal  = balances.get("XBT", 0.0)
    print(f"💰 Live balances — MYR: RM{myr_bal:.2f}, XBT: {xbt_bal:.8f}")
except Exception as e:
    print(f"❌ Cannot get balances: {e}")
    db.close()
    sys.exit(1)

# 4. Backfill 7 hari guna Luno candles API (1hr candles = 168 titik)
# Luno candles endpoint: GET /api/exchange/1/candles?pair=XBTMYR&duration=3600&since=<timestamp_ms>
PAIRS_ASSETS = {
    "XBTMYR": "XBT",
    "ETHMYR": "ETH",
    "XRPMYR": "XRP",
    "SOLMYR": "SOL",
}

print("\n📡 Fetching Luno candle data (1hr candles × 7 days)...")

# Ambil harga per jam untuk setiap pair — dict[pair] → {timestamp_ms: price}
price_by_time: dict[str, dict[int, float]] = {}

since_ms = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp() * 1000)

for pair, asset in PAIRS_ASSETS.items():
    price_by_time[pair] = {}
    try:
        import requests
        url    = f"https://api.luno.com/api/exchange/1/candles?pair={pair}&duration=3600&since={since_ms}"
        r      = requests.get(url, timeout=10)
        data   = r.json()
        candles = data.get("candles", [])
        for c in candles:
            ts   = int(c["timestamp"])
            price_by_time[pair][ts] = float(c["close"])
        print(f"  ✅ {pair}: {len(candles)} candles")
        time.sleep(0.3)
    except Exception as e:
        print(f"  ⚠️  {pair} candles failed: {e}")

# 5. Bina snapshot per jam — gabungkan semua pairs
# Kumpul semua timestamps yang ada
all_ts = sorted(set(
    ts for p_data in price_by_time.values() for ts in p_data
))

print(f"\n🕐 Building {len(all_ts)} hourly snapshots...")

# Ambil DB trades untuk compute cumulative asset balances per time
trades_all = db.query(Trade).filter(Trade.status == "COMPLETED").order_by(Trade.created_at.asc()).all()

# Compute balance-at-time menggunakan trade history
# Logic: on each timestamp, replay trades up to that time
snapshots_added = 0
skipped         = 0

# Convert existing snapshot times untuk avoid duplicates
existing_times = set(
    int(s.snapshot_at.replace(tzinfo=timezone.utc).timestamp() * 1000)
    for s in db.query(Portfolio.snapshot_at).all()
)

for ts_ms in all_ts:
    if ts_ms in existing_times:
        skipped += 1
        continue

    dt_utc = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

    # Replay trades up to this timestamp
    holdings: dict[str, float] = {}
    cash = myr_bal  # Anggap MYR constant (approx)

    for t in trades_all:
        t_ms = int(t.created_at.replace(tzinfo=timezone.utc).timestamp() * 1000)
        if t_ms > ts_ms:
            break
        asset = PAIRS_ASSETS.get(t.pair, "XBT")
        if t.trade_type == "BUY":
            holdings[asset] = holdings.get(asset, 0.0) + t.amount_btc
        else:
            holdings[asset] = max(0.0, holdings.get(asset, 0.0) - t.amount_btc)

    # Nilai holdings pada timestamp ini
    crypto_val = 0.0
    for p, asset in PAIRS_ASSETS.items():
        price_then = price_by_time.get(p, {}).get(ts_ms, 0.0)
        if price_then > 0:
            # Use actual live XBT balance for BTC (known), estimates for others
            vol = xbt_bal if asset == "XBT" else holdings.get(asset, 0.0)
            crypto_val += vol * price_then

    total = round(cash + crypto_val, 2)
    if total <= 0:
        continue

    snap = Portfolio(
        btc_balance = xbt_bal,
        myr_balance = myr_bal,
        btc_price   = price_by_time.get("XBTMYR", {}).get(ts_ms, 0.0),
        total_value = total,
        total_pnl   = 0.0,
        pnl_pct     = 0.0,
        snapshot_at = dt_utc.replace(tzinfo=None),
    )
    db.add(snap)
    snapshots_added += 1

db.commit()
db.close()

print(f"\n✅ Done!")
print(f"   Added:   {snapshots_added} snapshots")
print(f"   Skipped: {skipped} (already existed)")
print(f"\n🔄 Restart backend dan refresh dashboard — chart sepatutnya smooth sekarang!")
