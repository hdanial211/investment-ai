from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
import threading
import time
from pydantic import BaseModel
from dotenv import load_dotenv
from shared import engine_state, global_state
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
    coin: str
    amount: float

class BacktestParams(BaseModel):
    coin: str = "ETH"
    initial_cash: float = 100000.0
    trade_size_fiat: float = 4000.0
    max_layers: int = 6
    drop_threshold: float = 0.05
    take_profit_pct: float = 0.10
    trailing_activation_pct: float = 0.03
    trailing_gap_pct: float = 0.01
    enable_dca: bool = True
    ai_type: str = "xgboost"

@app.get("/api/state")
def get_state():
    return {
        "global": global_state,
        "coins": engine_state
    }

@app.post("/api/toggle-auto")
def toggle_auto(toggle: AutoToggle):
    global_state["is_auto"] = toggle.is_auto
    return {"status": "success", "is_auto": global_state["is_auto"]}

@app.post("/api/set-amount")
def set_amount(setting: AmountSetting):
    if setting.amount >= 10.0 and setting.coin in engine_state:
        engine_state[setting.coin]["trade_amount_myr"] = setting.amount
    return {"status": "success", "trade_amount_myr": engine_state[setting.coin]["trade_amount_myr"]}

class ManualAction(BaseModel):
    coin: str

@app.post("/api/manual-buy")
def manual_buy(action: ManualAction):
    coin = action.coin
    if coin not in engine_state:
        raise HTTPException(status_code=400, detail="Invalid coin")
        
    price = engine_state[coin]["current_price"]
    if price <= 0:
        raise HTTPException(status_code=400, detail="Price not available")
    
    amount = engine_state[coin]["trade_amount_myr"]
    layer = {
        "id": len(engine_state[coin]["layers"]) + 1,
        "entry_price": price,
        "amount_myr": amount,
        "take_profit": price * 1.006,
        "status": "OPEN"
    }
    engine_state[coin]["layers"].append(layer)
    global_state["balance_myr"] -= amount
    return {"status": "success", "layer": layer}

@app.post("/api/panic-sell")
def panic_sell(action: ManualAction):
    coin = action.coin
    if coin in engine_state:
        engine_state[coin]["layers"] = []
    return {"status": "success", "message": f"All positions closed for {coin}"}

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
                coin_symbol = params.coin.upper()
                data_path = os.path.join(base_dir, 'data', f'{coin_symbol}_USDT_1m.csv')
                
                # Choose model based on ai_type
                if params.ai_type == "rl_lstm":
                    model_path = os.path.join(base_dir, 'models', f'ppo_lstm_{coin_symbol}.zip')
                else:
                    model_path = os.path.join(base_dir, 'models', f'xgboost_scalping_{coin_symbol}_1y.pkl')
                
                logger.info(f"Using Model: {model_path} ({params.ai_type})")
                
                if not os.path.exists(data_path) or not os.path.exists(model_path):
                    progress_callback({"type": "error", "message": f"Data or model for {coin_symbol} not found"})
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
                    progress_callback=progress_callback,
                    enable_dca=params.enable_dca,
                    ai_type=params.ai_type
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
                global_state["balance_myr"] = myr_balance
                
            # Dynamically calculate exchange rate (Hata ETH MYR / Binance ETH USDT)
            hata_eth = hata_api.get_ticker("ETH_MYR")
            binance_eth = engine_state.get("ETH", {}).get("current_price", 0.0)
            if hata_eth > 0 and binance_eth > 0:
                global_state["usdt_myr_rate"] = hata_eth / binance_eth
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
