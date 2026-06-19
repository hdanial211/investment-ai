import requests

res = requests.get("https://my-api.hata.io/orderbook/api/v2/exchange-info")
data = res.json().get("data", [])
for p in data:
    if p.get("quote_name") == "Malaysian Ringgit" and p.get("base") in ["BTC", "ETH", "SOL", "XRP", "LTC"]:
        print(f"'{p['base']}': {{'qty_scale': {p['disp_qty_scale']}, 'price_scale': {p['disp_price_scale']}}},")
