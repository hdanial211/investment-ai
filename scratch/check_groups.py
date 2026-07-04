import json

with open("backend/bot_state.json") as f:
    d = json.load(f)

coins = d.get("engine_state", {})
global_state = d.get("global_state", {})
print(f"frozen_myr: RM{global_state.get('frozen_myr', 0):.2f}\n")

for c, state in coins.items():
    groups = state.get("groups", [])
    if not groups:
        continue
    mode = state.get("system_mode", "?")
    risk = state.get("risk_level", 1)
    gap = state.get("grid_gap_pct", 0.01)
    print(f"=== {c} | mode={mode} | risk={risk} | gap={gap*100:.1f}% ===")
    for g in groups:
        layers = g.get("layers", [])
        standby_id = g.get("standby_buy_order_id")
        standby_price = g.get("standby_buy_price", 0)
        holding = [l for l in layers if l.get("status") == "HOLDING"]
        pending = [l for l in layers if l.get("status") == "PENDING_BUY"]
        print(f"  Group {g['id']}: {len(layers)} layers ({len(holding)} HOLDING, {len(pending)} PENDING_BUY)")
        print(f"           standby_buy_id={standby_id} @ RM{standby_price}")
        for l in layers:
            print(f"    Layer {l['id']}: {l['status']} | entry=RM{l.get('entry_price',0)} | sell_id={l.get('sell_order_id')}")
    print()
