import sys
sys.path.append('e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI/backend')
import hata_api

for coin in ['XRP', 'LTC']:
    print(f"--- {coin} ---")
    res = hata_api.get_my_orders(f"{coin}_MYR")
    orders = res.get('data', [])
    for o in orders:
        print(f"Order: {o.get('id')} - {o.get('side')} - {o.get('price')} - {o.get('quantity')}")
