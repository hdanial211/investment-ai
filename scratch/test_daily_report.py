import sys
import os
from datetime import datetime, timedelta
import sqlite3
import urllib.request
import urllib.parse
import json

DB_FILE = r"e:\PROJECTS\SEMUA PROJECT\INVESTMENT AI\backend\investment_ai.db"

def generate_and_send_report(target_date_str):
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    
    # UTC Window calculation (Malaysia time UTC+8)
    start_utc = target_date - timedelta(hours=8)
    end_utc = start_utc + timedelta(days=1)
    
    start_utc_str = start_utc.strftime("%Y-%m-%d %H:%M:%S")
    end_utc_str = end_utc.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Connecting to database: {DB_FILE}")
    print(f"Local Date: {target_date_str}")
    print(f"UTC query window: {start_utc_str} -> {end_utc_str}")
    
    if not os.path.exists(DB_FILE):
        print("ERROR: Database file does not exist!")
        return

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    try:
        # Fetch completed trades (WIN/LOSS) in the target local day
        query = """
            SELECT coin_id, actual_outcome, pnl_myr, fee_total_myr, entry_price, exit_price, timestamp
            FROM ml_training_log
            WHERE actual_outcome IN ('WIN', 'LOSS')
              AND timestamp >= ?
              AND timestamp < ?
        """
        cur.execute(query, (start_utc_str, end_utc_str))
        rows = cur.fetchall()
        
        # Aggregate stats
        coin_stats = {
            "BTC": {"pnl": 0.0, "trades": 0, "win": 0, "fees": 0.0},
            "ETH": {"pnl": 0.0, "trades": 0, "win": 0, "fees": 0.0},
            "SOL": {"pnl": 0.0, "trades": 0, "win": 0, "fees": 0.0},
            "XRP": {"pnl": 0.0, "trades": 0, "win": 0, "fees": 0.0},
            "LTC": {"pnl": 0.0, "trades": 0, "win": 0, "fees": 0.0}
        }
        
        total_pnl = 0.0
        total_trades = 0
        total_fees = 0.0
        
        for r in rows:
            coin = r[0]
            outcome = r[1]
            pnl = float(r[2] or 0.0)
            fee = float(r[3] or 0.0)
            
            if coin in coin_stats:
                coin_stats[coin]["pnl"] += pnl
                coin_stats[coin]["fees"] += fee
                coin_stats[coin]["trades"] += 1
                if outcome == "WIN":
                    coin_stats[coin]["win"] += 1
                
                total_pnl += pnl
                total_fees += fee
                total_trades += 1
        
        # Build Markdown Message
        msg_lines = [
            "📊 *DAILY REPORT INVESTMENT AI*",
            f"📅 *Tarikh:* {target_date_str} (Malaysia Time)",
            "",
            "💰 *Realized Profit & Loss (PnL) dari API Hata:*",
        ]
        
        any_trades = False
        for coin, stats in coin_stats.items():
            if stats["trades"] > 0:
                any_trades = True
                pnl_str = f"+RM{stats['pnl']:.4f}" if stats["pnl"] >= 0 else f"-RM{abs(stats['pnl']):.4f}"
                win_rate = (stats["win"] / stats["trades"]) * 100
                msg_lines.append(
                    f"• *{coin}/MYR*: `{pnl_str}` | {stats['trades']} trade(s) | WR: {win_rate:.0f}% (Fees: RM{stats['fees']:.4f})"
                )
            else:
                msg_lines.append(f"• *{coin}/MYR*: Tiada trade")
                
        total_pnl_str = f"+RM{total_pnl:.4f}" if total_pnl >= 0 else f"-RM{abs(total_pnl):.4f}"
        
        msg_lines.extend([
            "",
            "📈 *Jumlah Keseluruhan:*",
            f"• *Total Realized PnL:* `{total_pnl_str}`",
            f"• *Total Trades:* `{total_trades}`",
            f"• *Total Fees:* `RM {total_fees:.4f}`",
            "",
            "🤖 *Status Enjin Dagangan:*",
            "• Sistem berjalan secara Autonomi.",
            "• Grid Multi-Group aktif."
        ])
        
        if not any_trades:
            # Let's double check total records in whole DB
            cur.execute("SELECT COUNT(*) FROM ml_training_log WHERE actual_outcome IN ('WIN', 'LOSS')")
            total_db_trades = cur.fetchone()[0]
            print(f"Total WIN/LOSS trades in whole DB: {total_db_trades}")
            
            # Let's print most recent trade timestamps to check
            cur.execute("SELECT timestamp, coin_id, pnl_myr, actual_outcome FROM ml_training_log WHERE actual_outcome IN ('WIN', 'LOSS') ORDER BY timestamp DESC LIMIT 5")
            recent_trades = cur.fetchall()
            print("Most recent trades in DB:")
            for rt in recent_trades:
                print(f"  {rt[0]} | {rt[1]} | PnL={rt[2]} | {rt[3]}")
        
        report_text = "\n".join(msg_lines)
        
        # Send to Telegram
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
            
    finally:
        conn.close()

if __name__ == "__main__":
    generate_and_send_report("2026-07-01")
