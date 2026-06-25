import os
import time
import hmac
import hashlib
import requests
import urllib.parse
import json
from dotenv import load_dotenv

load_dotenv()

HATA_API_KEY = os.getenv("HATA_API_KEY", "")
HATA_API_SECRET = os.getenv("HATA_API_SECRET", "")
BASE_URL = "https://my-api.hata.io" # For Malaysia accounts

def _generate_signature(params: dict, secret: str, is_post: bool = False) -> str:
    # Sort parameters alphabetically by key
    sorted_params = dict(sorted(params.items()))
    
    if is_post:
        # Hata API requires hashing the exact raw JSON string payload with no spaces
        query_string = json.dumps(sorted_params, separators=(',', ':'))
    else:
        # Construct query string for GET requests
        query_string = urllib.parse.urlencode(sorted_params)
        
    # Generate HMAC SHA256 signature
    signature = hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def get_myr_balance() -> tuple:
    """Fetch the real MYR balance (available, frozen) from Hata API"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        print("Warning: HATA_API_KEY or HATA_API_SECRET not found. Using simulated balance.")
        return 10000.00, 0.00
        
    endpoint = "/orderbook/sapi/balance"
    timestamp = str(int(time.time()))
    
    params = {
        "timestamp": timestamp,
        "token_symbol": "MYR"
    }
    
    signature = _generate_signature(params, HATA_API_SECRET)
    
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print("Hata API Balance Response:", data)
        
        if isinstance(data, list):
            for item in data:
                if item.get("symbol") == "MYR":
                    return float(item.get("available", 0.0)), float(item.get("frozen", 0.0))
        elif isinstance(data, dict):
            if "available" in data:
                return float(data.get("available", 0.0)), float(data.get("frozen", 0.0))
            elif "data" in data and isinstance(data["data"], list):
                 for item in data["data"]:
                    if item.get("symbol") == "MYR":
                        return float(item.get("available", 0.0)), float(item.get("frozen", 0.0))
                        
        return 0.0, 0.0
        
    except Exception as e:
        print(f"Error fetching Hata API balance: {e}")
        return 0.0, 0.0

def get_token_balance(symbol: str) -> tuple:
    """Fetch the real token balance (available, frozen) from Hata API"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        return 0.0, 0.0
        
    endpoint = "/orderbook/sapi/balance"
    timestamp = str(int(time.time()))
    
    params = {
        "timestamp": timestamp,
        "token_symbol": symbol.upper()
    }
    
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            for item in data:
                if item.get("symbol") == symbol.upper():
                    return float(item.get("available", 0.0)), float(item.get("frozen", 0.0))
        elif isinstance(data, dict):
            if "available" in data:
                return float(data.get("available", 0.0)), float(data.get("frozen", 0.0))
            elif "data" in data and isinstance(data["data"], list):
                 for item in data["data"]:
                    if item.get("symbol") == symbol.upper():
                        return float(item.get("available", 0.0)), float(item.get("frozen", 0.0))
                        
        return 0.0, 0.0
    except Exception as e:
        print(f"Error fetching Hata API balance for {symbol}: {e}")
        return 0.0, 0.0

