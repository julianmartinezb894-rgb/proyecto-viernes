import os
import time
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Credenciales inyectadas de forma segura desde el entorno de Render
API_KEY = os.environ.get("GOOGLE_API_KEY")
CX_ID = os.environ.get("GOOGLE_CX_ID")

def buscar_en_google_oficial(query):
    url = f"https://googleapis.com{API_KEY}&cx={CX_ID}&q={query}"
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
    return jsonify({"estado": "VIERNES operando en la nube", "motor": "Activo"})

@app.route('/buscar')
def ejecutar_busqueda():
    # Captura el término de búsqueda desde la URL (ej: /buscar?q=tecnologia)
    query = request.args.get('q', 'arbitraje agéntico B2B')
    datos_extraidos = buscar_en_google_oficial(query)
    return jsonify({
        "motor": "VIERNES Data Extractor",
        "termino_buscado": query,
        "resultados": datos_extraidos
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
