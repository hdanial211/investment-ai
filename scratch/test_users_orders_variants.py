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

def test_users_orders(params):
    endpoint = "/orderbook/sapi/users/orders"
    params["timestamp"] = str(int(time.time()))
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Params: {list(params.keys())} | Values: {params} | Code: {response.status_code}")
    if response.status_code == 200:
        print("Resp:", response.json())
    else:
        print("Resp:", response.text)

print("--- Testing GET /orderbook/sapi/users/orders ---")
test_users_orders({"pair": "XRPMYR"})
test_users_orders({"symbol": "XRPMYR"})
test_users_orders({"pair_name": "XRPMYR"})
test_users_orders({"status": "active"})
test_users_orders({"pair": "XRPMYR", "status": "active"})
test_users_orders({"pair_name": "XRPMYR", "status": "active"})
