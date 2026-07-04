import sys
import json
sys.path.append('e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI/backend')
import hata_api

total = 0
for coin in ['BTC', 'ETH', 'SOL', 'XRP', 'LTC']:
    orders = hata_api.get_my_orders(f'{coin}_MYR')
    if 'data' in orders:
        open_orders = [o for o in orders['data'] if o.get('status') in ['open', 'pending']]
        total += len(open_orders)
        for o in open_orders:
            print(f"{o.get('market')} {o.get('side')} {o.get('price')} {o.get('quantity')} {o.get('status')}")
print('Total pending across all coins:', total)
