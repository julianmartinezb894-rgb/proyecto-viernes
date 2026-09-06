# FILE: app.py
# VIERNES 2.0 — Motor de búsqueda y extracción
#
# Corrección:
# - URL válida de DuckDuckGo Lite.
# - Extracción de resultados orgánicos.
# - Mantiene la ruta /buscar.
# - No modifica finanzas.py ni otros archivos.

import urllib.parse

from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup


app = Flask(__name__)


def scraping_alternativo(termino):
    resultados = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # URL correcta de DuckDuckGo Lite.
    termino_codificado = urllib.parse.quote_plus(termino)
    url_busqueda = (
        f"https://lite.duckduckgo.com/lite/?q={termino_codificado}"
    )

    try:
        respuesta = requests.get(
            url_busqueda,
            headers=headers,
            timeout=8
        )

        respuesta.raise_for_status()

        soup = BeautifulSoup(respuesta.text, "html.parser")

        # DuckDuckGo Lite utiliza enlaces con la clase result-link.
        enlaces = soup.select("a.result-link")

        for enlace in enlaces[:5]:
            url_limpia = enlace.get("href", "").strip()

            if url_limpia:
                resultados.append({
                    "fuente": "VIERNES Engine (DDG Lite)",
                    "url": url_limpia
                })

    except requests.RequestException as error:
        print(f"Error de conexión con DuckDuckGo: {error}")

    except Exception as error:
        print(f"Error en el motor de scraping: {error}")

    return resultados


@app.route("/buscar", methods=["GET"])
def buscar():
    termino = request.args.get("termino", "").strip()

    if not termino:
        return jsonify({
            "error": "El parámetro 'termino' es obligatorio"
        }), 400

    datos_extraidos = scraping_alternativo(termino)

    return jsonify({
        "motor": "VIERNES Data Extractor",
        "termino_buscado": termino,
        "resultados": datos_extraidos
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
