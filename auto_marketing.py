# FILE: auto_marketing.py
# VIERNES 2.0 — Motor de marketing estable
#
# FASE 1:
# - Elimina la dependencia de Hugging Face.
# - No ejecuta marketing automáticamente al importar.
# - No publica en X ni Reddit.
# - No modifica app.py, finanzas.py, acelerador.py
#   ni nucleo_autonomo.py.
# - Si se llama al ciclo, devuelve False sin tumbar el proceso.
#
# IMPORTANTE:
# Las credenciales se leen desde Render.
# No se guardan tokens ni claves en este archivo.

import logging


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("viernes.auto_marketing")

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )


# ============================================================
# CICLO DE MARKETING
# ============================================================

def ejecutar_ciclo_marketing() -> bool:
    """
    Punto de entrada compatible con el archivo anterior.

    Durante esta fase no ejecuta llamadas externas.
    """

    logger.info(
        "[VIERNES - MARKETING] "
        "Motor de marketing en modo seguro."
    )

    logger.info(
        "[VIERNES - MARKETING] "
        "Proveedor Hugging Face desactivado."
    )

    return False


# ============================================================
# COMPATIBILIDAD CON POSIBLES LLAMADAS DEL ORQUESTADOR
# ============================================================

def ejecutar_ciclo_agentico() -> bool:
    """
    Alias de compatibilidad.
    """

    return ejecutar_ciclo_marketing()


# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================

if __name__ == "__main__":
    ejecutar_ciclo_marketing()
