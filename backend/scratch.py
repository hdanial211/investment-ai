import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://localhost:8000/api/backtest-stream') as ws:
        await ws.send(json.dumps({
            'initial_cash': 100000, 
            'trade_size_fiat': 4000, 
            'max_layers': 6, 
            'drop_threshold': 5.0, 
            'take_profit_pct': 10.0, 
            'trailing_activation_pct': 3.0, 
            'trailing_gap_pct': 1.0
        }))
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print(data.get('type'), data.get('percent') if data.get('type') == 'progress' else '')
            if data.get('type') in ['complete', 'error']:
                break

asyncio.run(test())
