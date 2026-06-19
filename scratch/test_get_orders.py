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

def test_get_users_orders(pair_name=None):
    endpoint = "/orderbook/sapi/users/orders"
    timestamp = str(int(time.time()))
    params = {
        "timestamp": timestamp,
    }
    if pair_name:
        params["pair_name"] = pair_name
        
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    print(f"GET {url} with params: {params}")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print("Status Code:", response.status_code)
        print("Response Keys:", response.json().keys() if response.status_code == 200 else "N/A")
        print("Response JSON:", response.text[:2000]) # Print first 2000 chars of response
    except Exception as e:
        print("Error:", e)

# Test without pair_name first, then with XRPMYR
test_get_users_orders()
test_get_users_orders("XRPMYR")
