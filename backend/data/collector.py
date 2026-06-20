import sqlite3
import json
import logging
from datetime import datetime
from exchange.hata_ws import HataWebSocket
import asyncio

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, db_path='investment_ai.db'):
        self.db_path = db_path
        self.setup_db()

    def setup_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hata_live_klines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                timestamp INTEGER,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def on_ws_message(self, message):
        """Handle incoming websocket messages from Hata"""
        # Note: the exact keys depend on Hata WS documentation. 
        # This is a generic handler based on typical crypto exchange payloads.
        try:
            if "method" in message and message["method"] == "update":
                data = message.get("data", {})
                # E.g. {"symbol": "BTC_MYR", "kline": {"t": 1234567, "o": "100", "h": "105", "l": "95", "c": "102", "v": "10"}}
                if "kline" in data:
                    k = data["kline"]
                    symbol = data.get("symbol", "UNKNOWN")
                    self.save_kline(symbol, k.get("t"), float(k.get("o")), float(k.get("h")), float(k.get("l")), float(k.get("c")), float(k.get("v")))
        except Exception as e:
            logger.error(f"Error parsing message: {e}")

    def save_kline(self, symbol, timestamp, open_p, high_p, low_p, close_p, volume):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO hata_live_klines (symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, timestamp, open_p, high_p, low_p, close_p, volume))
        conn.commit()
        conn.close()
        logger.info(f"Saved kline: {symbol} @ {timestamp} - C:{close_p}")

    async def start(self):
        ws = HataWebSocket(on_message_callback=self.on_ws_message)
        await ws.connect()

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import log_config
    collector = DataCollector()
    try:
        asyncio.run(collector.start())
    except KeyboardInterrupt:
        logger.info("Collector stopped.")
