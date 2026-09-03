# FILE: acelerador.py
# OBJETIVO: Enlazar el caché de forma dinámica e inyectar la ruta de salud sin modificar app.py
# REGLA DE SEGURIDAD: Respeta al 100% la regla de congelación absoluta de archivos base.

import sys
from cache_viernes import obtener_datos_rapidos, guardar_datos_rapidos

print("[ACELERADOR] Iniciando inyección dinámica de velocidad y salud en memoria...")

# 1. Forzar la carga inicial de tu aplicación web congelada
try:
    import app as app_original
except Exception as e:
    print(f"[!] Error al precargar app.py: {e}")
    sys.exit(1)

# =====================================================================
# NUEVA INYECCIÓN: RUTA DE SALUD EN RAM PARA EVITAR COLD START (CRON-JOB)
# =====================================================================
if hasattr(app_original, 'app'):
    @app_original.app.route('/despertar', methods=['GET'])
    def despertar_sistema():
        """Ruta limpia para responder al ping externo sin activar el scraper."""
        return {"status": "online", "message": "VIERNES activo y operativo"}, 200
    print("[✓] Inyección de ruta /despertar completada con éxito.")
else:
    print("[!] Error crítico: No se encontró la instancia de Flask 'app' en app.py.")

# 2. Resguardar la función original del scraper lento de 36 segundos
if hasattr(app_original, 'scraping_alternativo'):
    funcion_lenta_original = app_original.scraping_alternativo
    
    # 3. Diseñar la nueva ruta híbrida ultrarrápida
    def ruta_hibrida_acelerada(keyword, *args, **kwargs):
        # Intenta responder en milisegundos si los datos ya existen
        datos_en_cache = obtener_datos_rapidos(keyword)
        if datos_en_cache is not None:
            return datos_en_cache
            
        # Si no existen, ejecuta el scraper lento una sola vez
        print(f"[ACELERADOR] Término nuevo '{keyword}'. Ejecutando extractor base...")
        resultado_json = funcion_lenta_original(keyword, *args, **kwargs)
        
        # Guarda el resultado para que la siguiente llamada sea instantánea
        guardar_datos_rapidos(keyword, resultado_json)
        return resultado_json

    # 4. Inyectar la velocidad directamente en la memoria del servidor de Flask
    app_original.scraping_alternativo = ruta_hibrida_acelerada
    print("[✓] Inyección de velocidad completada. El endpoint ahora corre sobre caché.")
else:
    print("[!] Advertencia: No se detectó 'scraping_alternativo' en app.py. Modo pasivo activo.")

# =====================================================================
# ACTIVACIÓN DEL ORQUESTADOR AUTÓNOMO (NÚCLEO) AL ARRANCAR EL SERVIDOR
# =====================================================================
try:
    from nucleo_autonomo import iniciar_orquestador_en_segundo_plano
    iniciar_orquestador_en_segundo_plano()
except Exception as e:
    print(f"[!] Error al encender el motor del Núcleo Autónomo: {e}")

# 5. Cederle el control a la aplicación de Flask para que Render levante el servicio web
if __name__ == "__main__":
    if hasattr(app_original, 'app'):
        app_original.app.run(host="0.0.0.0", port=10000)
