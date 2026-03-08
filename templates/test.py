import requests

url = 'http://127.0.0.1:5000/api/chat'
data = {'message': 'Ինչ է վիրուսը'}

try:
    response = requests.post(url, json=data, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except requests.exceptions.ConnectionError:
    print("❌ Սերվերը չի աշխատում: Ստուգիր, որ python app.py-ն աշխատում է")
except Exception as e:
    print(f"❌ Սխալ: {e}")