"""
Fix pnl_myr yang salah dalam Trade DB berdasarkan FIFO cost basis.
"""
import sys; sys.path.insert(0, '.')
from database.models import SessionLocal, Trade

db = SessionLocal()

# Ambil semua BTC trades ikut tarikh
btc_buys  = db.query(Trade).filter(Trade.pair=="XBTMYR", Trade.trade_type=="BUY",  Trade.status=="COMPLETED").order_by(Trade.created_at).all()
btc_sells = db.query(Trade).filter(Trade.pair=="XBTMYR", Trade.trade_type=="SELL", Trade.status=="COMPLETED").order_by(Trade.created_at).all()

print("=== BUY trades ===")
for t in btc_buys:
    print(f"  id={t.id} | {t.amount_myr:.4f} MYR | {t.amount_btc:.8f} BTC | @{t.price_myr:.0f} | pnl={t.pnl_myr}")

print("\n=== SELL trades (before fix) ===")
for t in btc_sells:
    print(f"  id={t.id} | {t.amount_myr:.4f} MYR | {t.amount_btc:.8f} BTC | @{t.price_myr:.0f} | pnl={t.pnl_myr}")

# FIFO recalculate
buy_queue = []  # [(unit, cost_per_unit)]
for b in btc_buys:
    buy_queue.append([b.amount_btc, b.price_myr])  # [units_remaining, cost_price]

print("\n=== FIFO recalculate ===")
for sell in btc_sells:
    units_to_sell = sell.amount_btc
    proceeds      = sell.amount_myr
    cost_basis    = 0.0
    units_matched = 0.0

    for entry in buy_queue:
        if units_to_sell <= 0:
            break
        avail = entry[0]
        if avail <= 0:
            continue
        matched     = min(avail, units_to_sell)
        cost_basis  += matched * entry[1]    # matched units × buy price
        units_matched += matched
        entry[0]    -= matched
        units_to_sell -= matched

    # Only attribute proceeds proportional to matched/sold ratio
    if sell.amount_btc > 0:
        ratio            = units_matched / sell.amount_btc
        attributed_sell  = proceeds * ratio
        correct_pnl      = attributed_sell - cost_basis
    else:
        correct_pnl = 0.0

    print(f"  id={sell.id} | proceeds=RM{proceeds:.4f} | matched={units_matched:.8f}/{sell.amount_btc:.8f} | cost=RM{cost_basis:.4f} | pnl_lama=RM{sell.pnl_myr:.4f} -> pnl_betul=RM{correct_pnl:.4f}")

    # Update DB
    sell.pnl_myr = round(correct_pnl, 4)

db.commit()
print("\n✅ DB updated!")
