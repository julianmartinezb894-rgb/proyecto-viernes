# FILE: app.py
# VIERNES 2.0 — Motor de búsqueda y extracción

import os

from flask import Flask, request, jsonify
import requests


app = Flask(__name__)


def buscar_google(termino):
    resultados = []

    api_key = os.environ.get("GOOGLE_API_KEY")
    cx_id = os.environ.get("GOOGLE_CX_ID")

    if not api_key or not cx_id:
        print(
            "[VIERNES - BÚSQUEDA] Faltan GOOGLE_API_KEY o GOOGLE_CX_ID",
            flush=True
        )
        return resultados

    url = "https://www.googleapis.com/customsearch/v1"

    parametros = {
        "key": api_key,
        "cx": cx_id,
        "q": termino,
        "num": 5
    }

    try:
        respuesta = requests.get(
            url,
            params=parametros,
            timeout=15
        )

        respuesta.raise_for_status()

        datos = respuesta.json()

        for item in datos.get("items", []):
            resultados.append({
                "fuente": "VIERNES Engine (Google)",
                "titulo": item.get("title", ""),
                "url": item.get("link", ""),
                "descripcion": item.get("snippet", "")
            })

        print(
            f"[VIERNES - BÚSQUEDA] Resultados encontrados: {len(resultados)}",
            flush=True
        )

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


@app.route("/buscar", methods=["GET"])
def buscar():
    termino = request.args.get("termino", "").strip()

    if not termino:
        return jsonify({
            "error": "El parámetro 'termino' es obligatorio"
        }), 400

    datos_extraidos = buscar_google(termino)

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
