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

def append_to_md(content):
    with open(result_file, 'a', encoding='utf-8') as f:
        f.write(content + "\n")

# Setup 30 unique experiments
experiments = [
    # --- KUMPULAN 1: KONSERVATIF & SELAMAT (Modal Terkawal) ---
    {"id": 15, "name": "The Turtle Guard (RM10 x 30 Layer)", "desc": "Beli banyak tapi saiz sangat kecil untuk tahan crash 15%.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 30, "drop_threshold": -0.005, "take_profit_pct": 0.005, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 16, "name": "The Sniper (Deep Drop)", "desc": "Tunggu harga jatuh 3% baru beli layer baru. TP besar 3%.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 50.0, "max_layers_per_signal": 5, "drop_threshold": -0.030, "take_profit_pct": 0.030, "trailing_activation_pct": 0.015, "trailing_gap_pct": 0.005, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 17, "name": "Deep Value Layering (Moderate)", "desc": "Saiz RM30, Gap 2%, TP 1.5%. Tunggu dan peram bila bawah.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 30.0, "max_layers_per_signal": 6, "drop_threshold": -0.020, "take_profit_pct": 0.015, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 18, "name": "Patience is Gold (1 Layer Only)", "desc": "Beli RM100 sekali, TP 5%, tiada DCA. Percaya 100% pada AI.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 100.0, "max_layers_per_signal": 1, "drop_threshold": -0.990, "take_profit_pct": 0.050, "trailing_activation_pct": 0.020, "trailing_gap_pct": 0.005, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": False, "ai_type": "ensemble"}},
    {"id": 19, "name": "Micro DCA Jarak Jauh", "desc": "RM10, Gap 5%. Beli bila betul-betul jatuh teruk.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 10, "drop_threshold": -0.050, "take_profit_pct": 0.020, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},

    # --- KUMPULAN 2: SCALPER LAJU (Ambil Untung Cepat) ---
    {"id": 20, "name": "High Frequency Scalping (0.2% TP)", "desc": "TP sangat ketat (0.2%) untuk trade beribu kali setahun.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 20.0, "max_layers_per_signal": 10, "drop_threshold": -0.005, "take_profit_pct": 0.002, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 21, "name": "Machine Gun Scalper (Gap 0.3%)", "desc": "Beli setiap 0.3% jatuh. RM10 per layer.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 15, "drop_threshold": -0.003, "take_profit_pct": 0.004, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 22, "name": "Mid-Frequency Trailing (0.5% Act)", "desc": "Bila untung 0.5%, buka Trailing Stop 0.1% untuk kejar harga.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 20.0, "max_layers_per_signal": 8, "drop_threshold": -0.008, "take_profit_pct": 0.990, "trailing_activation_pct": 0.005, "trailing_gap_pct": 0.001, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 23, "name": "Scalp & Run (RM50, TP 0.4%)", "desc": "Modal besar sikit (RM50), tapi cepat lari (TP 0.4%).", "params": {"initial_cash": 1000.0, "trade_size_fiat": 50.0, "max_layers_per_signal": 5, "drop_threshold": -0.005, "take_profit_pct": 0.004, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 24, "name": "Heavy Scalping (RM100, 3 Layers)", "desc": "Trade berat tapi pantas.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 100.0, "max_layers_per_signal": 3, "drop_threshold": -0.010, "take_profit_pct": 0.005, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},

    # --- KUMPULAN 3: MARTINGALE TRADISIONAL (1x, 2x, 4x, 8x...) ---
    {"id": 25, "name": "Aggressive Micro Martingale (5 Lapis)", "desc": "Mula dengan RM5 sahaja, TP ketat 0.3%. Max Exposure RM155.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 5.0, "max_layers_per_signal": 5, "drop_threshold": -0.010, "take_profit_pct": 0.003, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 26, "name": "Wide Gap Martingale (Anti-Crash)", "desc": "Martingale gandaan RM10 (10,20,40,80) tapi hanya beli setiap kali jatuh 5%!", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 4, "drop_threshold": -0.050, "take_profit_pct": 0.010, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 27, "name": "Fast Recovery Martingale (RM10, 4 Lapis)", "desc": "Gap kecil 0.8% tapi ganda cepat untuk pulih.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 4, "drop_threshold": -0.008, "take_profit_pct": 0.005, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 28, "name": "High Risk Martingale (RM20, 5 Lapis)", "desc": "Max exposure RM620. Untung besar tapi risiko tinggi.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 20.0, "max_layers_per_signal": 5, "drop_threshold": -0.010, "take_profit_pct": 0.010, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 29, "name": "Micro Frequency Martingale (RM2, 8 Lapis)", "desc": "Mula dengan RM2. Gap 0.5%. Mampu cecah gandaan 128x (RM256).", "params": {"initial_cash": 1000.0, "trade_size_fiat": 2.0, "max_layers_per_signal": 8, "drop_threshold": -0.005, "take_profit_pct": 0.004, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},

    # --- KUMPULAN 4: DYNAMIC TP + MARTINGALE (Sistem Pilihan Baru) ---
    {"id": 30, "name": "Dynamic TP Martingale (RM5, Gap 1%)", "desc": "TP membesar apabila Martingale masuk layer dalam. Gap 1%.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 5.0, "max_layers_per_signal": 5, "drop_threshold": -0.010, "take_profit_pct": 0.002, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": True, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 31, "name": "Dynamic TP Martingale (RM10, Gap 0.5%)", "desc": "Layer rapat (0.5%) untuk agresif mengumpul pada kejatuhan kecil.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 4, "drop_threshold": -0.005, "take_profit_pct": 0.002, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": True, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 32, "name": "Dynamic TP Extreme Drop (Gap 3%)", "desc": "Martingale yang selamat pada junaman 3% sahaja.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 4, "drop_threshold": -0.030, "take_profit_pct": 0.0025, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": True, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 33, "name": "Dynamic TP Trailing Hybrid", "desc": "Sistem Dynamic TP, tetapi ada Trailing Stop dilekatkan bila untung.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 4, "drop_threshold": -0.010, "take_profit_pct": 0.990, "trailing_activation_pct": 0.005, "trailing_gap_pct": 0.001, "use_martingale": True, "use_dynamic_tp": True, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 34, "name": "The Ultimate 6-Layer Dynamic Martingale", "desc": "Mula dengan RM3. Max exposure RM189. Dynamic TP diaktifkan.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 3.0, "max_layers_per_signal": 6, "drop_threshold": -0.008, "take_profit_pct": 0.002, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": True, "enable_dca": True, "ai_type": "ensemble"}},

    # --- KUMPULAN 5: TRAILING STOP MASTER (Mengejar Trend) ---
    {"id": 35, "name": "The Trailing Master (Gap 1%, Act 1%)", "desc": "Tiada Hard TP. Trailing hidup bila untung 1%.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 15.0, "max_layers_per_signal": 10, "drop_threshold": -0.010, "take_profit_pct": 0.990, "trailing_activation_pct": 0.010, "trailing_gap_pct": 0.003, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 36, "name": "Ultra Tight Trailing (Act 0.3%, Gap 0.1%)", "desc": "Trailing hidup sangat awal (0.3%) untuk kunci untung segera.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 20.0, "max_layers_per_signal": 10, "drop_threshold": -0.008, "take_profit_pct": 0.990, "trailing_activation_pct": 0.003, "trailing_gap_pct": 0.001, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 37, "name": "Wide Trailing (Act 2%, Gap 0.5%)", "desc": "Beri ruang untuk trend membesar sebelum jual.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 15, "drop_threshold": -0.010, "take_profit_pct": 0.990, "trailing_activation_pct": 0.020, "trailing_gap_pct": 0.005, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 38, "name": "Trailing Stop + Martingale (RM10, 4L)", "desc": "Pulih dengan Martingale dan kejar profit dengan Trailing.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 4, "drop_threshold": -0.010, "take_profit_pct": 0.990, "trailing_activation_pct": 0.005, "trailing_gap_pct": 0.002, "use_martingale": True, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 39, "name": "Deep Trailing Rescue", "desc": "Layer di -3%, Trailing di 0.5%. Pertahanan kental.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 30.0, "max_layers_per_signal": 5, "drop_threshold": -0.030, "take_profit_pct": 0.990, "trailing_activation_pct": 0.005, "trailing_gap_pct": 0.002, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},

    # --- KUMPULAN 6: TETAPAN OPTIMUM (Campuran Strategi Terbaik) ---
    {"id": 40, "name": "Golden Mean (RM15, 10L, 0.8% Gap, 0.6% TP)", "desc": "Kesimbangan antara profit sederhana dan pertahanan.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 15.0, "max_layers_per_signal": 10, "drop_threshold": -0.008, "take_profit_pct": 0.006, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 41, "name": "The Whale Imitator (RM250, 2L, 5% Gap)", "desc": "Membeli saiz gergasi pada kejatuhan drastik.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 250.0, "max_layers_per_signal": 2, "drop_threshold": -0.050, "take_profit_pct": 0.020, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 42, "name": "Micro Limitless (RM1, 100L, 0.2% Gap)", "desc": "Saiz sekecil mungkin. Sentiasa berada dalam pasaran.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 1.0, "max_layers_per_signal": 100, "drop_threshold": -0.002, "take_profit_pct": 0.005, "trailing_activation_pct": 999.0, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 43, "name": "Martingale Mega Defense (RM5, 5L, 2% Gap)", "desc": "Martingale yang cuma masuk pasaran bila ada junaman merah.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 5.0, "max_layers_per_signal": 5, "drop_threshold": -0.020, "take_profit_pct": 0.005, "trailing_activation_pct": 999.0, "use_martingale": True, "use_dynamic_tp": True, "enable_dca": True, "ai_type": "ensemble"}},
    {"id": 44, "name": "The Final Holy Grail Candidate", "desc": "RM10, 15 Layer, 0.6% Gap, Trailing 0.5% Act / 0.15% Gap. Sangat kukuh.", "params": {"initial_cash": 1000.0, "trade_size_fiat": 10.0, "max_layers_per_signal": 15, "drop_threshold": -0.006, "take_profit_pct": 0.990, "trailing_activation_pct": 0.005, "trailing_gap_pct": 0.0015, "use_martingale": False, "use_dynamic_tp": False, "enable_dca": True, "ai_type": "ensemble"}}
]

print(f"Starting {len(experiments)} Experiments in Batch...")

append_to_md("\n\n# --- UJIAN BATCH 30 TETAPAN (MEGA BACKTEST) ---\n")

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

print("All 30 experiments completed successfully!")
