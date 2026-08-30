import urllib.parse
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def scraping_alternativo(termino):
    resultados = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    # Buscador DuckDuckGo Lite para evitar captchas y bloqueos
    url_busqueda = f"https://duckduckgo.com{urllib.parse.quote(termino)}"
    
    try:
        res = requests.get(url_busqueda, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # Encontrar los bloques de resultados orgánicos
            links = soup.find_all("a", class_="result__url")
            
            for link in links[:5]:  # Extraer los primeros 5 enlaces
                url_limpia = link.get("href", "").strip()
                if url_limpia:
                    resultados.append({
                        "fuente": "VIERNES Engine (DDG)",
                        "url": url_limpia
                    })
    except Exception as e:
        print(f"Error en el motor de scraping: {e}")
        
    return resultados

@app.route("/buscar", methods=["GET"])
def buscar():
    termino = request.args.get("termino")
    
    if not termino:
        return jsonify({"error": "El parámetro 'termino' es obligatorio"}), 400
        
    # Activación del motor alternativo automático
    datos_extraidos = scraping_alternativo(termino)
    
    return jsonify({
        "motor": "VIERNES Data Extractor",
        "termino_buscado": termino,
        "resultados": datos_extraidos
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
