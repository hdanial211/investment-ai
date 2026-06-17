import asyncio
import websockets
import json
import logging
import pandas as pd
import joblib
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.features.indicators import calculate_features
import backend.hata_api as hata

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("eth_bot")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

class ETHLiveBot:
    def __init__(self):
        with open(CONFIG_PATH, 'r') as f:
            self.config = json.load(f)
            
        self.coin = self.config["coin"]
        self.symbol = f"{self.coin.lower()}usdt"
        self.hata_symbol = f"{self.coin}_MYR"
        self.model = joblib.load(os.path.join(os.path.dirname(__file__), self.config["model_path"]))
        
        self.klines = []
        self.state = "WAITING" # WAITING, HOLDING, PROFIT_HUNTING
        
        self.position = {
            "amount_coin": 0.0,
            "total_invested": 0.0,
            "average_price": 0.0,
            "layer_count": 0
        }
        
        self.highest_price_seen = 0.0
        self.pending_layer_order_id = None
        
        logger.info(f"Bot Initialized for {self.coin} - Config: {self.config}")

    def update_klines(self, kline):
        if kline['x']: # Candle closed
            self.klines.append({
                'timestamp': pd.to_datetime(kline['t'], unit='ms'),
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v'])
            })
            if len(self.klines) > 150:
                self.klines.pop(0)
            return True
        return False

    def predict_signal(self):
        if len(self.klines) < 50:
            return 0.0
        
        df = pd.DataFrame(self.klines)
        df_feat = calculate_features(df)
        latest = df_feat.iloc[-1:]
        
        feature_cols = [c for c in latest.columns if c not in ['timestamp', 'target', 'ai_signal', 'future_close']]
        X = latest[['open', 'high', 'low', 'close', 'volume', 'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 'Volume_ROC'] + 
                   [c for c in feature_cols if c.startswith('BB')] + 
                   [c for c in feature_cols if c.startswith('MACD')] + 
                   [c for c in feature_cols if c.startswith('STOCH')] + 
                   [c for c in feature_cols if c.startswith('ATR')] + 
                   (['VWAP_D'] if 'VWAP_D' in feature_cols else (['VWAP'] if 'VWAP' in feature_cols else []))]
        
        probs = self.model.predict_proba(X)
        return float(probs[0, 1])

    async def execute_trade(self, side, price, amount_fiat):
        quantity = amount_fiat / price
        quantity = round(quantity, 5) # Respect exchange precision
        
        logger.info(f"EXECUTING {side} ORDER: RM {amount_fiat} at {price}")
        res = hata.place_limit_order(self.hata_symbol, side, price, quantity)
        return res, quantity

    async def run(self):
        ws_url = f"wss://stream.binance.com:9443/stream?streams={self.symbol}@kline_1m"
        
        while True:
            try:
                async with websockets.connect(ws_url) as ws:
                    logger.info(f"Connected to Binance WS for {self.symbol}")
                    while True:
                        data = await ws.recv()
                        payload = json.loads(data)
                        kline_data = payload['data']['k']
                        current_price = float(kline_data['c'])
                        
                        candle_closed = self.update_klines(kline_data)
                        
                        # --- STATE MACHINE ---
                        
                        if self.state == "WAITING":
                            if candle_closed:
                                prob = self.predict_signal()
                                if prob >= self.config["min_confidence"]:
                                    logger.info(f"GOLDEN ENTRY SIGNAL! Conf: {prob*100:.2f}%")
                                    # Execute Buy
                                    hata_price = hata.get_ticker(self.hata_symbol)
                                    if hata_price > 0:
                                        res, qty = await self.execute_trade("BUY", hata_price, self.config["trade_size_fiat"])
                                        self.position["average_price"] = hata_price
                                        self.position["amount_coin"] += qty
                                        self.position["total_invested"] += self.config["trade_size_fiat"]
                                        self.position["layer_count"] = 1
                                        self.state = "HOLDING"
                                        
                        elif self.state == "HOLDING":
                            avg_price = self.position["average_price"]
                            profit_pct = (current_price - avg_price) / avg_price
                            
                            # Check Trailing Stop Activation
                            if profit_pct >= self.config["trailing_activation_pct"]:
                                logger.info(f"PROFIT HIT {profit_pct*100:.2f}%. ACTIVATING TRAILING STOP!")
                                self.state = "PROFIT_HUNTING"
                                self.highest_price_seen = current_price
                                continue
                                
                            # Check DCA Layering
                            drop_pct = (avg_price - current_price) / avg_price
                            if drop_pct >= self.config["drop_threshold_pct"] and self.position["layer_count"] < self.config["max_layers"]:
                                logger.info(f"PRICE DROPPED {drop_pct*100:.2f}%. EXECUTING DCA LAYER {self.position['layer_count'] + 1}!")
                                hata_price = hata.get_ticker(self.hata_symbol)
                                if hata_price > 0:
                                    res, qty = await self.execute_trade("BUY", hata_price, self.config["trade_size_fiat"])
                                    
                                    # Recalculate Average
                                    new_total = self.position["total_invested"] + self.config["trade_size_fiat"]
                                    new_amount = self.position["amount_coin"] + qty
                                    self.position["average_price"] = new_total / new_amount
                                    self.position["total_invested"] = new_total
                                    self.position["amount_coin"] = new_amount
                                    self.position["layer_count"] += 1
                                    
                        elif self.state == "PROFIT_HUNTING":
                            # Update Highest Price
                            if current_price > self.highest_price_seen:
                                self.highest_price_seen = current_price
                                
                            # Calculate Stop Trigger
                            stop_trigger = self.highest_price_seen * (1.0 - self.config["trailing_gap_pct"])
                            
                            if current_price <= stop_trigger:
                                logger.info(f"TRAILING STOP TRIGGERED! Selling {self.position['amount_coin']} ETH")
                                hata_price = hata.get_ticker(self.hata_symbol)
                                if hata_price > 0:
                                    res, qty = await self.execute_trade("SELL", hata_price, hata_price * self.position["amount_coin"])
                                    logger.info(f"TRADE CLOSED. PNL: +RM {(hata_price * self.position['amount_coin']) - self.position['total_invested']:.2f}")
                                    
                                    # Reset State
                                    self.position = {"amount_coin": 0.0, "total_invested": 0.0, "average_price": 0.0, "layer_count": 0}
                                    self.highest_price_seen = 0.0
                                    self.state = "WAITING"

            except Exception as e:
                logger.error(f"WebSocket/Bot Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    bot = ETHLiveBot()
    asyncio.run(bot.run())
