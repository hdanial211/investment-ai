import os
import time
import hmac
import hashlib
import requests
import urllib.parse
import json
from dotenv import load_dotenv

load_dotenv()

HATA_API_KEY = os.getenv("HATA_API_KEY", "")
HATA_API_SECRET = os.getenv("HATA_API_SECRET", "")
BASE_URL = "https://my-api.hata.io"

def try_hash_method(params, method_name, hash_string, json_payload):
    signature = hmac.new(
        HATA_API_SECRET.encode('utf-8'),
        hash_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}/orderbook/sapi/orders/create"
    try:
        response = requests.post(url, json=json_payload, headers=headers, timeout=10)
        print(f"Method: {method_name} | Code: {response.status_code} | Resp: {response.text}")
    except Exception as e:
        print("Error:", e)

# Base params (keys already sorted alphabetically for the JSON payload)
# We will use all strings for simplicity, or ints if needed
params = {
    "is_buy": "true",
    "pair": "BTCMYR",
    "price": "100000",
    "qty": "0.00001",
    "timestamp": int(time.time()),
    "type": "limit"
}

# Method A: URL encode with timestamp as integer in JSON
sorted_params = dict(sorted(params.items()))
hash_str_A = urllib.parse.urlencode(sorted_params)
try_hash_method(params, "URL-Encode (int timestamp)", hash_str_A, params)

# Method B: URL encode with timestamp as string in JSON
params_str = params.copy()
params_str["timestamp"] = str(params_str["timestamp"])
sorted_params_str = dict(sorted(params_str.items()))
hash_str_B = urllib.parse.urlencode(sorted_params_str)
try_hash_method(params_str, "URL-Encode (str timestamp)", hash_str_B, params_str)

# Method C: JSON string (no spaces)
hash_str_C = json.dumps(sorted_params_str, separators=(',', ':'))
try_hash_method(params_str, "JSON dumps (no spaces)", hash_str_C, params_str)

# Method D: JSON string (with spaces)
hash_str_D = json.dumps(sorted_params_str)
try_hash_method(params_str, "JSON dumps (spaces)", hash_str_D, params_str)

# Method E: URL encode with is_buy as actual boolean, timestamp as int
params_bool = params.copy()
params_bool["is_buy"] = True
sorted_params_bool = dict(sorted(params_bool.items()))
hash_str_E = urllib.parse.urlencode(sorted_params_bool).replace("True", "true") # python urlencode makes it True
try_hash_method(params_bool, "URL-Encode (boolean true)", hash_str_E, params_bool)

# Method F: Send payload as URL encoded form data (data=) instead of JSON!
def try_form_data():
    timestamp = str(int(time.time()))
    p = {
        "is_buy": "true",
        "pair": "BTCMYR",
        "price": "100000",
        "qty": "0.00001",
        "timestamp": timestamp,
        "type": "limit"
    }
    sorted_p = dict(sorted(p.items()))
    qs = urllib.parse.urlencode(sorted_p)
    sig = hmac.new(HATA_API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    headers = {"X-API-KEY": HATA_API_KEY, "Signature": sig}
    res = requests.post(f"{BASE_URL}/orderbook/sapi/orders/create", data=p, headers=headers)
    print(f"Method: Form-Data | Code: {res.status_code} | Resp: {res.text}")
try_form_data()

