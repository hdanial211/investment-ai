# shared.py
import log_config
import json
import logging
import os
import tempfile
import threading
import time

logger = logging.getLogger(__name__)

# Thread-safe lock for save_state() — prevents concurrent writes
# from FastAPI thread + live_engine thread corrupting bot_state.json
_state_lock = threading.Lock()

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
        "total_pnl": 0.0,
        "trade_amount_myr": 250.0,
        "risk_level": 1,
        "is_auto": False,
        "tp_pct": 0.005,
        "last_cycle_entry": 0.0,
        # ── Grid Multi-Group settings ──
        "groups": [],                    # List of active trading groups (each has layers + standby buy)
        "grid_gap_pct": 0.01,           # Gap % between buy/sell levels per layer (configurable per coin)
        "max_layers": 0,                 # Max layers per group (0 = risk_level default: 3/5/6)
        "max_groups": 3,                 # Max concurrent groups per coin (configurable)
        "new_group_gap_pct": 0.02,       # % below lowest layer to start new group (configurable per coin)
        "system_mode": "grid",           # 'grid' = new system
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
    "BTC": 0.004,
    "ETH": 0.005,
    "SOL": 0.008,
    "XRP": 0.006,
    "LTC": 0.004,
}

def _migrate_coin_state(coin: dict) -> dict:
    """Migrate old flat-layer state to new multi-group state.
    Also cleans orphaned fields from the old DCA system."""
    # Clean orphaned flat-layer fields (from old DCA system)
    _orphan_fields = ["consolidated_sell_order_id"]
    for field in _orphan_fields:
        coin.pop(field, None)

    # If already has 'groups', it's the new format
    if "groups" in coin:
        # Clean leftover flat 'layers' if groups already exist
        if "layers" in coin and not coin["layers"]:
            coin.pop("layers", None)
        # Clean leftover flat standby fields if groups already exist
        if coin.get("standby_buy_order_id") is None:
            coin.pop("standby_buy_order_id", None)
        if coin.get("standby_buy_price", 0.0) == 0.0:
            coin.pop("standby_buy_price", None)
        # Ensure new fields exist
        coin.setdefault("max_groups", 3)
        coin.setdefault("new_group_gap_pct", 0.02)
        coin.setdefault("max_layers", 0)
        return coin

    # Migrate: wrap old layers + standby_buy into group #1
    old_layers = coin.pop("layers", [])
    old_standby_id = coin.pop("standby_buy_order_id", None)
    old_standby_price = coin.pop("standby_buy_price", 0.0)

    coin["groups"] = []
    if old_layers:
        coin["groups"].append({
            "id": 1,
            "layers": old_layers,
            "standby_buy_order_id": old_standby_id,
            "standby_buy_price": old_standby_price,
            "created_at": time.time()
        })

    coin.setdefault("max_groups", 3)
    coin.setdefault("new_group_gap_pct", 0.02)
    coin.setdefault("max_layers", 0)
    coin.setdefault("system_mode", "grid")
    return coin


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                saved_state = json.load(f)

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
                    # Migrate old format to new multi-group format
                    default_state[coin] = _migrate_coin_state(default_state[coin])
                # Apply AI-suggested TP if still at generic default
                if default_state[coin].get("tp_pct", 0.005) == 0.005 and coin in AI_SUGGESTED_TP:
                    default_state[coin]["tp_pct"] = AI_SUGGESTED_TP[coin]
            return default_state
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            # Return fresh state instead of None to prevent crashes
            fresh = {
                "ETH": create_coin_state(),
                "BTC": create_coin_state(),
                "SOL": create_coin_state(),
                "XRP": create_coin_state(),
                "LTC": create_coin_state()
            }
            for c in fresh:
                if c in AI_SUGGESTED_TP:
                    fresh[c]["tp_pct"] = AI_SUGGESTED_TP[c]
            return fresh

    # Fresh state
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
    """Thread-safe atomic save — writes to temp file first, then renames.
    Prevents data corruption from concurrent writes or mid-write crashes."""
    with _state_lock:
        try:
            # Atomic write: write to temp file in same directory, then rename
            dir_name = os.path.dirname(STATE_FILE)
            fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=dir_name)
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(engine_state, f, indent=4)
                # Atomic rename (on Windows, need to remove target first)
                if os.path.exists(STATE_FILE):
                    os.replace(tmp_path, STATE_FILE)
                else:
                    os.rename(tmp_path, STATE_FILE)
            except Exception:
                # Clean up temp file on failure
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise
        except Exception as e:
            logger.error(f"Error saving state: {e}")


def truncate_float(val: float, decimals: int) -> float:
    """Truncate float value to specific decimal places without rounding up.
    Shared utility used by api.py and live_engine.py."""
    eps = 1e-9
    factor = 10 ** decimals
    return int((val + eps) * factor) / factor


def compute_system_status() -> dict:
    """Compute system health status from current bot state."""
    pending_buys = []
    holding_coins = []
    stuck_orders = []
    total_layers = 0
    total_groups = 0
    standby_coins = []

    for coin_id, coin_state in engine_state.items():
        for group in coin_state.get("groups", []):
            total_groups += 1
            for l in group.get("layers", []):
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
            if group.get("standby_buy_order_id"):
                standby_coins.append(coin_id)

    if stuck_orders:
        return {
            "status": "warning",
            "analysis": f"{len(stuck_orders)} pesanan beli tersangkut: {', '.join(stuck_orders)}.",
            "recommendation": "Auto-cancel akan berlaku jika melebihi 5 minit."
        }
    elif total_layers == 0:
        return {
            "status": "safe",
            "analysis": "Tiada posisi terbuka. Bot memantau isyarat XGBoost untuk semua 5 coin.",
            "recommendation": "Bot akan masuk apabila isyarat Golden Entry (>60%) dikesan."
        }
    else:
        buy_str = f"{len(pending_buys)} pending ({', '.join(set(pending_buys))})" if pending_buys else "tiada pending"
        hold_str = f"{len(set(holding_coins))} coin holding ({', '.join(set(holding_coins))})" if holding_coins else ""
        standby_str = f"standby buy: {', '.join(set(standby_coins))}" if standby_coins else ""
        parts = filter(None, [buy_str, hold_str, standby_str])
        analysis = f"Operasi normal. {total_groups} group, {total_layers} layers aktif — {' | '.join(parts)}."

        return {
            "status": "safe",
            "analysis": analysis,
            "recommendation": "Grid Multi-Group berjalan. Setiap layer ada sell sendiri (Maker 0%). Standby BUY per group aktif."
        }
