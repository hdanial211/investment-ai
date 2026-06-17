import os
import sys
import json
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath('e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI/backend/api.py')))
from backtest.dca_engine import run_dca_backtest

base_dir = 'e:/PROJECTS/SEMUA PROJECT/INVESTMENT AI'
csv_path = os.path.join(base_dir, 'data', 'ETH_USDT_1m.csv')
model_path = os.path.join(base_dir, 'models', 'xgboost_scalping_ETH_1y.pkl')
result_file = os.path.join(base_dir, 'backtesting result')

experiments = [
    {
        "id": 15,
        "name": "The Turtle (Micro DCA, Wide Net)",
        "desc": "Beli banyak tapi saiz sangat kecil untuk tahan crash yang lama.",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 50,
            "drop_threshold": -0.005, "take_profit_pct": 0.005, "trailing_activation_pct": 999.0,
            "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"
        }
    },
    {
        "id": 16,
        "name": "The Sniper (Deep Drop Buying)",
        "desc": "Tunggu harga jatuh 2% baru beli layer baru. TP besar 2%.",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 50.0, "max_layers_per_signal": 5,
            "drop_threshold": -0.020, "take_profit_pct": 0.020, "trailing_activation_pct": 0.010, "trailing_gap_pct": 0.003,
            "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"
        }
    },
    {
        "id": 17,
        "name": "Aggressive Martingale (Micro Size)",
        "desc": "Martingale (1x, 2x, 4x, 8x, 16x) tapi bermula dengan RM5 sahaja. TP ketat 0.3%.",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 5.0, "max_layers_per_signal": 5,
            "drop_threshold": -0.010, "take_profit_pct": 0.003, "trailing_activation_pct": 999.0,
            "use_martingale": True, "use_dynamic_tp": True, "enable_dca": True, "ai_type": "ensemble"
        }
    },
    {
        "id": 18,
        "name": "Wide Gap Martingale (Anti-Crash)",
        "desc": "Martingale gandaan RM10 (10,20,40,80) tapi hanya beli setiap kali jatuh 5%!",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 4,
            "drop_threshold": -0.050, "take_profit_pct": 0.010, "trailing_activation_pct": 999.0,
            "use_martingale": True, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"
        }
    },
    {
        "id": 19,
        "name": "The Scalping Machine (No DCA, Full Trust AI)",
        "desc": "Terus tembak RM300 setiap kali AI suruh. Tiada DCA. TP ketat 0.4%.",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 300.0, "max_layers_per_signal": 1,
            "drop_threshold": -0.999, "take_profit_pct": 0.004, "trailing_activation_pct": 999.0,
            "use_martingale": False, "use_dynamic_tp": False, "enable_dca": False, "ai_type": "ensemble"
        }
    },
    {
        "id": 20,
        "name": "Fixed Layering + Active Trailing Master",
        "desc": "Layer tetap RM20. Take profit dilepaskan (99%) untuk kejar trend dengan Trailing Stop.",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 20.0, "max_layers_per_signal": 10,
            "drop_threshold": -0.010, "take_profit_pct": 0.990, "trailing_activation_pct": 0.005, "trailing_gap_pct": 0.002,
            "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"
        }
    },
    {
        "id": 21,
        "name": "High-Frequency Micro-Martingale",
        "desc": "Martingale pantas (Max 6 layer), Gap sangat kecil 0.3%. Mod mesin basuh.",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 5.0, "max_layers_per_signal": 6,
            "drop_threshold": -0.003, "take_profit_pct": 0.002, "trailing_activation_pct": 999.0,
            "use_martingale": True, "use_dynamic_tp": True, "enable_dca": True, "ai_type": "ensemble"
        }
    },
    {
        "id": 22,
        "name": "The Hybrid: Martingale + Trailing Stop",
        "desc": "Beli bawah dengan Martingale, lepastu bila naik kita perah semaksimum mungkin dengan Trailing.",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 4,
            "drop_threshold": -0.015, "take_profit_pct": 0.990, "trailing_activation_pct": 0.008, "trailing_gap_pct": 0.003,
            "use_martingale": True, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"
        }
    },
    {
        "id": 23,
        "name": "Deep Value Layering (Moderate)",
        "desc": "Saiz RM30, Gap 3%, TP 1.5%. Tunggu dan peram bila bawah.",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 30.0, "max_layers_per_signal": 6,
            "drop_threshold": -0.030, "take_profit_pct": 0.015, "trailing_activation_pct": 999.0,
            "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"
        }
    },
    {
        "id": 24,
        "name": "The Optimal Balance (RM15, 10 Layer, 1% Gap, 0.6% TP)",
        "desc": "Cuba cari titik pertengahan yang sempurna. Tidak terlalu agresif, tak terlalu selamat.",
        "params": {
            "initial_cash": 1000.0, "trade_size_fiat": 15.0, "max_layers_per_signal": 10,
            "drop_threshold": -0.010, "take_profit_pct": 0.006, "trailing_activation_pct": 999.0,
            "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"
        }
    }
]

def append_to_md(content):
    with open(result_file, 'a', encoding='utf-8') as f:
        f.write(content + "\n")

print("Starting 10 Experiments...")

for exp in experiments:
    print(f"Running Exp {exp['id']}: {exp['name']}...")
    try:
        res = run_dca_backtest(csv_path, model_path, **exp['params'])
        
        # Prepare Markdown
        md = f"""---

## {exp['id']}. Eksperimen: {exp['name']}
**Penerangan:** {exp['desc']}
**Tetapan:**
- Saiz Layer: RM {exp['params']['trade_size_fiat']} | Max Layer: {exp['params']['max_layers_per_signal']}
- Gap Layering: {abs(exp['params']['drop_threshold'])*100:.2f}% | Take Profit: {exp['params']['take_profit_pct']*100:.2f}%
- Martingale: {exp['params']['use_martingale']} | Dynamic TP: {exp['params'].get('use_dynamic_tp', False)}
**Keputusan:**
- Jumlah Trade: {res['total_closed_trades']}
- Win Rate: {res['win_rate_pct']:.2f}% ({res['won_trades']} Menang / {res['lost_trades']} Kalah)
- Untung Bersih: **+ RM {res['net_pnl']:.2f}**
- Max Drawdown: **{res['max_drawdown_pct']:.2f}%**
- Baki Akaun: RM {res['final_value']:.2f}
"""
        append_to_md(md)
        print(f"Exp {exp['id']} done. PnL: {res['net_pnl']:.2f}")
    except Exception as e:
        print(f"Error on Exp {exp['id']}: {e}")
        traceback.print_exc()

print("All experiments completed!")
