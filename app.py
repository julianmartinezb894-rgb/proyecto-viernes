# FILE: app.py
# VIERNES 2.0 — Motor de búsqueda y extracción

import os
import urllib.parse
import time

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

    termino_codificado = urllib.parse.quote_plus(termino)

    # Buscador gratuito, sin API Key.
    url_busqueda = (
        f"https://lite.duckduckgo.com/lite/?q={termino_codificado}"
    )

    try:
        respuesta = requests.get(
            url_busqueda,
            headers=headers,
            timeout=30
        )

        respuesta.raise_for_status()

        soup = BeautifulSoup(respuesta.text, "html.parser")

        # Selector principal de resultados.
        enlaces = soup.select("a.result-link")

        print(
            f"[VIERNES - BÚSQUEDA] Enlaces encontrados: {len(enlaces)}",
            flush=True
        )

        for enlace in enlaces[:5]:
            url_limpia = enlace.get("href", "").strip()

            if url_limpia:
                resultados.append({
                    "fuente": "VIERNES Engine (DDG)",
                    "url": url_limpia
                })

    except requests.RequestException as error:
        print(
            f"[VIERNES - BÚSQUEDA] Error de conexión: {error}",
            flush=True
        )

    except Exception as error:
        print(
            f"[VIERNES - BÚSQUEDA] Error de extracción: {error}",
            flush=True
        )

    return resultados


@app.route("/")
def inicio():
    return jsonify({
        "motor": "VIERNES Data Extractor",
        "estado": "activo",
        "mensaje": "Motor de búsqueda disponible"
    })


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
    puerto = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=puerto
    )
