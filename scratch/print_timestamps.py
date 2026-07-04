from datetime import datetime
import json

def main():
    with open("backend/bot_state.json", "r") as f:
        data = json.load(f)
    for coin, info in data.items():
        if not isinstance(info, dict):
            continue
        # Grid Paired Orders: iterate groups[].layers[]
        groups = info.get("groups", [])
        all_layers = []
        for g in groups:
            all_layers.extend(g.get("layers", []))
        if not all_layers:
            continue
        print(f"Coin: {coin}")
        for layer in all_layers:
            created_at = layer.get("created_at")
            if created_at:
                dt = datetime.fromtimestamp(created_at)
                print(f"  Layer {layer.get('id')}: {layer.get('status')} | Created At: {dt} ({created_at})")
            else:
                print(f"  Layer {layer.get('id')}: {layer.get('status')} | Created At: None")

if __name__ == "__main__":
    main()
