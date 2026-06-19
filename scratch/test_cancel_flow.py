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

def place_test_order():
    endpoint = "/orderbook/sapi/orders/create"
    timestamp = str(int(time.time()))
    params = {
        "is_buy": "true",
        "pair": "LTCMYR",
        "price": "173", # RM 173 (5% below market)
        "qty": "0.100", # 0.1 LTC = RM 17.3
        "timestamp": timestamp,
        "type": "limit"
    }
    signature = _generate_signature(params, HATA_API_SECRET, is_post=True)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    res = requests.post(url, json=params, headers=headers)
    print("Place Order Result:", res.status_code, res.text)
    if res.status_code == 200:
        return res.json().get("data", {}).get("id")
    return None

def test_delete_cancel(order_id):
    endpoint = "/orderbook/sapi/order"
    timestamp = str(int(time.time()))
    # Test with order_id
    params = {
        "timestamp": timestamp,
        "symbol": "BTCMYR",
        "order_id": str(order_id)
    }
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    res = requests.delete(url, params=params, headers=headers)
    print("DELETE cancel (order_id) Result:", res.status_code, res.text)
    
    if res.status_code != 200:
        # Test with orderId
        params = {
            "timestamp": timestamp,
            "symbol": "BTCMYR",
            "orderId": str(order_id)
        }
        signature = _generate_signature(params, HATA_API_SECRET)
        headers["Signature"] = signature
        res = requests.delete(url, params=params, headers=headers)
        print("DELETE cancel (orderId) Result:", res.status_code, res.text)
    return res.status_code == 200

def test_post_cancel(order_id):
    endpoint = "/orderbook/sapi/orders/cancel"
    timestamp = str(int(time.time()))
    params = {
        "order_id": int(order_id),
        "timestamp": int(timestamp)
    }
    signature = _generate_signature(params, HATA_API_SECRET, is_post=True)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    res = requests.post(url, json=params, headers=headers)
    print("POST cancel Result:", res.status_code, res.text)
    return res.status_code == 200

order_id = place_test_order()
if order_id:
    print(f"Placed order with ID: {order_id}")
    time.sleep(1)
    # Try DELETE first
    success = test_delete_cancel(order_id)
    if not success:
        print("DELETE cancel failed, trying POST cancel...")
        test_post_cancel(order_id)
else:
    print("Failed to place test order.")
