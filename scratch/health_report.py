import urllib.request
import json
import sys

def main():
    try:
        url = "http://127.0.0.1:8000/api/state"
        req = urllib.request.Request(url, headers={'User-Agent': 'Health-Check-Agent'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            
        print("==================================================")
        print("         INVESTMENT AI SYSTEM STATUS REPORT       ")
        print("==================================================")
        
        global_state = res.get("global", {})
        guardian = global_state.get("guardian_status", {})
        print(f"System Status: {guardian.get('status', 'N/A').upper()}")
        print(f"System Analysis: {guardian.get('analysis', 'N/A')}")
        print(f"System Recommendation: {guardian.get('recommendation', 'N/A')}")
        print(f"USDT/MYR Rate: {global_state.get('usdt_myr_rate', 0.0):.4f}")
        print(f"Hata Account Status:")
        print(f"  - MYR Balance: RM {global_state.get('balance_myr', 0.0):.2f}")
        print(f"  - MYR Frozen: RM {global_state.get('frozen_myr', 0.0):.2f}")
        
        coins = res.get("coins", {})
        total_pnl = sum(info.get("total_pnl", 0.0) for info in coins.values())
        print(f"Total Portfolio PnL: RM {total_pnl:.4f}")
        print("--------------------------------------------------")
        print("COIN STATUS:")
        
        coins = res.get("coins", {})
        for coin, info in coins.items():
            is_auto = info.get("is_auto", False)
            price = info.get("current_price", 0.0)
            signal = info.get("last_signal", 0)
            confidence = info.get("confidence", 0.0)
            layers = info.get("layers", [])
            pnl = info.get("total_pnl", 0.0)
            risk = info.get("risk_level", 0)
            trade_amount = info.get("trade_amount_myr", 0.0)
            consolidated_id = info.get("consolidated_sell_order_id", None)
            
            sig_str = "BUY" if signal == 1 else "SELL/NONE"
            status_str = "AUTO" if is_auto else "MANUAL"
            
            print(f"\n{coin} | Status: {status_str} | Risk Lvl: {risk} | Trade Amt: RM {trade_amount:.2f}")
            print(f"  Current Price: MYR {price}")
            print(f"  Last AI Signal: {sig_str} (Conf: {confidence:.2f}%)")
            print(f"  Total PnL: RM {pnl:.4f}")
            print(f"  Active Layers: {len(layers)}")
            if consolidated_id:
                print(f"  Consolidated Sell Order ID: {consolidated_id}")
            
            for layer in layers:
                lid = layer.get("id")
                entry = layer.get("entry_price")
                qty = layer.get("quantity")
                lstatus = layer.get("status")
                sell_oid = layer.get("sell_order_id")
                print(f"    - Layer {lid}: Price {entry} | Qty {qty} | Status: {lstatus} (Sell OID: {sell_oid})")
                
        print("==================================================")
        
    except Exception as e:
        print(f"Error fetching API state: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
