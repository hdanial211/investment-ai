import sys
sys.path.insert(0, '.')
from exchange.luno_client import luno_client
from database.models import SessionLocal, Trade
import calendar

db = SessionLocal()
e  = db.query(Trade).order_by(Trade.created_at.asc()).first()
ts = int(calendar.timegm(e.created_at.timetuple()) * 1000)
d  = luno_client.get_pnl_from_luno(since_ts_ms=ts)

print("=== P&L BETUL (selepas FIFO cap) ===")
print(f"Modal masuk : RM{d['total_cost']:.2f}")
print(f"Untung BERSIH: RM{d['total_pnl']:.2f}  ({d['pnl_pct']:.2f}%)")
print()
for p, v in d['pairs'].items():
    print(f"  {p}:")
    print(f"    Modal  : RM{v['cost']:.2f}")
    print(f"    Attributed sell: RM{v.get('attributed_sell', v['sold']):.2f}  (raw jual: RM{v['sold']:.2f})")
    print(f"    Unrealised : RM{v['remaining_val']:.2f}  ({v['remaining_vol']:.8f} unit)")
    print(f"    Untung : RM{v['pnl']:.4f}  ({v['num_trades']} trades)")
    print()
