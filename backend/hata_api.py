import os
import time
import hmac
import hashlib
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

HATA_API_KEY = os.getenv("HATA_API_KEY", "")
HATA_API_SECRET = os.getenv("HATA_API_SECRET", "")
BASE_URL = "https://my-api.hata.io" # For Malaysia accounts

def _generate_signature(params: dict, secret: str) -> str:
    # Sort parameters alphabetically by key
    sorted_params = dict(sorted(params.items()))
    # Construct query string
    query_string = urllib.parse.urlencode(sorted_params)
    # Generate HMAC SHA256 signature
    signature = hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def get_myr_balance() -> float:
    """Fetch the real MYR balance from Hata API"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        print("Warning: HATA_API_KEY or HATA_API_SECRET not found. Using simulated balance.")
        return 10000.00
        
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
        
        # Parse balance from response (assuming structure has balance or available_balance)
        # We might need to inspect the response structure if it's different.
        # Usually it returns a list of balances or a single object.
        print("Hata API Balance Response:", data)
        
        if isinstance(data, list):
            for item in data:
                if item.get("symbol") == "MYR":
                    return float(item.get("available", 0.0))
        elif isinstance(data, dict):
            # If it returns a dict with 'available'
            if "available" in data:
                return float(data["available"])
            elif "data" in data and isinstance(data["data"], list):
                 for item in data["data"]:
                    if item.get("symbol") == "MYR":
                        return float(item.get("available", 0.0))
                        
        return 0.0 # Default if parsing fails
        
    except Exception as e:
        print(f"Error fetching Hata API balance: {e}")
        # Return fallback value or None to let caller handle
        return 0.0

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

def place_limit_order(symbol: str, side: str, price: float, quantity: float) -> dict:
    """Place a Limit Maker Order"""
    if not HATA_API_KEY or not HATA_API_SECRET:
        print(f"SIMULATED: Placed Limit {side} for {quantity} {symbol} at RM{price}")
        return {"status": "simulated", "orderId": "sim_123", "price": price}

    endpoint = "/orderbook/sapi/order"
    timestamp = str(int(time.time()))
    
    params = {
        "timestamp": timestamp,
        "symbol": symbol,
        "side": side.upper(), # BUY or SELL
        "type": "LIMIT",
        "timeInForce": "GTC",
        "price": str(price),
        "quantity": str(quantity)
    }
    
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.post(url, data=params, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Order Success: Limit {side} {quantity} {symbol} at RM{price}")
        return response.json()
    except Exception as e:
        print(f"Error placing Limit {side} Order: {e}")
        return {"status": "error", "message": str(e)}

def cancel_order(symbol: str, order_id: str) -> dict:
    """Cancel an open order"""
    if not HATA_API_KEY:
        print(f"SIMULATED: Cancelled Order {order_id}")
        return {"status": "simulated_cancelled"}
        
    endpoint = "/orderbook/sapi/order"
    timestamp = str(int(time.time()))
    params = {
        "timestamp": timestamp,
        "symbol": symbol,
        "orderId": order_id
    }
    signature = _generate_signature(params, HATA_API_SECRET)
    headers = {
        "X-API-KEY": HATA_API_KEY,
        "Signature": signature
    }
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.delete(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error cancelling order {order_id}: {e}")
        return {"status": "error"}
