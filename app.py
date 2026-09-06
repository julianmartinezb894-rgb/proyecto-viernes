# FILE: app.py
# VIERNES 2.0 — Motor de búsqueda y extracción

import os
import urllib.parse
import xml.etree.ElementTree as ET

from flask import Flask, request, jsonify
import requests


app = Flask(__name__)


def buscar_google_news(termino):
    """Búsqueda gratuita mediante Google News RSS."""
    resultados = []

    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote_plus(termino)
        + "&hl=en-US&gl=US&ceid=US:en"
    )

    headers = {
        "User-Agent": "VIERNES-Engine/1.0"
    }

    try:
        respuesta = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        respuesta.raise_for_status()

        raiz = ET.fromstring(respuesta.content)

        for item in raiz.findall(".//item")[:5]:
            titulo = item.findtext("title", "").strip()
            enlace = item.findtext("link", "").strip()

            if titulo and enlace:
                resultados.append({
                    "fuente": "VIERNES Engine (Google News)",
                    "titulo": titulo,
                    "url": enlace
                })

        print(
            f"[VIERNES - BÚSQUEDA] Resultados: {len(resultados)}",
            flush=True
        )

    except requests.RequestException as error:
        print(
            f"[VIERNES - BÚSQUEDA] Error de conexión: {error}",
            flush=True
        )

    except ET.ParseError as error:
        print(
            f"[VIERNES - BÚSQUEDA] Error de XML: {error}",
            flush=True
        )

    except Exception as error:
        print(
            f"[VIERNES - BÚSQUEDA] Error de extracción: {error}",
            flush=True
        )

    return resultados


def scraping_alternativo(termino):
    return buscar_google_news(termino)


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "motor": "VIERNES Data Extractor",
        "estado": "activo"
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
