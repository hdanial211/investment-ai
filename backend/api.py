from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Holy Grail Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
engine_state = {
    "current_price": 0.0,
    "last_signal": 0.0, # 0 = wait, 1 = golden entry
    "confidence": 0.0,
    "is_auto": False,
    "layers": [],
    "total_pnl": 0.0,
    "balance_myr": 10000.00
}

class AutoToggle(BaseModel):
    is_auto: bool

@app.get("/api/state")
def get_state():
    return engine_state

@app.post("/api/toggle-auto")
def toggle_auto(toggle: AutoToggle):
    engine_state["is_auto"] = toggle.is_auto
    return {"status": "success", "is_auto": engine_state["is_auto"]}

@app.post("/api/manual-buy")
def manual_buy():
    # Logic to trigger Hata API Buy
    # For now, we simulate layering
    price = engine_state["current_price"]
    if price <= 0:
        raise HTTPException(status_code=400, detail="Price not available")
    
    layer = {
        "id": len(engine_state["layers"]) + 1,
        "entry_price": price,
        "amount_myr": 50.0,
        "take_profit": price * 1.006,
        "status": "OPEN"
    }
    engine_state["layers"].append(layer)
    engine_state["balance_myr"] -= 50.0
    return {"status": "success", "layer": layer}

@app.post("/api/panic-sell")
def panic_sell():
    engine_state["layers"] = []
    # Simulate closing all at market
    return {"status": "success", "message": "All positions closed"}

import threading

def start_server():
    # Start live engine in background
    import live_engine
    t = threading.Thread(target=live_engine.run, daemon=True)
    t.start()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_server()
