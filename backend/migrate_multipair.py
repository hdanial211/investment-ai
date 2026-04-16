"""
migrate_multipair.py — Setup database untuk multi-pair trading
"""
import sys, os
sys.path.insert(0, os.path.abspath('.'))

from database.models import engine, Base, GridState, SessionLocal, BotSettings, create_tables
from sqlalchemy import text

# Step 1: Create new tables (GridState etc)
create_tables()
print("Tables created/updated")

# Step 2: Add pair column to trades if not exists
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE trades ADD COLUMN pair VARCHAR DEFAULT 'XBTMYR'"))
        conn.commit()
        print("pair column added to trades")
    except Exception as e:
        print(f"pair column already exists: {e}")

# Step 3: Seed GridState with 4 pairs
db = SessionLocal()

# Get existing BTC base_price from BotSettings
bot_s = db.query(BotSettings).filter(BotSettings.id == 1).first()
btc_base = bot_s.base_price_myr if bot_s else 0.0

pairs_config = [
    {"pair": "XBTMYR", "display_name": "Bitcoin (BTC)",  "base_currency": "XBT", "margin": 2.5, "size": 35.0, "enabled": True,  "base": btc_base},
    {"pair": "ETHMYR", "display_name": "Ethereum (ETH)", "base_currency": "ETH", "margin": 2.5, "size": 35.0, "enabled": False, "base": 0.0},
    {"pair": "XRPMYR", "display_name": "Ripple (XRP)",   "base_currency": "XRP", "margin": 3.0, "size": 35.0, "enabled": False, "base": 0.0},
    {"pair": "SOLMYR", "display_name": "Solana (SOL)",   "base_currency": "SOL", "margin": 3.0, "size": 35.0, "enabled": False, "base": 0.0},
]

for p in pairs_config:
    existing = db.query(GridState).filter(GridState.pair == p["pair"]).first()
    if not existing:
        gs = GridState(
            pair=p["pair"],
            display_name=p["display_name"],
            base_currency=p["base_currency"],
            enabled=p["enabled"],
            base_price_myr=p["base"],
            rebalance_margin_pct=p["margin"],
            trade_size_myr=p["size"],
        )
        db.add(gs)
        print(f"Added GridState: {p['pair']} | enabled={p['enabled']}")
    else:
        print(f"Already exists:  {p['pair']}")

db.commit()

# Verify
all_states = db.query(GridState).all()
print("\n=== GridState Table ===")
for g in all_states:
    print(f"  {g.pair:10} | {g.display_name:20} | enabled={g.enabled} | base=RM {g.base_price_myr:,.0f} | margin={g.rebalance_margin_pct}%")

db.close()
print("\nMigration complete!")
