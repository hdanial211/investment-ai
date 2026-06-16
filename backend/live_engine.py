import asyncio
import websockets
import json
import logging
import pandas as pd
import numpy as np
import joblib
import os
import sys

# Import shared state from api
import api

# Features calculation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from backend.features.indicators import calculate_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
SYMBOL = "ethusdt"
WS_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_1m"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "xgboost_scalping_ETH_1y.pkl")

# Load AI
model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    logger.info("AI Model loaded for Live Engine.")
else:
    logger.error("AI Model not found! Live Engine cannot run AI.")

# Rolling data
klines = []
MAX_KLINES = 150 # Enough for EMA_21, VWAP, etc.

async def process_kline(kline):
    global klines
    
    # Update current price in dashboard
    api.engine_state["current_price"] = float(kline['c'])
    
    # If candle is closed, append to history and predict
    if kline['x']:
        klines.append({
            'timestamp': pd.to_datetime(kline['t'], unit='ms'),
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c']),
            'volume': float(kline['v'])
        })
        
        if len(klines) > MAX_KLINES:
            klines.pop(0)
            
        if len(klines) >= 50 and model is not None:
            df = pd.DataFrame(klines)
            df_feat = calculate_features(df)
            
            # Extract latest row
            latest = df_feat.iloc[-1:]
            
            # Predict
            feature_cols = [c for c in latest.columns if c not in ['timestamp', 'target', 'ai_signal', 'future_close']]
            # Ensure correct order
            X = latest[['open', 'high', 'low', 'close', 'volume', 'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 'Volume_ROC'] + 
                       [c for c in feature_cols if c.startswith('BB')] + 
                       [c for c in feature_cols if c.startswith('MACD')] + 
                       [c for c in feature_cols if c.startswith('STOCH')] + 
                       [c for c in feature_cols if c.startswith('ATR')] + 
                       (['VWAP_D'] if 'VWAP_D' in feature_cols else (['VWAP'] if 'VWAP' in feature_cols else []))]
            
            probs = model.predict_proba(X)
            golden_prob = float(probs[0, 1])
            
            api.engine_state["confidence"] = golden_prob * 100
            
            if golden_prob > 0.60:
                logger.info(f"GOLDEN ENTRY DETECTED! Confidence: {golden_prob*100:.2f}%")
                api.engine_state["last_signal"] = 1
                
                # If Auto mode is ON, execute trade
                if api.engine_state["is_auto"]:
                    logger.info("Auto Mode ON: Executing Buy!")
                    api.manual_buy() # Calls the layering system
            else:
                api.engine_state["last_signal"] = 0
                
        # Handle Layering Logic (Check Take Profits)
        layers = api.engine_state["layers"]
        active_layers = []
        for l in layers:
            if api.engine_state["current_price"] >= l["take_profit"]:
                logger.info(f"TAKE PROFIT HIT for layer {l['id']}!")
                api.engine_state["balance_myr"] += l["amount_myr"] * 1.006 # Add profit back
                api.engine_state["total_pnl"] += l["amount_myr"] * 0.006
            else:
                active_layers.append(l)
        api.engine_state["layers"] = active_layers


async def start_ws():
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                logger.info("Connected to Binance WebSocket!")
                while True:
                    data = await ws.recv()
                    payload = json.loads(data)
                    kline = payload['k']
                    await process_kline(kline)
        except Exception as e:
            logger.error(f"WebSocket Error: {e}")
            await asyncio.sleep(5)

def run():
    asyncio.run(start_ws())

if __name__ == "__main__":
    run()
