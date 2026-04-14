import sys, os
sys.path.insert(0, os.path.abspath('.'))
from database.models import SessionLocal
from exchange.luno_client import LunoClient
from strategy.decision_maker import DecisionMaker

db = SessionLocal()
luno = LunoClient()

price_data = luno.get_btc_price()
current_price = price_data['last_trade']
balances = luno.get_balances()
print(f'Current Price: RM {current_price:,.2f}')
print(f'Live balances: {balances}')

dm = DecisionMaker(db)
result = dm.decide_rebalance(real_balances=balances, current_price=current_price)
print(f'\nDecision: action={result["action"]}, execute={result["execute"]}')
print(f'Reason: {result["reason"]}')
print(f'Amount MYR: {result["amount_myr"]}')
db.close()
