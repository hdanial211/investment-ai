"""
test_sell.py — READ-ONLY diagnostic script
Does NOT modify any DB values. Safe to run anytime.
"""
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from database.models import SessionLocal, BotSettings, Trade
from exchange.luno_client import LunoClient
from config import settings as cfg

db = SessionLocal()
luno = LunoClient()

# Live data
price_data = luno.get_btc_price()
current_price = price_data['last_trade']
balances = luno.get_balances()

# DB state
bot_s = db.query(BotSettings).filter(BotSettings.id==1).first()
base = bot_s.base_price_myr if bot_s else 0
margin = bot_s.rebalance_margin_pct if bot_s else 2.5
trade_size = bot_s.trade_size_myr if bot_s else 35
last_buy = db.query(Trade).filter(Trade.trade_type=="BUY").order_by(Trade.created_at.desc()).first()

sell_target = base * (1 + margin/100)
buy_target  = base * (1 - margin/100)
pct_from_base = ((current_price - base) / base) * 100

print("=" * 55)
print(f"  BTC Price   : RM {current_price:>12,.2f}")
print(f"  MYR Balance : RM {balances['MYR']:>12,.2f}")
print(f"  BTC Balance : {balances['XBT']:>15.8f} BTC")
print("-" * 55)
print(f"  Base Price  : RM {base:>12,.2f}")
print(f"  SELL Target : RM {sell_target:>12,.2f}  (+{margin}%)")
print(f"  BUY Target  : RM {buy_target:>12,.2f}  (-{margin}%)")
print(f"  From Base   : {pct_from_base:>+15.2f}%")
print("-" * 55)
if last_buy:
    pct_from_buy = ((current_price - last_buy.price_myr) / last_buy.price_myr) * 100
    print(f"  Last BUY    : RM {last_buy.price_myr:>12,.2f}  ({last_buy.created_at.strftime('%d %b %H:%M')})")
    print(f"  P&L vs Buy  : {pct_from_buy:>+15.2f}%")
print("=" * 55)

if current_price >= sell_target:
    print(f"  STATUS: ✅ SHOULD SELL — price above target!")
elif current_price <= buy_target:
    print(f"  STATUS: ✅ SHOULD BUY  — price below target!")
else:
    remaining_up   = sell_target - current_price
    remaining_down = current_price - buy_target
    print(f"  STATUS: ⏳ HOLD — need RM {remaining_up:,.0f} more to sell, RM {remaining_down:,.0f} drop to buy")

db.close()
