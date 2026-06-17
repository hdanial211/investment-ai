# shared.py

# A dictionary to hold the state of each coin
# Keys will be something like "BTC", "ETH", "SOL", etc.
# We also keep a global balance.

global_state = {
    "balance_myr": 10000.00,
    "is_auto": False,
    "usdt_myr_rate": 4.70,
}

def create_coin_state():
    return {
        "current_price": 0.0,
        "last_signal": 0.0,
        "confidence": 0.0,
        "layers": [],
        "total_pnl": 0.0,
        "trade_amount_myr": 50.0
    }

engine_state = {
    "ETH": create_coin_state(),
    "BTC": create_coin_state(),
    "SOL": create_coin_state(),
    "XRP": create_coin_state(),
    "LTC": create_coin_state()
}