def get_order_status(order_id: str) -> dict:
    """Fetch order status/details from Hata API"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        # Simulated mode: assume all orders are fulfilled
        return {"status": "success", "data": {"status": "fulfilled"}}
        
    endpoint = "/orderbook/sapi/order"
    timestamp = str(int(time.time()))
    
    params = {
        "order_id": str(order_id),
        "timestamp": timestamp
    }
    
    signature = _generate_signature(params, HATA_API_SECRET)
    
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching order status for {order_id}: {response.text}")
            return {"status": "error", "message": response.text}
    except Exception as e:
        print(f"Error fetching order status for {order_id}: {e}")
        return {"status": "error", "message": str(e)}

def get_ticker(symbol: str = "ETH_MYR") -> float:
    """Fetch current market price (ticker) from exchange-info"""
    clean_sym = symbol.replace("_", "").upper()
    url = f"{BASE_URL}/orderbook/api/v2/exchange-info"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("data", [])
        for item in items:
            if item.get("txpair") == clean_sym:
                return float(item.get("price", 0.0))
        # Fallback to base + quote check
        for item in items:
            if item.get("base") + item.get("quote") == clean_sym:
                return float(item.get("price", 0.0))
        return 0.0
    except Exception as e:
        print(f"Error fetching ticker for {symbol}: {e}")
        return 0.0

COIN_SCALES = {
    "BTC": {"qty": 5, "price": 0},
    "ETH": {"qty": 4, "price": 0},
    "SOL": {"qty": 3, "price": 1},
    "LTC": {"qty": 3, "price": 1},
    "XRP": {"qty": 1, "price": 3}
}

def place_limit_order(symbol: str, side: str, price: float, quantity: float) -> dict:
    """Place a Limit Maker Order"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        print(f"SIMULATED: Placed Limit {side} for {quantity} {symbol} at RM{price}")
        return {"status": "simulated", "orderId": "sim_123", "price": price}

    endpoint = "/orderbook/sapi/orders/create"
    timestamp = str(int(time.time()))
    
    hata_side = "true" if side.upper() == "BUY" else "false"
    clean_symbol = symbol.replace("_", "").upper()
    base_coin = symbol.split("_")[0] if "_" in symbol else clean_symbol.replace("MYR", "")
    
    qty_scale = COIN_SCALES.get(base_coin, {}).get("qty", 4)
    price_scale = COIN_SCALES.get(base_coin, {}).get("price", 2)
    
    # Format according to exact scale
    fmt_price = f"{price:.{price_scale}f}"
    fmt_qty = f"{quantity:.{qty_scale}f}"
    
    params = {
        "is_buy": hata_side,
        "pair": clean_symbol,
        "price": fmt_price,
        "qty": fmt_qty,
        "timestamp": timestamp,
        "type": "limit"
    }
    
    signature = _generate_signature(params, HATA_API_SECRET, is_post=True)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.post(url, json=params, headers=headers, timeout=10)
        if response.status_code != 200:
            err_msg = response.text
            print(f"Error placing Limit {side} Order: {err_msg}")
            return {"status": "error", "message": err_msg}
            
        print(f"Order Success: Limit {side} {quantity} {symbol} at RM{price}")
        return response.json()
    except Exception as e:
        print(f"Error placing Limit {side} Order: {e}")
        return {"status": "error", "message": str(e)}

def cancel_order(symbol: str, order_id: str) -> dict:
    """Cancel an open order on Hata"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        print(f"SIMULATED: Cancelled Order {order_id}")
        return {"status": "simulated_cancelled"}
        
    endpoint = "/orderbook/sapi/orders/cancel"
    timestamp = str(int(time.time()))
    clean_symbol = symbol.replace("_", "").upper()
    
    params = {
        "order_id": str(order_id),
        "pair": clean_symbol,
        "timestamp": timestamp
    }
    
    signature = _generate_signature(params, HATA_API_SECRET, is_post=True)
    
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.post(url, json=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error cancelling order {order_id}: {response.text}")
            return {"status": "error", "message": response.text}
    except Exception as e:
        print(f"Error cancelling order {order_id}: {e}")
        return {"status": "error", "message": str(e)}

def get_trade_history(pair: str, limit: int = 50) -> dict:
    """Fetch trade history from Hata API for real P&L calculation"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        return {"status": "simulated", "data": []}
        
    endpoint = "/orderbook/sapi/trades"
    timestamp = str(int(time.time()))
    clean_pair = pair.replace("_", "").upper()
    
    params = {
        "limit": str(limit),
        "pair": clean_pair,
        "timestamp": timestamp
    }
    
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching trade history for {pair}: {response.text}")
            return {"status": "error", "message": response.text}
    except Exception as e:
        print(f"Error fetching trade history for {pair}: {e}")
        return {"status": "error", "message": str(e)}

def get_my_orders(pair: str, status: str = "active") -> dict:
    """Fetch open/active orders from Hata API"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        return {"status": "simulated", "data": []}
        
    endpoint = "/orderbook/sapi/orders"
    timestamp = str(int(time.time()))
    clean_pair = pair.replace("_", "").upper()
    
    params = {
        "pair": clean_pair,
        "status": status,
        "timestamp": timestamp
    }
    
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching orders for {pair}: {response.text}")
            return {"status": "error", "message": response.text}
    except Exception as e:
        print(f"Error fetching orders for {pair}: {e}")
        return {"status": "error", "message": str(e)}
