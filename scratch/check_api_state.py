import requests
import json

try:
    res = requests.get("http://localhost:8000/api/state", timeout=5)
    print("Status:", res.status_code)
    print(json.dumps(res.json(), indent=2))
except Exception as e:
    print("Error:", e)
