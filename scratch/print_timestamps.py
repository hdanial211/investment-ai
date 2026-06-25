from datetime import datetime
import json

def main():
    with open("backend/bot_state.json", "r") as f:
        data = json.load(f)
    for coin, info in data.items():
        print(f"Coin: {coin}")
        for layer in info.get("layers", []):
            created_at = layer.get("created_at")
            if created_at:
                dt = datetime.fromtimestamp(created_at)
                print(f"  Layer {layer.get('id')}: {layer.get('status')} | Created At: {dt} ({created_at})")
            else:
                print(f"  Layer {layer.get('id')}: {layer.get('status')} | Created At: None")

if __name__ == "__main__":
    main()
