import os
import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

def buscar_en_google_oficial(query, api_key, cx_id):
    url = f"https://googleapis.com{api_key}&cx={cx_id}&q={query}"
    for intento in range(5):
        try:
            headers = {'User-Agent': 'ViernesAgentEngine/1.0 (Autonomous B2B Bot)'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 429:
                time.sleep(2 ** intento)
                continue
            response.raise_for_status()
            data = response.json()
            
            items = data.get('items', [])
            resultados = []
            for item in items:
                resultados.append({
                    'titulo': item.get('title', 'Sin título'),
                    'enlace': item.get('link', '')
                })
            return resultados
        except Exception:
            time.sleep(2 ** intento)
    return []

@app.route('/')
def home():
    # Endpoint de verificación para que Render sepa que VIERNES está vivo
    return jsonify({"estado": "VIERNES operando en la nube", "motor": "Activo"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
