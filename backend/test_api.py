import requests
import time

coins = ['ETH', 'BTC', 'SOL', 'LTC', 'XRP']
for c in coins:
    print(f"--- {c} ---")
    try:
        r1 = requests.post('http://localhost:8000/api/set-risk-level', json={'coin': c, 'risk_level': 3}, timeout=5)
        print("Risk:", r1.json())
        r2 = requests.post('http://localhost:8000/api/set-amount', json={'coin': c, 'amount': 50.0}, timeout=5)
        print("Amount:", r2.json())
        r3 = requests.post('http://localhost:8000/api/toggle-auto', json={'coin': c, 'is_auto': True}, timeout=5)
        print("Auto:", r3.json())
    except Exception as e:
        print("Error:", e)
    time.sleep(0.5)
