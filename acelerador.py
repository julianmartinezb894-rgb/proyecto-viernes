import os
import secrets
import sys
from datetime import datetime
from decimal import Decimal

from flask import jsonify, request


print(
    "[ACELERADOR] Iniciando VIERNES...",
    flush=True
)

try:
    import app as app_original
except Exception as error:
    print(
        f"[ACELERADOR] Error al cargar app.py: {error}",
        flush=True
    )
    sys.exit(1)

if not hasattr(app_original, "app"):
    print(
        "[ACELERADOR] ERROR: app.py no contiene app.",
        flush=True
    )
    sys.exit(1)

flask_app = app_original.app

print(
    "[ACELERADOR] app.py cargado correctamente.",
    flush=True
)


if not any(
    regla.rule == "/despertar"
    for regla in flask_app.url_map.iter_rules()
):
    @flask_app.route("/despertar", methods=["GET", "HEAD"])
    def despertar_sistema():
        return jsonify({
            "status": "online",
            "message": "VIERNES activo y operativo"
        }), 200


try:
    from buscador_web import buscar_web

    app_original.scraping_alternativo = buscar_web

    print(
        "[ACELERADOR] Motor Tavily conectado.",
        flush=True
    )

except Exception as error:
    print(
        f"[ACELERADOR] Error al conectar Tavily: {error}",
        flush=True
    )
    sys.exit(1)


try:
    from cache_viernes import (
        obtener_datos_rapidos,
        guardar_datos_rapidos
    )

    buscador_web_original = app_original.scraping_alternativo

    def busqueda_con_cache(termino, *args, **kwargs):
        try:
            datos_cache = obtener_datos_rapidos(termino)

            if datos_cache is not None:
                return datos_cache

        except Exception as error:
            print(
                f"[ACELERADOR] Error de cache: {error}",
                flush=True
            )

        resultado = buscador_web_original(
            termino,
            *args,
            **kwargs
        )

        try:
            guardar_datos_rapidos(
                termino,
                resultado
            )
        except Exception as error:
            print(
                f"[ACELERADOR] Error guardando cache: {error}",
                flush=True
            )

        return resultado

    app_original.scraping_alternativo = busqueda_con_cache

    print(
        "[ACELERADOR] Cache conectado.",
        flush=True
    )

except Exception as error:
    print(
        f"[ACELERADOR] Cache no disponible: {error}",
        flush=True
    )


NICHO_INICIAL = "personas con demanda directa de extracción de datos"

CONSULTAS_INICIALES = (
    'site:reddit.com "need web scraping"',
    'site:reddit.com "looking for a web scraper"',
    'site:reddit.com "need data extraction"',
)


def token_valido():
    token_configurado = os.environ.get(
        "PIPELINE_ADMIN_TOKEN",
        ""
    )

    token_recibido = request.headers.get(
        "X-Pipeline-Token",
        ""
    )

    if not token_configurado:
        return False

    return secrets.compare_digest(
        token_recibido,
        token_configurado
    )


def convertir_json(valor):
    if isinstance(valor, dict):
        return {
            clave: convertir_json(dato)
            for clave, dato in valor.items()
        }

    if isinstance(valor, list):
        return [
            convertir_json(dato)
            for dato in valor
        ]

    if isinstance(valor, datetime):
        return valor.isoformat()

    if isinstance(valor, Decimal):
        return float(valor)

    return valor


if not any(
    regla.rule == "/pipeline/descubrir"
    for regla in flask_app.url_map.iter_rules()
):
    @flask_app.route(
        "/pipeline/descubrir",
        methods=["POST"]
    )
    def ejecutar_descubrimiento_comercial():
        if not token_valido():
            return jsonify({
                "error": "No autorizado"
            }), 401

        try:
            from pipeline_comercial import (
                abrir_base_datos,
                descubrir_leads
            )

            conexion = abrir_base_datos()

            resumen_total = {
                "resultados_tavily": 0,
                "leads_guardados": 0,
                "duplicados": 0,
                "cualificados": 0,
            }

            try:
                for consulta in CONSULTAS_INICIALES:
                    resumen = descubrir_leads(
                        conexion,
                        NICHO_INICIAL,
                        consulta
                    )

                    for clave in resumen_total:
                        resumen_total[clave] += resumen[
                            clave
                        ]
            finally:
                conexion.close()

            return jsonify({
                "status": "ok",
                "nicho": NICHO_INICIAL,
                "consultas": CONSULTAS_INICIALES,
                "resultado": resumen_total
            }), 200

        except Exception as error:
            print(
                f"[ACELERADOR] Error en pipeline: {error}",
                flush=True
            )

            return jsonify({
                "error": "Error al ejecutar pipeline comercial"
            }), 500


if not any(
    regla.rule == "/pipeline/metricas"
    for regla in flask_app.url_map.iter_rules()
):
    @flask_app.route(
        "/pipeline/metricas",
        methods=["GET"]
    )
    def ver_metricas_comerciales():
        if not token_valido():
            return jsonify({
                "error": "No autorizado"
            }), 401

        try:
            from pipeline_comercial import (
                abrir_base_datos,
                obtener_metricas
            )

            conexion = abrir_base_datos()

            try:
                metricas = obtener_metricas(conexion)
            finally:
                conexion.close()

            return jsonify({
                "status": "ok",
                "metricas": convertir_json(metricas)
            }), 200

        except Exception as error:
            print(
                f"[ACELERADOR] Error leyendo métricas: {error}",
                flush=True
            )

            return jsonify({
                "error": "Error al leer métricas"
            }), 500


if not any(
    regla.rule == "/pipeline/leads"
    for regla in flask_app.url_map.iter_rules()
):
    @flask_app.route(
        "/pipeline/leads",
        methods=["GET"]
    )
    def ver_leads_comerciales():
        if not token_valido():
            return jsonify({
                "error": "No autorizado"
            }), 401

        try:
            from pipeline_comercial import (
                abrir_base_datos,
                obtener_leads
            )

            conexion = abrir_base_datos()

            try:
                leads = obtener_leads(
                    conexion,
                    limite=20
                )
            finally:
                conexion.close()

            return jsonify({
                "status": "ok",
                "leads": convertir_json(leads)
            }), 200

        except Exception as error:
            print(
                f"[ACELERADOR] Error leyendo leads: {error}",
                flush=True
            )

            return jsonify({
                "error": "Error al leer leads"
            }), 500


def obtener_puerto():
    try:
        return int(
            os.environ.get("PORT", "10000")
        )
    except (TypeError, ValueError):
        return 10000


if __name__ == "__main__":
    puerto = obtener_puerto()

    print(
        f"[ACELERADOR] VIERNES listo en puerto {puerto}.",
        flush=True
    )

    flask_app.run(
        host="0.0.0.0",
        port=puerto,
        debug=False,
        threaded=True
    )
