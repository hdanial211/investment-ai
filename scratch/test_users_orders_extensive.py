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
    
    response = requests.get(url, params=params, headers=headers, timeout=5)
    if response.status_code == 200:
        print(f"SUCCESS! Params: {list(params.keys())} | Code: {response.status_code}")
        print("Resp:", response.text[:200])
        return True
    return False

# List of parameter sets to try
configs = []

# Try page/rows/limit variants with pair
for p_key in ["pair", "pair_name", "symbol"]:
    p_val = "XRPMYR"
    configs.append({p_key: p_val})
    configs.append({p_key: p_val, "page": 1, "rows": 10})
    configs.append({p_key: p_val, "page": "1", "rows": "10"})
    configs.append({p_key: p_val, "page": 1, "limit": 10})
    configs.append({p_key: p_val, "page": "1", "limit": "10"})
    configs.append({p_key: p_val, "page": 1, "size": 10})
    configs.append({p_key: p_val, "page": "1", "size": "10"})
    configs.append({p_key: p_val, "status": "active"})
    configs.append({p_key: p_val, "status": "active", "page": 1, "limit": 10})

print("Running extensive tests...")
for c in configs:
    if test_users_orders(c):
        print("Found matching combination!")
        break
print("Done.")
