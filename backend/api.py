from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
import threading
import time
from pydantic import BaseModel
from dotenv import load_dotenv
from shared import engine_state
import hata_api

load_dotenv()

app = FastAPI(title="Holy Grail Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AutoToggle(BaseModel):
    is_auto: bool

class AmountSetting(BaseModel):
    amount: float

class BacktestParams(BaseModel):
    initial_cash: float = 100000.0
    trade_size_fiat: float = 4000.0
    max_layers: int = 6
    drop_threshold: float = 0.05
    take_profit_pct: float = 0.10
    trailing_activation_pct: float = 0.03
    trailing_gap_pct: float = 0.01

@app.get("/api/state")
def get_state():
    return engine_state

@app.post("/api/toggle-auto")
def toggle_auto(toggle: AutoToggle):
    engine_state["is_auto"] = toggle.is_auto
    return {"status": "success", "is_auto": engine_state["is_auto"]}

@app.post("/api/set-amount")
def set_amount(setting: AmountSetting):
    if setting.amount >= 10.0: # Minimum RM10
        engine_state["trade_amount_myr"] = setting.amount
    return {"status": "success", "trade_amount_myr": engine_state["trade_amount_myr"]}

@app.post("/api/manual-buy")
def manual_buy():
    # Logic to trigger Hata API Buy
    # For now, we simulate layering
    price = engine_state["current_price"]
    if price <= 0:
        raise HTTPException(status_code=400, detail="Price not available")
    
    amount = engine_state["trade_amount_myr"]
    layer = {
        "id": len(engine_state["layers"]) + 1,
        "entry_price": price,
        "amount_myr": amount,
        "take_profit": price * 1.006,
        "status": "OPEN"
    }
    engine_state["layers"].append(layer)
    engine_state["balance_myr"] -= amount
    return {"status": "success", "layer": layer}

@app.post("/api/panic-sell")
def panic_sell():
    engine_state["layers"] = []
    # Simulate closing all at market
    return {"status": "success", "message": "All positions closed"}

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json

@app.websocket("/api/backtest-stream")
async def websocket_backtest(websocket: WebSocket):
    await websocket.accept()
    try:
        config_msg = await websocket.receive_text()
        config = json.loads(config_msg)
        params = BacktestParams(**config)
        
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        
        def progress_callback(msg):
            print(f"Callback received: {msg.get('type')}")
            asyncio.run_coroutine_threadsafe(queue.put(msg), loop)
            
        def run_backtest_thread():
            try:
                base_dir = os.path.dirname(os.path.dirname(__file__))
                data_path = os.path.join(base_dir, 'data', 'ETH_USDT_1m.csv')
                model_path = os.path.join(base_dir, 'models', 'xgboost_scalping_ETH_1y.pkl')
                
                if not os.path.exists(data_path) or not os.path.exists(model_path):
                    progress_callback({"type": "error", "message": "Data or model not found"})
                    return

                drop_threshold_val = -abs(params.drop_threshold)
                from backtest.dca_engine import run_dca_backtest
                metrics = run_dca_backtest(
                    csv_path=data_path, 
                    model_path=model_path,
                    initial_cash=params.initial_cash,
                    trade_size_fiat=params.trade_size_fiat,
                    commission=0.000, 
                    drop_threshold=drop_threshold_val,
                    take_profit_pct=params.take_profit_pct,
                    max_layers_per_signal=params.max_layers,
                    trailing_activation_pct=params.trailing_activation_pct,
                    trailing_gap_pct=params.trailing_gap_pct,
                    progress_callback=progress_callback
                )
                progress_callback({"type": "complete", "metrics": metrics})
            except Exception as e:
                progress_callback({"type": "error", "message": str(e)})

        t = threading.Thread(target=run_backtest_thread)
        t.start()
        
        while True:
            msg = await queue.get()
            print(f"Sending WS msg: {msg.get('type')}")
            await websocket.send_text(json.dumps(msg))
            if msg.get("type") in ["complete", "error"]:
                break
    except WebSocketDisconnect:
        print("Client disconnected from backtest stream")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"WebSocket error: {e}")

def update_balance_loop():
    while True:
        try:
            myr_balance = hata_api.get_myr_balance()
            if myr_balance is not None:
                engine_state["balance_myr"] = myr_balance
        except Exception as e:
            print(f"Failed to update balance loop: {e}")
        time.sleep(15) # Fetch every 15 seconds

@app.on_event("startup")
def start_server():
    # Start live engine in background
    import live_engine
    t1 = threading.Thread(target=live_engine.run, daemon=True)
    t1.start()
    
    # Start balance fetch loop
    t2 = threading.Thread(target=update_balance_loop, daemon=True)
    t2.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
