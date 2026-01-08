import requests
import json
import sys

def test_generic_post():
    url = "http://localhost:8000/api/jobs"
    payload = {
        "input_type": "text",
        "content": "Vaga de teste Backend Developer Python. Requisitos: Python 3+ anos, FastAPI, MongoDB. Diferencial: AWS."
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Job created via Generic Endpoint")
        else:
            print("❌ FAILURE: Endpoint returned error")
            
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    test_generic_post()
