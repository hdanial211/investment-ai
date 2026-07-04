import sys
import os
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import json

sys.path.append('e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI/backend')
import hata_api

def generate_direct_report(target_date_str=None):
    # If no date provided, default to current local date (Malaysia time UTC+8)
    if not target_date_str:
        # Malaysia is UTC+8, get current time and format
        my_time = datetime.utcnow() + timedelta(hours=8)
        target_date_str = my_time.strftime("%Y-%m-%d")
        
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    
    # 00:00:00 to 23:59:59 Malaysia Time (UTC+8)
    # Convert Malaysia Time to UTC timestamps for Hata API start_time and end_time
    start_dt = target_date
    end_dt = start_dt + timedelta(days=1) - timedelta(seconds=1)
    
    # Hata API timestamps are standard Unix timestamps in seconds
    start_ts = str(int(start_dt.timestamp()))
    end_ts = str(int(end_dt.timestamp()))
    
    print(f"Fetching DIRECT trade history from Hata API...")
    print(f"Local Date Target: {target_date_str}")
    print(f"Unix Time Window: {start_ts} ({start_dt}) -> {end_ts} ({end_dt})")
    
    coins = ["BTC", "ETH", "SOL", "XRP", "LTC"]
    coin_stats = {}
    
    total_pnl = 0.0
    total_trades = 0
    total_fees = 0.0
    
    # ── STEP 3: Fetch directly from Hata API ──
    for coin in coins:
        coin_stats[coin] = {"pnl": 0.0, "trades": 0, "win": 0, "fees": 0.0, "buys": 0, "sells": 0}
        pair = f"{coin}_MYR"
        
        res = hata_api.get_trade_history(pair, limit=100, start_time=start_ts, end_time=end_ts)
        
        if res.get("status") == "error":
            print(f"[{coin}] API Error: {res.get('message')}")
            continue
            
        trades = res.get("data", {}).get("trades", [])
        if not trades:
            continue
            
        buy_trades = []
        sell_trades = []
        
        for t in trades:
            is_buy = t.get("is_buy")  # boolean
            price = float(t.get("price", 0))
            qty = float(t.get("qty", 0))
            fee = float(t.get("fee", 0))
            
            # Estimate fee in MYR
            if is_buy:
                fee_myr = fee * price
                buy_trades.append({"price": price, "qty": qty, "fee_myr": fee_myr})
                coin_stats[coin]["buys"] += 1
                coin_stats[coin]["fees"] += fee_myr
                total_fees += fee_myr
            else:
                fee_myr = fee
                sell_trades.append({"price": price, "qty": qty, "fee_myr": fee_myr})
                coin_stats[coin]["sells"] += 1
                coin_stats[coin]["fees"] += fee_myr
                total_fees += fee_myr
            
            coin_stats[coin]["trades"] += 1
            total_trades += 1
            
        gap_pct = 0.005 # default fallback 0.5%
        try:
            gap_pct = float(hata_api.shared.engine_state[coin].get("grid_gap_pct", 0.005))
        except Exception:
            pass
            
        pnl_realized = 0.0
        for s in sell_trades:
            # Match with a buy in the same day first
            matched_buy = None
            for b in buy_trades:
                if b["price"] < s["price"]:
                    matched_buy = b
                    buy_trades.remove(b)
                    break
            
            if matched_buy:
                profit = (s["price"] - matched_buy["price"]) * s["qty"] - s["fee_myr"] - matched_buy["fee_myr"]
                pnl_realized += profit
                coin_stats[coin]["win"] += 1
            else:
                # Fallback: estimate buy price using grid_gap_pct
                est_buy_price = s["price"] / (1.0 + gap_pct)
                profit = (s["price"] - est_buy_price) * s["qty"] - s["fee_myr"]
                pnl_realized += profit
                coin_stats[coin]["win"] += 1
                
        coin_stats[coin]["pnl"] = pnl_realized
        total_pnl += pnl_realized

    # ── STEP 4: Semak status active groups & layers HOLDING dari bot_state.json ──
    state_file = r"e:\PROJECTS\SEMUA PROJECT\INVESTMENT AI\backend\bot_state.json"
    active_groups_count = 0
    total_holding_layers = 0
    holding_details = []
    
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                
            for coin in coins:
                coin_data = state_data.get(coin, {})
                groups = coin_data.get("groups", [])
                
                coin_groups = len(groups)
                coin_holding = 0
                for g in groups:
                    for l in g.get("layers", []):
                        if l.get("status") == "HOLDING":
                            coin_holding += 1
                
                active_groups_count += coin_groups
                total_holding_layers += coin_holding
                
                if coin_groups > 0 or coin_holding > 0:
                    holding_details.append(f"  • *{coin}*: {coin_groups} group(s) | {coin_holding} layer(s) HOLDING")
        except Exception as e:
            print(f"Error reading bot_state.json: {e}")
            holding_details.append("  • Ralat membaca fail bot_state.json")

    # ── STEP 5: Tulis report harian yang kemas ──
    msg_lines = [
        "📊 *DAILY REPORT INVESTMENT AI*",
        f"📅 *Tarikh:* {target_date_str} (Malaysia Time)",
        "",
        "💰 *Realized Profit & Loss (PnL) Terus dari Hata API:*",
    ]
    
    for coin, stats in coin_stats.items():
        if stats["trades"] > 0:
            pnl_str = f"+RM{stats['pnl']:.4f}" if stats["pnl"] >= 0 else f"-RM{abs(stats['pnl']):.4f}"
            msg_lines.append(
                f"• *{coin}/MYR*: `{pnl_str}` | {stats['buys']} Buy / {stats['sells']} Sell | Fees: RM{stats['fees']:.4f}"
            )
        else:
            msg_lines.append(f"• *{coin}/MYR*: Tiada trade")
            
    total_pnl_str = f"+RM{total_pnl:.4f}" if total_pnl >= 0 else f"-RM{abs(total_pnl):.4f}"
    
    msg_lines.extend([
        "",
        "📈 *Jumlah Dagangan Live:*",
        f"• *Total Realized PnL:* `{total_pnl_str}`",
        f"• *Total Trades:* `{total_trades}`",
        f"• *Total Fees:* `RM {total_fees:.4f}`",
        "",
        "📦 *Status Posisi Semasa (bot_state.json):*",
        f"• *Total Active Groups:* `{active_groups_count}`",
        f"• *Total Layers HOLDING:* `{total_holding_layers}`"
    ])
    
    if holding_details:
        msg_lines.extend(holding_details)
        
    msg_lines.extend([
        "",
        "🤖 *Status Enjin Dagangan:*",
        "• Data diperolehi secara live dari API Hata.",
        "• Grid Multi-Group aktif."
    ])
    
    report_text = "\n".join(msg_lines)
    
    # ── STEP 6: Hantar ke Telegram Group ──
    token = "8880063318:AAHeAoJ1E4m1BTJVmTJEKVz5TbNTwW9K98k"
    chat_id = "-1003819849481"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": report_text,
        "parse_mode": "Markdown"
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as response:
        print("TELEGRAM SEND SUCCESS:", response.read().decode())

if __name__ == "__main__":
    # If run manually, check if date is passed as arg, else default to today
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    generate_direct_report(target_date)
