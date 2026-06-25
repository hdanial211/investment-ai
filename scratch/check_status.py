import urllib.request
import json
import os
import sqlite3

def check_bot_status():
    print("=" * 60)
    print("INVESTMENT AI - LIVE STATUS CHECK")
    print("=" * 60)
    
    # 1. Fetch API State
    try:
        url = "http://127.0.0.1:8000/api/state"
        req = urllib.request.Request(url, headers={'User-Agent': 'Auto-Healing Monitor'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[ERROR] Failed to query backend API: {e}")
        return

    # Print Global Info
    g = data.get("global", {})
    print(f"Global Balance: RM {g.get('balance_myr', 0):.4f}")
    print(f"Frozen Balance: RM {g.get('frozen_myr', 0):.4f}")
    print(f"USDT/MYR Rate : {g.get('usdt_myr_rate', 0):.4f}")
    print(f"Hata Health   : {g.get('hata_exchange_health', 'N/A')}")
    print("-" * 60)

    # Print Coins
    # Check if 'coins' is a key in data, or if it is at root
    coins_data = data.get("coins", {})
    if not coins_data:
        coins_data = {k: v for k, v in data.items() if k != "global"}
        
    for coin, info in coins_data.items():
        current_price = info.get("current_price", 0)
        is_auto = info.get("is_auto", False)
        total_pnl = info.get("total_pnl", 0)
        confidence = info.get("confidence", 0)
        layers = info.get("layers", [])
        
        status_str = "AUTO" if is_auto else "MANUAL"
        print(f"{coin:<4} | Price: {current_price:<10} | Auto: {status_str:<6} | PnL: RM {total_pnl:<8.4f} | AI Confidence: {confidence:.2f}%")
        
        if not layers:
            print("  [No Active Layers]")
        else:
            for idx, layer in enumerate(layers):
                lid = layer.get("id")
                entry = layer.get("entry_price")
                tp = layer.get("take_profit")
                qty = layer.get("quantity")
                status = layer.get("status")
                buy_id = layer.get("buy_order_id")
                sell_id = layer.get("sell_order_id")
                
                print(f"  -> Layer {lid}: {status:<12} | Qty: {qty:<10.6f} | Entry: {entry:<8} | TP: {tp:<8.4f}")
                if buy_id:
                    print(f"     Buy Order ID: {buy_id}")
                if sell_id:
                    print(f"     Sell Order ID: {sell_id}")
        print("-" * 60)

    # 2. Database check
    db_path = os.path.join("backend", "investment_ai.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Database Integrity: [OK] | Tables found: {', '.join(tables)}")
            
            # Print schema of trades
            if "trades" in tables:
                cursor.execute("PRAGMA table_info(trades)")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"Trades Table Columns: {', '.join(columns)}")
                
                # Fetch recent rows dynamically matching available columns
                cursor.execute("SELECT count(*) FROM trades")
                trade_count = cursor.fetchone()[0]
                print(f"Total Trades Logged in DB: {trade_count}")
                
                # Get the intersection of requested columns and existing ones
                col_list = []
                for c in ["id", "coin", "pair_name", "side", "price", "quantity", "qty", "status", "timestamp", "created_at"]:
                    if c in columns:
                        col_list.append(c)
                
                if col_list:
                    select_cols = ", ".join(col_list)
                    cursor.execute(f"SELECT {select_cols} FROM trades ORDER BY id DESC LIMIT 5")
                    recent = cursor.fetchall()
                    if recent:
                        print("Recent 5 Database Trades:")
                        for r in recent:
                            trade_details = " | ".join([f"{col_list[i]}: {r[i]}" for i in range(len(col_list))])
                            print(f"  {trade_details}")
            conn.close()
        except Exception as e:
            print(f"Database Check: [FAIL] | Error: {e}")
    else:
        print(f"Database Check: [FAIL] | File not found at {db_path}")
    print("=" * 60)

if __name__ == "__main__":
    check_bot_status()
