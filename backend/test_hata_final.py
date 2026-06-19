import sys
sys.path.append("e:\\PROJECTS\\SEMUA PROJECT\\INVESTMENT AI\\backend")
from hata_api import place_limit_order

print("Testing place_limit_order via hata_api.py with formatting...")
# price=180.8, qty=0.005 -> notional = 0.90 RM (below 30 RM min notional)
res = place_limit_order("LTC_MYR", "BUY", 180.8, 0.0056789)
print("Result:", res)
