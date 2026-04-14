import sys, os
sys.path.insert(0, os.path.abspath('.'))
from exchange.luno_client import LunoClient

luno = LunoClient()

# Check order status specifically
order_id = "BXE3XNKTG4S24RH"
try:
    status = luno.get_order_status(order_id)
    print(f"Order {order_id}: state={status['state']} filled={status['volume_filled']} price={status['price']}")
except Exception as e:
    print(f"Error checking order: {e}")

# Check balance
bal = luno.get_balances()
print(f"BTC: {bal['XBT']}  |  MYR: {bal['MYR']}")
