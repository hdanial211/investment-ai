import urllib.request
import json

def fetch_state():
    url = "http://127.0.0.1:8000/api/state"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Auto-Healing Monitor'})
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                print("Global state:")
                for k, v in data['global'].items():
                    print(f"  {k}: {v}")
                print("\nCoins:")
                for coin, state in data['coins'].items():
                    print(f"  {coin}: PNL = {state.get('total_pnl')}, Risk = {state.get('risk_level')}, Layers = {len(state.get('layers', []))}, Auto = {state.get('is_auto')}")
            else:
                print(f"API State Response code: {response.status}")
    except Exception as e:
        print(f"Failed to fetch state: {e}")

if __name__ == "__main__":
    fetch_state()
