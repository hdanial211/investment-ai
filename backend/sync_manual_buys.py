"""
Sync ETH and XRP manual buys from Luno into bot DB.
Data from Luno API:
  ETH: 0.0043 ETH | RM 39.83 | price = 39.83/0.0043 = 9263.95
  XRP: 3.0 XRP    | RM 16.76 | price = 16.76/3.0 = 5.587
"""
import sys; sys.path.insert(0, '.')
from database.models import SessionLocal, Trade, GridState
from datetime import datetime

db = SessionLocal()

# ETH trade
eth_myr    = 39.83
eth_vol    = 0.0043
eth_price  = eth_myr / eth_vol
eth_fee_xp = 2.58e-05 * eth_price  # fee in ETH → convert to MYR

# XRP trade  
xrp_myr   = 16.76
xrp_vol   = 3.0
xrp_price = xrp_myr / xrp_vol
xrp_fee   = 0.018 * xrp_price  # fee in XRP → convert to MYR

trades_to_add = [
    Trade(
        pair="ETHMYR",
        trade_type="BUY",
        amount_myr=eth_myr,
        amount_btc=eth_vol,
        price_myr=round(eth_price, 2),
        fee_myr=round(eth_fee_xp, 4),
        signal="MANUAL_BUY",
        order_id="BXCSSVHEQECY5Z6",
        status="COMPLETED",
    ),
    Trade(
        pair="XRPMYR",
        trade_type="BUY",
        amount_myr=xrp_myr,
        amount_btc=xrp_vol,
        price_myr=round(xrp_price, 4),
        fee_myr=round(xrp_fee, 4),
        signal="MANUAL_BUY",
        order_id="BXM6WURVRUUQY8U",
        status="COMPLETED",
    ),
]

for t in trades_to_add:
    db.add(t)
    print(f"[{t.pair}] Inserted BUY: {t.amount_btc} units @ RM{t.price_myr:,.4f} (RM{t.amount_myr:.2f})")

# Also update base_price in GridState to match actual buy price
for t in trades_to_add:
    gs = db.query(GridState).filter(GridState.pair == t.pair).first()
    if gs:
        gs.base_price_myr = t.price_myr
        print(f"[{t.pair}] GridState base_price => RM{t.price_myr:,.4f}")

db.commit()
db.close()
print("\nDone! Dashboard akan tunjuk Last Beli selepas refresh.")
