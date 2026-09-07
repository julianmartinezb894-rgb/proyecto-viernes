# FILE: acelerador.py
# VIERNES 2.0 — Arrancador principal de Render
#
# OBJETIVO:
# 1. Importar la aplicación Flask desde app.py.
# 2. Mantener el proceso principal vivo.
# 3. Utilizar el puerto proporcionado por Render.
# 4. NO ejecutar todavía el sistema de marketing.
#
# NOTA:
# El marketing se volverá a conectar después de confirmar que
# el servidor permanece estable. No mezclamos ambos problemas.

import os
from app import app


def obtener_puerto():
    """Obtiene el puerto asignado por Render."""
    try:
        return int(os.environ.get("PORT", "10000"))
    except (TypeError, ValueError):
        print(
            "[VIERNES] PORT inválido. Utilizando puerto 10000.",
            flush=True
        )
        return 10000


def iniciar_servidor():
    """Inicia el servidor Flask de VIERNES."""
    puerto = obtener_puerto()

    print(
        f"[VIERNES] Iniciando servidor en 0.0.0.0:{puerto}",
        flush=True
    )

    app.run(
        host="0.0.0.0",
        port=puerto,
        threaded=True
    )


if __name__ == "__main__":
    iniciar_servidor()
