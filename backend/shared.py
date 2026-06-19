# shared.py
import json
import os
import time

# A dictionary to hold the state of each coin
# Keys will be something like "BTC", "ETH", "SOL", etc.
# We also keep a global balance.

global_state = {
    "balance_myr": 10000.00,
    "usdt_myr_rate": 4.70,
    "frozen_myr": 0.00,
    "guardian_status": {
        "status": "safe",
        "analysis": "Bot sedang memulakan enjin autonomi...",
        "recommendation": "Sila tunggu sistem startup recovery selesai."
    },
    "guardian_last_update": "Never"
}

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


def compute_system_status() -> dict:
    """Compute system health status from current bot state.
    Fully autonomous — no external API calls."""
    pending_buys = []
    pending_sells = []
    stuck_orders = []
    total_layers = 0

    for coin_id, coin_state in engine_state.items():
        for l in coin_state.get("layers", []):
            total_layers += 1
            s = l.get("status", "")
            if s == "PENDING_BUY":
                created_at = l.get("created_at", time.time())
                age_min = (time.time() - created_at) / 60
                pending_buys.append(coin_id)
                if age_min > 3:
                    stuck_orders.append(f"{coin_id} ({age_min:.0f} min)")
            elif s == "PENDING_SELL":
                pending_sells.append(coin_id)

    if stuck_orders:
        return {
            "status": "warning",
            "analysis": f"{len(stuck_orders)} pesanan beli tersangkut: {', '.join(stuck_orders)}. Bot akan membatalkan secara automatik pada minit berikutnya.",
            "recommendation": "Sistem memantau. Auto-cancel akan berlaku jika melebihi 5 minit. Tiada tindakan manual diperlukan."
        }
    elif total_layers == 0:
        return {
            "status": "safe",
            "analysis": "Tiada posisi terbuka. Bot memantau isyarat keyakinan XGBoost untuk semua 5 coin.",
            "recommendation": "Bot akan masuk secara automatik apabila isyarat Golden Entry (> 60%) dikesan."
        }
    else:
        buy_str = f"{len(pending_buys)} beli menunggu ({', '.join(set(pending_buys))})" if pending_buys else "tiada pesanan beli"
        sell_str = f"{len(pending_sells)} jual aktif ({', '.join(set(pending_sells))})" if pending_sells else "tiada pesanan jual"
        return {
            "status": "safe",
            "analysis": f"Operasi normal. {total_layers} lapisan aktif — {buy_str}, {sell_str}.",
            "recommendation": "Bot berjalan lancar. Auto-layer (1% DCA) akan dicetuskan apabila pesanan jual selesai."
        }

