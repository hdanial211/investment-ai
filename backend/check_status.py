import sys
import json
sys.path.append('e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI/backend')
import hata_api

d = json.load(open('e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI/backend/bot_state.json'))
for coin in ['XRP', 'LTC']:
    groups = d[coin].get('groups', [])
    for g in groups:
        for l in g.get('layers', []):
            sell_id = l.get('sell_order_id')
            if sell_id:
                res = hata_api.get_order_status(sell_id)
                status = res.get('data', {}).get('status', 'unknown')
                print(f"{coin} Layer {l.get('id')} sell {sell_id}: {status}")
        
        buy_id = g.get('standby_buy_order_id')
        if buy_id:
            res = hata_api.get_order_status(buy_id)
            status = res.get('data', {}).get('status', 'unknown')
            print(f"{coin} standby buy {buy_id}: {status}")
