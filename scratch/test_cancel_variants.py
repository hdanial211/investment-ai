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

def _generate_signature(params: dict, secret: str, is_post: bool = False) -> str:
    sorted_params = dict(sorted(params.items()))
    import json
    if is_post:
        query_string = json.dumps(sorted_params, separators=(',', ':'))
    else:
        query_string = urllib.parse.urlencode(sorted_params)
    signature = hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_cancel(order_id, params):
    endpoint = "/orderbook/sapi/orders/cancel"
    # Ensure order_id and timestamp are in params
    params["timestamp"] = str(int(time.time()))
    
    signature = _generate_signature(params, HATA_API_SECRET, is_post=True)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.post(url, json=params, headers=headers, timeout=10)
        print(f"Params: {list(params.keys())} | Values: {params} | Code: {response.status_code}")
        print(f"Resp: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print("Error:", e)
        return False

order_id = "241457083" # From our LTC buy order

# Test variants
print("--- Testing POST /orderbook/sapi/orders/cancel Combinations ---")
if test_cancel(order_id, {"order_id": order_id, "pair": "LTCMYR"}):
    print("Success 1!")
elif test_cancel(order_id, {"order_id": int(order_id), "pair": "LTCMYR"}):
    print("Success 2!")
elif test_cancel(order_id, {"order_id": order_id, "symbol": "LTCMYR"}):
    print("Success 3!")
elif test_cancel(order_id, {"orderId": order_id, "pair": "LTCMYR"}):
    print("Success 4!")
elif test_cancel(order_id, {"orderId": int(order_id), "pair": "LTCMYR"}):
    print("Success 5!")
