"""
Update trade_size_myr per pair:
- XRPMYR: RM 20
- ETHMYR: RM 40
- XBTMYR: RM 35 (unchanged)
- SOLMYR: RM 35 (unchanged)
"""
import sys; sys.path.insert(0, '.')
from database.models import SessionLocal, GridState

db = SessionLocal()

updates = {
    "XRPMYR": {"trade_size_myr": 20.0},
    "ETHMYR":  {"trade_size_myr": 40.0},
}

for pair, vals in updates.items():
    gs = db.query(GridState).filter(GridState.pair == pair).first()
    if gs:
        for k, v in vals.items():
            setattr(gs, k, v)
        print(f"[{pair}] trade_size_myr => RM {vals['trade_size_myr']:.0f}")
    else:
        print(f"[{pair}] NOT FOUND in DB")

db.commit()
db.close()
print("\nDone! Semua dikemaskini.")

# Verify
db2 = SessionLocal()
for gs in db2.query(GridState).all():
    print(f"  {gs.pair}: trade_size=RM{gs.trade_size_myr}, enabled={gs.enabled}")
db2.close()
