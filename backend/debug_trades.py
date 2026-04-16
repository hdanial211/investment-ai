"""Debug: Check trade records in DB"""
import sys; sys.path.insert(0, '.')
from database.models import SessionLocal, Trade, GridState

db = SessionLocal()

# Check all recent trades
trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(20).all()
print("=== Recent Trades (last 20) ===")
for t in trades:
    pair_val = getattr(t, 'pair', 'NO_PAIR_COL')
    print(f"  ID={t.id} | pair={pair_val!r} | type={t.trade_type} | price=RM{t.price_myr:,.2f} | signal={t.signal} | {t.created_at}")

# Check GridState base prices
print("\n=== GridState ===")
for gs in db.query(GridState).all():
    print(f"  {gs.pair}: enabled={gs.enabled}, base_price=RM{gs.base_price_myr}, trade_size=RM{gs.trade_size_myr}")

db.close()
