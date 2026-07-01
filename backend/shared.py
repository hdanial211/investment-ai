# shared.py
import log_config
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
        "is_auto": False,
        "tp_pct": 0.005,
        "consolidated_sell_order_id": None,  # Keep for backward compat (old DCA system)
        "last_cycle_entry": 0.0,
        # ── Grid Paired Orders settings ──
        "grid_gap_pct": 0.01,               # Gap % between buy/sell levels (configurable per coin)
        "standby_buy_order_id": None,        # Single cascade standby BUY below current position
        "standby_buy_price": 0.0,            # Price of standby BUY
        "system_mode": "grid",               # 'grid' = new system, 'dca' = old system
        "max_layers": 0,                     # 0 = guna risk_level default (3/5/6), >0 = custom per coin

        # ── Adaptive ML Pipeline (per-coin, independent) ──
        "model_version": "v1",
        "trades_since_retrain": 0,
        "last_retrain_at": None,
        "adaptive_threshold": 0.60,
        "active_trade_cycle_id": None,
        "ml_stats": {
            "total_predictions": 0,
            "total_trades_logged": 0,
            "recent_win_rate": 0.0,
            "model_accuracy": 0.0,
            "threshold_label": "Default",
            "threshold_sample_size": 0
        }
    }
# AI-suggested TP% per coin (from training data volatility analysis)
AI_SUGGESTED_TP = {
    "BTC": 0.004,   # 0.4% — Large cap, low volatility
    "ETH": 0.005,   # 0.5% — Medium volatility
    "SOL": 0.008,   # 0.8% — High volatility
    "XRP": 0.006,   # 0.6% — Medium-high volatility
    "LTC": 0.004,   # 0.4% — Low volatility
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
                # Apply AI-suggested TP if still at generic default
                if default_state[coin].get("tp_pct", 0.005) == 0.005 and coin in AI_SUGGESTED_TP:
                    default_state[coin]["tp_pct"] = AI_SUGGESTED_TP[coin]
            return default_state
        except Exception as e:
            print(f"Error loading state: {e}")
            
    # Fresh state — apply AI-suggested TP per coin
    fresh = {
        "ETH": create_coin_state(),
        "BTC": create_coin_state(),
        "SOL": create_coin_state(),
        "XRP": create_coin_state(),
        "LTC": create_coin_state()
    }
    for coin in fresh:
        if coin in AI_SUGGESTED_TP:
            fresh[coin]["tp_pct"] = AI_SUGGESTED_TP[coin]
    return fresh

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
    holding_coins = []
    stuck_orders = []
    total_layers = 0
    coins_with_consolidated_sell = []

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
            elif s == "HOLDING":
                holding_coins.append(coin_id)
        
        if coin_state.get("consolidated_sell_order_id"):
            coins_with_consolidated_sell.append(coin_id)

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
        hold_str = f"{len(set(holding_coins))} coin holding ({', '.join(set(holding_coins))})" if holding_coins else "tiada holding"
        sell_str = f"Gabungan sell aktif: {', '.join(coins_with_consolidated_sell)}" if coins_with_consolidated_sell else "tiada gabungan sell"

        # Grid system extra info: individual sells and standby buys
        grid_sell_coins = []
        standby_buy_coins = []
        for coin_id, coin_state in engine_state.items():
            system_mode = coin_state.get("system_mode", "grid")
            if system_mode == "grid":
                layers_with_sell = [l for l in coin_state.get("layers", []) if l.get("sell_order_id")]
                if layers_with_sell:
                    grid_sell_coins.append(f"{coin_id}({len(layers_with_sell)})")
                if coin_state.get("standby_buy_order_id"):
                    standby_buy_coins.append(coin_id)

        grid_sell_str = f"Grid sell individu: {', '.join(grid_sell_coins)}" if grid_sell_coins else ""
        standby_str = f"Standby buy: {', '.join(standby_buy_coins)}" if standby_buy_coins else ""
        extra = " | ".join(filter(None, [grid_sell_str, standby_str]))

        analysis = f"Operasi normal. {total_layers} lapisan aktif — {buy_str}, {hold_str}. {sell_str}."
        if extra:
            analysis += f" [{extra}]"

        return {
            "status": "safe",
            "analysis": analysis,
            "recommendation": "Bot berjalan lancar. Grid sell individu akan dicetuskan apabila layer baru diisi. Standby buy memantau paras seterusnya."
        }
