import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def test_groq():
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    mock_state = {
        "global": {
            "balance_myr": 88.82,
            "frozen_myr": 30.08
        },
        "coins": {
            "XRP": {
                "current_price": 4.72,
                "layers": [
                    {
                        "id": 2,
                        "entry_price": 4.726,
                        "take_profit": 4.75,
                        "status": "PENDING_SELL"
                    }
                ]
            },
            "LTC": {
                "current_price": 182.4,
                "layers": [
                    {
                        "id": 1,
                        "entry_price": 182.3,
                        "take_profit": 183.21,
                        "status": "PENDING_BUY"
                    }
                ]
            }
        }
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional crypto trading bot guardian watchdog. You analyze the active trading layers and account state, and provide safety recommendations in Malay. You must return your response in JSON format matching the schema: {\"status\": \"safe\" | \"warning\" | \"action_required\", \"analysis\": \"string\", \"recommendation\": \"string\"}"
            },
            {
                "role": "user",
                "content": f"Here is the current state of my trading bot:\n{json.dumps(mock_state, indent=2)}"
            }
        ],
        "response_format": {
            "type": "json_object"
        }
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        print("Status Code:", res.status_code)
        if res.status_code == 200:
            print("Groq Response JSON:")
            print(json.dumps(res.json(), indent=2))
        else:
            print("Error Response:", res.text)
    except Exception as e:
        print("Exception:", e)

test_groq()
