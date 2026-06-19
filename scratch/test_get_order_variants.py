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

def test_get_order(params):
    endpoint = "/orderbook/sapi/order"
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Params: {list(params.keys())} | Values: {params} | Code: {response.status_code}")
        print(f"Resp: {response.text}")
    except Exception as e:
        print("Error:", e)

# Test combinations for XRP order 241439511
timestamp = str(int(time.time()))

print("--- Testing GET /orderbook/sapi/order Combinations ---")
test_get_order({"timestamp": timestamp, "pair": "XRPMYR", "orderId": "241439511"})
test_get_order({"timestamp": timestamp, "pair": "XRPMYR", "order_id": "241439511"})
test_get_order({"timestamp": timestamp, "pair": "XRPMYR", "id": "241439511"})
test_get_order({"timestamp": timestamp, "symbol": "XRPMYR", "orderId": "241439511"})
test_get_order({"timestamp": timestamp, "symbol": "XRPMYR", "order_id": "241439511"})
test_get_order({"timestamp": timestamp, "symbol": "XRPMYR", "id": "241439511"})
test_get_order({"timestamp": timestamp, "orderId": "241439511"})
test_get_order({"timestamp": timestamp, "order_id": "241439511"})
