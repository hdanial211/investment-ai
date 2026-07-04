import json
import time
import sys

STATE_FILE = "e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI/backend/bot_state.json"

with open(STATE_FILE, "r") as f:
    state = json.load(f)

changed = False
for coin, data in state.items():
    legacy_layers = data.get("layers", [])
    if not legacy_layers:
        continue
    
    print(f"Migrating {len(legacy_layers)} legacy layers for {coin}...")
    changed = True
    
    groups = data.get("groups", [])
    if not groups:
        groups.append({
            "id": 1,
            "layers": [],
            "status": "ACTIVE",
            "created_at": time.time(),
            "standby_buy_order_id": data.get("standby_buy_order_id"),
            "standby_buy_price": data.get("standby_buy_price", 0.0)
        })
        data["groups"] = groups
    
    first_group = groups[0]
    
    # Combine
    all_layers = legacy_layers + first_group.get("layers", [])
    
    # Sort by entry_price descending (highest price is layer 1)
    all_layers.sort(key=lambda x: x.get("entry_price", 0), reverse=True)
    
    # Reassign IDs
    for i, l in enumerate(all_layers):
        l["id"] = i + 1
        
    first_group["layers"] = all_layers
    
    # Clean up legacy
    data["layers"] = []
    data["consolidated_sell_order_id"] = None
    if "standby_buy_order_id" in data:
        data["standby_buy_order_id"] = None
        data["standby_buy_price"] = 0.0

if changed:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)
    print("Migration complete.")
else:
    print("No legacy layers to migrate.")
