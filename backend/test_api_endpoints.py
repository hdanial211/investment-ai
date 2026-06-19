import requests

print("Setting risk level to 3...")
res1 = requests.post("http://localhost:8000/api/set-risk-level", json={"coin": "ETH", "risk_level": 3})
print("POST set-risk-level:", res1.json())

print("\nGetting state...")
res2 = requests.get("http://localhost:8000/api/state")
data = res2.json()
print("GET risk_level:", data["coins"]["ETH"]["risk_level"])

print("\nToggling auto...")
res3 = requests.post("http://localhost:8000/api/toggle-auto", json={"coin": "ETH", "is_auto": True})
print("POST toggle-auto:", res3.json())

print("\nGetting state...")
res4 = requests.get("http://localhost:8000/api/state")
data2 = res4.json()
print("GET is_auto:", data2["coins"]["ETH"]["is_auto"])
