# shared.py

# A dictionary to hold the state of each coin
# Keys will be something like "BTC", "ETH", "SOL", etc.
# We also keep a global balance.

global_state = {
    "balance_myr": 10000.00,
    "usdt_myr_rate": 4.70,
    "frozen_myr": 0.00,
    "guardian_status": {
        "status": "safe",
        "analysis": "Sistem sedang memulakan Enjin Penjaga AI (Groq)...",
        "recommendation": "Tiada tindakan diperlukan buat masa ini."
    },
    "guardian_last_update": "Never"
}

import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "bot_state.json")

def create_coin_state():
    return {
        "current_price": 0.0,
        "last_signal": 0.0,
        "confidence": 0.0,
        "layers": [],
        "total_pnl": 0.0,
        "trade_amount_myr": 250.0,
        "risk_level": 1,
        "is_auto": False
    }

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                saved_state = json.load(f)
                
            # Merge with default structure to prevent missing keys
            default_state = {
                "ETH": create_coin_state(),
                "BTC": create_coin_state(),
                "SOL": create_coin_state(),
                "XRP": create_coin_state(),
                "LTC": create_coin_state()
            }
            
            for coin in default_state:
                if coin in saved_state:
                    default_state[coin].update(saved_state[coin])
            return default_state
        except Exception as e:
            print(f"Error loading state: {e}")
            
    return {
        "ETH": create_coin_state(),
        "BTC": create_coin_state(),
        "SOL": create_coin_state(),
        "XRP": create_coin_state(),
        "LTC": create_coin_state()
    }

engine_state = load_state()

def save_state():
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(engine_state, f, indent=4)
    except Exception as e:
        print(f"Error saving state: {e}")
