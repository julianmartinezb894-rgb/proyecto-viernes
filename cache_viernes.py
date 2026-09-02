# FILE: cache_viernes.py
# OBJETIVO: Acelerar las respuestas de VIERNES por debajo de los 3 segundos
# REGLA DE SEGURIDAD: Archivo complementario totalmente nuevo e independiente.

import time

# Base de datos en memoria ultrarrápida para almacenar JSONs ya extraídos
ALMACEN_OPTIMIZADO = {}

def obtener_datos_rapidos(keyword):
    """
    Busca de forma inmediata en el caché interno para responder en milisegundos,
    evitando que las IA cancelen la suscripción por timeout de 36 segundos.
    """
    ahora = time.time()
    if keyword in ALMACEN_OPTIMIZADO:
        registro = ALMACEN_OPTIMIZADO[keyword]
        # Si la información tiene menos de 1 hora de antigüedad, se entrega al instante
        if ahora - registro["timestamp"] < 3600:
            print(f"[CACHE] Entrega instantánea para el término: '{keyword}'")
            return registro["json_data"]
    return None

def guardar_datos_rapidos(keyword, json_data):
    """Guarda los datos extraídos para acelerar la siguiente consulta del mercado."""
    ALMACEN_OPTIMIZADO[keyword] = {
        "json_data": json_data,
        "timestamp": time.time()
    }
