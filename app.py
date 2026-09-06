# FILE: app.py
# VIERNES 2.0 — Motor de búsqueda y extracción

import os
import urllib.parse

from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup


app = Flask(__name__)


def buscar_duckduckgo(termino):
    """Busca resultados web sin API key."""
    resultados = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    url = (
        "https://html.duckduckgo.com/html/?q="
        + urllib.parse.quote_plus(termino)
    )

    try:
        respuesta = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        respuesta.raise_for_status()

        soup = BeautifulSoup(respuesta.text, "html.parser")

        for enlace in soup.select("a.result__a")[:5]:
            titulo = enlace.get_text(" ", strip=True)
            url_resultado = enlace.get("href", "").strip()

            if titulo and url_resultado:
                resultados.append({
                    "fuente": "VIERNES Engine (DDG)",
                    "titulo": titulo,
                    "url": url_resultado
                })

        print(
            f"[VIERNES - DDG] Resultados: {len(resultados)}",
            flush=True
        )

    except requests.RequestException as error:
        print(
            f"[VIERNES - DDG] Error: {error}",
            flush=True
        )

    return resultados


def buscar_wikipedia(termino):
    """Respaldo gratuito cuando DuckDuckGo no responde."""
    resultados = []

    url = "https://en.wikipedia.org/w/api.php"

    parametros = {
        "action": "query",
        "list": "search",
        "srsearch": termino,
        "format": "json",
        "utf8": 1,
        "srlimit": 5
    }

    try:
        respuesta = requests.get(
            url,
            params=parametros,
            timeout=15
        )

        respuesta.raise_for_status()

        datos = respuesta.json()

        for resultado in datos.get("query", {}).get("search", []):
            titulo = resultado.get("title", "").strip()

            if titulo:
                resultados.append({
                    "fuente": "VIERNES Engine (Wikipedia)",
                    "titulo": titulo,
                    "url": (
                        "https://en.wikipedia.org/wiki/"
                        + urllib.parse.quote(
                            titulo.replace(" ", "_")
                        )
                    )
                })

        print(
            f"[VIERNES - WIKIPEDIA] Resultados: {len(resultados)}",
            flush=True
        )

    except requests.RequestException as error:
        print(
            f"[VIERNES - WIKIPEDIA] Error: {error}",
            flush=True
        )

    except Exception as error:
        print(
            f"[VIERNES - WIKIPEDIA] Error de extracción: {error}",
            flush=True
        )

    return resultados


def scraping_alternativo(termino):
    """Motor principal con respaldo gratuito."""
    resultados = buscar_duckduckgo(termino)

    if not resultados:
        print(
            "[VIERNES - BÚSQUEDA] DDG sin resultados. "
            "Activando respaldo Wikipedia.",
            flush=True
        )

        resultados = buscar_wikipedia(termino)

    return resultados


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
