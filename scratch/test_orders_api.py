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

def test_endpoint(endpoint, params):
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"GET {endpoint} | Params: {list(params.keys())} | Code: {response.status_code}")
        print(f"Resp: {response.text[:1000]}")
    except Exception as e:
        print(f"Error for {endpoint}: {e}")

# 1. Test GET /orderbook/sapi/orders
print("\n--- Testing GET /orderbook/sapi/orders ---")
test_endpoint("/orderbook/sapi/orders", {"timestamp": str(int(time.time())), "pair": "XRPMYR"})
test_endpoint("/orderbook/sapi/orders", {"timestamp": str(int(time.time())), "pair_name": "XRPMYR"})
test_endpoint("/orderbook/sapi/orders", {"timestamp": str(int(time.time())), "symbol": "XRPMYR"})

# 2. Test GET /orderbook/sapi/order/details
print("\n--- Testing GET /orderbook/sapi/order/details ---")
test_endpoint("/orderbook/sapi/order/details", {"timestamp": str(int(time.time())), "orderId": "241439511"})
test_endpoint("/orderbook/sapi/order/details", {"timestamp": str(int(time.time())), "order_id": "241439511"})
test_endpoint("/orderbook/sapi/order/details", {"timestamp": str(int(time.time())), "id": "241439511"})
test_endpoint("/orderbook/sapi/order/details", {"timestamp": str(int(time.time())), "symbol": "XRPMYR", "orderId": "241439511"})
test_endpoint("/orderbook/sapi/order/details", {"timestamp": str(int(time.time())), "pair": "XRPMYR", "orderId": "241439511"})
