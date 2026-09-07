# FILE: acelerador.py
# VIERNES 2.0 — Arrancador principal de Render
#
# Funciones:
# 1. Carga app.py sin modificarlo.
# 2. Inyecta la ruta /despertar.
# 3. Sustituye el motor de búsqueda por buscador_web.py.
# 4. Mantiene el proceso Flask activo.
#
# IMPORTANTE:
# No se ejecuta auto_marketing.py desde aquí.

import sys
import threading
import os

print(
    "[ACELERADOR] Iniciando inyección dinámica de VIERNES...",
    flush=True
)

# ============================================================
# 1. CARGAR APLICACIÓN BASE
# ============================================================

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
        "[ACELERADOR] ERROR CRÍTICO: app.py no contiene 'app'.",
        flush=True
    )
    sys.exit(1)

flask_app = app_original.app

print(
    "[ACELERADOR] app.py cargado correctamente.",
    flush=True
)

# ============================================================
# 2. RUTA DE SALUD
# ============================================================

if not any(
    regla.rule == "/despertar"
    for regla in flask_app.url_map.iter_rules()
):
    @flask_app.route("/despertar", methods=["GET", "HEAD"])
    def despertar_sistema():
        return {
            "status": "online",
            "message": "VIERNES activo y operativo"
        }, 200

    print(
        "[ACELERADOR] Ruta /despertar inyectada.",
        flush=True
    )
else:
    print(
        "[ACELERADOR] Ruta /despertar ya existe.",
        flush=True
    )

# ============================================================
# 3. SUSTITUIR EL MOTOR DE BÚSQUEDA
# ============================================================

try:
    from buscador_web import buscar_web

    app_original.scraping_alternativo = buscar_web

    print(
        "[ACELERADOR] Motor web Tavily conectado correctamente.",
        flush=True
    )

except Exception as error:
    print(
        f"[ACELERADOR] ERROR al conectar buscador_web.py: {error}",
        flush=True
    )
    sys.exit(1)

# ============================================================
# 4. CACHE OPCIONAL
# ============================================================

try:
    from cache_viernes import (
        obtener_datos_rapidos,
        guardar_datos_rapidos
    )

    buscador_web_original = app_original.scraping_alternativo

    def busqueda_con_cache(termino, *args, **kwargs):
        """
        Primero intenta obtener el resultado desde memoria.
        Si no existe, consulta Tavily y guarda la respuesta.
        """

        try:
            datos_cache = obtener_datos_rapidos(termino)

            if datos_cache is not None:
                print(
                    f"[ACELERADOR] Cache HIT: {termino}",
                    flush=True
                )
                return datos_cache

        except Exception as error:
            print(
                f"[ACELERADOR] Error leyendo cache: {error}",
                flush=True
            )

        print(
            f"[ACELERADOR] Cache MISS: {termino}. "
            "Consultando web...",
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
        "[ACELERADOR] Sistema de cache conectado al motor web.",
        flush=True
    )

except Exception as error:
    print(
        f"[ACELERADOR] Cache no disponible. "
        f"Continuando sin cache: {error}",
        flush=True
    )

# ============================================================
# 5. PUERTO DE RENDER
# ============================================================

def obtener_puerto():
    try:
        return int(
            os.environ.get("PORT", "10000")
        )
    except (TypeError, ValueError):
        print(
            "[ACELERADOR] PORT inválido. "
            "Utilizando 10000.",
            flush=True
        )
        return 10000


# ============================================================
# 6. ARRANQUE
# ============================================================

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
