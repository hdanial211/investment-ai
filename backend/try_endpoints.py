import sys
import time
import requests
sys.path.append('e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI/backend')
import hata_api

def try_endpoint(ep, method="GET"):
    timestamp = str(int(time.time()))
    params = {"timestamp": timestamp}
    sig = hata_api._generate_signature(params, hata_api.HATA_API_SECRET)
    headers = {"X-API-KEY": hata_api.HATA_API_KEY, "Signature": sig}
    url = f"{hata_api.BASE_URL}{ep}"
    res = requests.request(method, url, params=params, headers=headers)
    print(f"Endpoint {ep} -> {res.status_code}")
    if res.status_code == 200:
        print(res.text[:200])

try_endpoint("/orderbook/sapi/orders")
try_endpoint("/orderbook/sapi/open_orders")
try_endpoint("/orderbook/sapi/openOrders")
try_endpoint("/sapi/v1/openOrders")
try_endpoint("/orderbook/sapi/my_orders")
try_endpoint("/orderbook/sapi/order/open")
