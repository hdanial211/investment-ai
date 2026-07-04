import json
d = json.load(open('e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI/backend/bot_state.json'))
for coin in ['XRP', 'LTC']:
    groups = d[coin].get('groups', [])
    for g in groups:
        for l in g.get('layers', []):
            print(f"{coin} Layer {l.get('id')} sell_order_id: {l.get('sell_order_id')}")
