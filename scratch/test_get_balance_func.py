import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
import hata_api

avail, froz = hata_api.get_token_balance("XRP")
print(f"XRP Balance: Available={avail}, Frozen={froz}")
