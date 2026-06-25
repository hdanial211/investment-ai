import log_config
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
import os
import uvicorn
import threading
import time
from pydantic import BaseModel
from dotenv import load_dotenv
from shared import engine_state, global_state, save_state
import shared
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
    coin: str
    is_auto: bool

class AmountSetting(BaseModel):
    coin: str
    amount: float

class TPSetting(BaseModel):
    coin: str
    tp_pct: float  # e.g. 0.005 = 0.5%

class RiskLevelSetting(BaseModel):
    coin: str
    risk_level: int

class ManualAction(BaseModel):
    coin: str

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
    if toggle.coin in engine_state:
        engine_state[toggle.coin]["is_auto"] = toggle.is_auto
        shared.save_state()
    return {"status": "success", "is_auto": engine_state[toggle.coin]["is_auto"]}

@app.post("/api/set-risk-level")
def set_risk_level(setting: RiskLevelSetting):
    if setting.risk_level in [1, 2, 3] and setting.coin in engine_state:
        engine_state[setting.coin]["risk_level"] = setting.risk_level
        shared.save_state()
    return {"status": "success", "risk_level": engine_state[setting.coin]["risk_level"]}

@app.post("/api/set-amount")
def set_amount(setting: AmountSetting):
    if setting.amount >= 10.0 and setting.coin in engine_state:
        engine_state[setting.coin]["trade_amount_myr"] = setting.amount
        shared.save_state()
    return {"status": "success", "trade_amount_myr": engine_state[setting.coin]["trade_amount_myr"]}

@app.post("/api/set-tp")
def set_tp(setting: TPSetting):
    """Set take profit percentage per coin from frontend"""
    if setting.coin not in engine_state:
        raise HTTPException(status_code=400, detail="Invalid coin")
    if setting.tp_pct < 0.001 or setting.tp_pct > 0.5:
        raise HTTPException(status_code=400, detail="TP% must be between 0.1% and 50%")
    
    engine_state[setting.coin]["tp_pct"] = setting.tp_pct
    shared.save_state()
    
    # If there are HOLDING layers, re-place consolidated sell with new TP%
    holding_layers = [l for l in engine_state[setting.coin].get("layers", []) if l.get("status") == "HOLDING"]
    if holding_layers:
        from live_engine import _place_consolidated_sell
        _place_consolidated_sell(setting.coin)
    
    return {"status": "success", "tp_pct": engine_state[setting.coin]["tp_pct"]}

@app.post("/api/manual-buy")
def manual_buy(action: ManualAction):
    coin = action.coin
    if coin not in engine_state:
        raise HTTPException(status_code=400, detail="Invalid coin")
        
    price = engine_state[coin]["current_price"]
    if price <= 0:
        raise HTTPException(status_code=400, detail="Price not available")
    
    amount = engine_state[coin].get("trade_amount_myr", 50.0)
    balance = global_state["balance_myr"]
    
    if amount > balance:
        raise HTTPException(status_code=400, detail="Insufficient balance in Hata")

    qty_scale = hata_api.COIN_SCALES.get(coin, {}).get("qty", 4)
    quantity = round(amount / price, qty_scale)
    hata_res = hata_api.place_limit_order(f"{coin}_MYR", "BUY", price, quantity)
    
    if hata_res.get("status") == "error":
        raise HTTPException(status_code=500, detail=f"Hata API Error: {hata_res.get('message')}")

    order_id = hata_res.get("data", {}).get("id")
    layer = {
        "id": len(engine_state[coin]["layers"]) + 1,
        "entry_price": price,
        "amount_myr": amount,
        "quantity": quantity,
        "status": "PENDING_BUY",
        "buy_order_id": str(order_id),
        "hata_buy_res": hata_res,
        "created_at": time.time()
    }
    engine_state[coin]["layers"].append(layer)
    shared.save_state()
    
    # Instantly update balance in global_state to reflect frozen amount
    try:
        res = hata_api.get_myr_balance()
        if res:
            global_state["balance_myr"], global_state["frozen_myr"] = res
    except Exception:
        pass
        
    return {"status": "success", "layer": layer}

@app.post("/api/panic-sell")
def panic_sell(action: ManualAction):
    coin = action.coin
    if coin not in engine_state:
        raise HTTPException(status_code=400, detail="Invalid coin")
    
    # 1. Cancel consolidated sell order if exists
    consolidated_sell_id = engine_state[coin].get("consolidated_sell_order_id")
    if consolidated_sell_id:
        hata_api.cancel_order(f"{coin}_MYR", consolidated_sell_id)
        engine_state[coin]["consolidated_sell_order_id"] = None
    
    # 2. Cancel any pending buy orders
    for layer in engine_state[coin]["layers"]:
        if layer.get("status") == "PENDING_BUY":
            buy_id = layer.get("buy_order_id")
            if buy_id:
                hata_api.cancel_order(f"{coin}_MYR", buy_id)
    
    # 3. Sell all holding at market (use current_price - 2% to ensure fill)
    current_price = engine_state[coin]["current_price"]
    holding_layers = [l for l in engine_state[coin]["layers"] if l.get("status") == "HOLDING"]
    
    if holding_layers and current_price > 0:
        # Sum up all net_qty from holding layers
        total_qty = sum(l.get("net_qty", l.get("sell_quantity", l.get("quantity", 0))) for l in holding_layers)
        qty_scale = hata_api.COIN_SCALES.get(coin, {}).get("qty", 4)
        total_qty = truncate_float(total_qty, qty_scale)
        
        if total_qty > 0:
            # Verify actual balance
            avail_bal, _ = hata_api.get_token_balance(coin)
            if avail_bal < total_qty:
                total_qty = truncate_float(avail_bal, qty_scale)
            
            if total_qty > 0:
                panic_price = current_price * 0.98  # 2% below to ensure fill
                hata_api.place_limit_order(f"{coin}_MYR", "SELL", panic_price, total_qty)
    
    # 4. Clear all layers
    engine_state[coin]["layers"] = []
    engine_state[coin]["consolidated_sell_order_id"] = None
    shared.save_state()
    
    return {"status": "success", "message": f"All positions closed for {coin}"}


def truncate_float(val: float, decimals: int) -> float:
    """Truncate float value to a specific number of decimal places without rounding up."""
    eps = 1e-9
    factor = 10 ** decimals
    return int((val + eps) * factor) / factor


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

@app.on_event("startup")
def start_server():
    # Start live engine in background (which includes WS and price/balance loops)
    import live_engine
    t1 = threading.Thread(target=live_engine.run, daemon=True)
    t1.start()

# Force reload to pick up bot state updates
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
