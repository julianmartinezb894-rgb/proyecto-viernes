# FILE: buscador_web.py
# VIERNES 2.0 — Motor de búsqueda web abierta mediante Tavily

import os
import requests


TAVILY_API_URL = "https://api.tavily.com/search"


def buscar_web(termino):
    """
    Busca información en la web abierta mediante Tavily.

    La clave se obtiene exclusivamente desde la variable
    de entorno TAVILY_API_KEY configurada en Render.
    """

    termino = str(termino).strip()

    if not termino:
        return []

    api_key = os.environ.get("TAVILY_API_KEY")

    if not api_key:
        print(
            "[VIERNES - WEB] ERROR: TAVILY_API_KEY no está configurada.",
            flush=True
        )
        return []

    payload = {
        "query": termino,
        "search_depth": "basic",
        "topic": "general",
        "max_results": 8,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
        "safe_search": True
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        respuesta = requests.post(
            TAVILY_API_URL,
            json=payload,
            headers=headers,
            timeout=20
        )

        respuesta.raise_for_status()

        datos = respuesta.json()

        resultados = []

        for resultado in datos.get("results", []):
            titulo = str(resultado.get("title", "")).strip()
            url = str(resultado.get("url", "")).strip()
            contenido = str(resultado.get("content", "")).strip()

            if titulo and url:
                resultados.append({
                    "fuente": "VIERNES Engine (Tavily Web Search)",
                    "titulo": titulo,
                    "url": url,
                    "contenido": contenido
                })

        print(
            f"[VIERNES - WEB] Búsqueda completada: "
            f"{len(resultados)} resultados para '{termino}'",
            flush=True
        )

        return resultados

    except requests.RequestException as error:
        print(
            f"[VIERNES - WEB] Error de conexión con Tavily: {error}",
            flush=True
        )
        return []

    except ValueError as error:
        print(
            f"[VIERNES - WEB] Respuesta JSON inválida de Tavily: {error}",
            flush=True
        )
        return []

    except Exception as error:
        print(
            f"[VIERNES - WEB] Error inesperado: {error}",
            flush=True
        )
        return []
