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

def test_history(params):
    endpoint = "/orderbook/sapi/trades/history"
    params["timestamp"] = str(int(time.time()))
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    response = requests.get(url, params=params, headers=headers, timeout=5)
    print(f"Params: {list(params.keys())} | Code: {response.status_code} | Resp: {response.text[:200]}")

print("--- Testing trades/history rows ---")
test_history({"symbol": "XRPMYR", "page": 1, "rows": 10})
test_history({"symbol": "XRP", "page": 1, "rows": 10})
test_history({"pair": "XRPMYR", "page": 1, "rows": 10})
test_history({"pair_name": "XRPMYR", "page": 1, "rows": 10})
test_history({"pair": "XRP_MYR", "page": 1, "rows": 10})
test_history({"symbol": "XRPMYR", "page": "1", "rows": "10"})
test_history({"pair": "XRPMYR", "page": "1", "rows": "10"})
