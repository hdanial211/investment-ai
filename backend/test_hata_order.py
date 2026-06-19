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
    # URL-encode the alphabetically sorted params
    sorted_params = dict(sorted(params.items()))
    query_string = urllib.parse.urlencode(sorted_params)
    signature = hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_order(params):
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}/orderbook/sapi/orders/create"
    print(f"Testing with params: {params}")
    try:
        response = requests.post(url, json=params, headers=headers, timeout=10)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)

# Test 1: all strings
params1 = {
    "is_buy": "true",
    "pair": "BTCMYR",
    "price": "100000",
    "qty": "0.00001",
    "timestamp": str(int(time.time())),
    "type": "limit"
}
test_order(params1)

# Test 2: timestamp as integer
params2 = {
    "is_buy": "true",
    "pair": "BTCMYR",
    "price": "100000",
    "qty": "0.00001",
    "timestamp": int(time.time()),
    "type": "limit"
}
test_order(params2)

# Test 3: is_buy as boolean, timestamp as integer
params3 = {
    "is_buy": True,
    "pair": "BTCMYR",
    "price": "100000",
    "qty": "0.00001",
    "timestamp": int(time.time()),
    "type": "limit"
}
test_order(params3)
