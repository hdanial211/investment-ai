import os
import time
import hmac
import hashlib
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

HATA_API_KEY = os.getenv("HATA_API_KEY", "")
HATA_API_SECRET = os.getenv("HATA_API_SECRET", "")
BASE_URL = "https://my-api.hata.io"

def _generate_signature(params: dict, secret: str) -> str:
    sorted_params = dict(sorted(params.items()))
    query_string = urllib.parse.urlencode(sorted_params)
    signature = hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def check_history():
    endpoint = "/orderbook/sapi/trades/history"
    timestamp = str(int(time.time()))
    params = {
        "symbol": "XRP",
        "page": 1,
        "rows": 20,
        "timestamp": timestamp
    }
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print("Code:", response.status_code)
    if response.status_code == 200:
        trades = response.json().get("data", {}).get("trades", [])
        print(f"Total trades found: {len(trades)}")
        for t in trades[:15]:  # Print last 15 trades
            print(f"Pair: {t.get('pair_name'):8} | Side: {'BUY' if t.get('is_buy') else 'SELL':4} | Price: {t.get('price'):10} | Qty: {t.get('qty'):10} | Time: {t.get('time')}")
    else:
        print("Response:", response.text)

check_history()
