import os
from dotenv import load_dotenv
from exchange.hata_client import HataClient

# Load credentials from .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def main():
    client = HataClient()
    print("Testing Hata API...")
    
    try:
        # Test 1: Get Markets (Public endpoint usually)
        print("\n--- Fetching Markets ---")
        markets = client.get_markets()
        print(f"Successfully fetched {len(markets.get('symbols', []))} markets.")
        
        # Test 2: Get Balance (Private endpoint)
        print("\n--- Fetching Balances ---")
        # Some exchanges use different endpoints, so we wrap in try-except
        balance = client.get_balance()
        print("Balance Response:", balance)
        
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
