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
