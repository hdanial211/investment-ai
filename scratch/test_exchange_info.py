import requests
res = requests.get("https://my-api.hata.io/orderbook/api/v2/exchange-info", timeout=10)
data = res.json()
print("Status:", res.status_code)
print("Keys:", data.keys())
if "data" in data:
    for item in data["data"][:15]:
        print(f"txpair: {item.get('txpair')}, base: {item.get('base')}, quote: {item.get('quote')}, price: {item.get('price')}")
