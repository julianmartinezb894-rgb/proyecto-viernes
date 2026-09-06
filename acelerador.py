import os
import time
import threading
import subprocess
from flask import Flask, jsonify

# ==========================================
# REGLA DE CONGELACIÓN: IMPORTACIÓN COMPATIBLE
# ==========================================
from app import app, scraping_alternativo

@app.route('/despertar', methods=['GET', 'HEAD'])
def despertar_ram():
    """Ruta anti-suspensión inyectada para responder de forma ultra-rápida"""
    return jsonify({"status": "despierto", "latencia_interna": "optima"}), 200

# ==========================================
# ORQUESTACIÓN ASÍNCRONA COMERCIAL DE TRACCIÓN
# ==========================================
def lanzar_brazo_marketing_seguro():
    """Hilo secundario que obliga a ejecutar el módulo de marketing al arrancar"""
    print("[VIERNES - DISPARADOR] Levantando el motor comercial automatizado...", flush=True)
    # Esperamos 5 segundos para asegurar que el servidor Flask web esté online
    time.sleep(5)
    try:
        print("[VIERNES - DISPARADOR] Ejecutando de forma nativa auto_marketing.py...", flush=True)
        # Ejecuta de forma directa el script de marketing usando el intérprete de Python del contenedor
        subprocess.run(["python", "auto_marketing.py"], check=True)
    except Exception as e:
        print(f"[VIERNES - ERROR COMERCIAL] Error al disparar el script de marketing: {e}", flush=True)

def lanzar_orquestador_seguro():
    """Hilo secundario para ejecutar los ciclos sin congelar el servidor Flask"""
    try:
        from nucleo_autonomo import ejecutar_ciclo_agentico
        print("[VIERNES - ENLACE] Puente de compatibilidad agéntica enlazado con éxito.", flush=True)
        ejecutar_ciclo_agentico()
    except Exception as e:
        print(f"[VIERNES - ERROR CRÍTICO] Error al levantar el núcleo asíncrono: {e}", flush=True)

# Inicialización segura de hilos paralelos antes de arrancar la aplicación web
hilo_marketing = threading.Thread(target=lanzar_brazo_marketing_seguro, daemon=True)
hilo_marketing.start()

hilo_nucleo = threading.Thread(target=lanzar_orquestador_seguro, daemon=True)
hilo_nucleo.start()
print("[V] Hilos asíncronos del ecosistema desplegados correctamente.", flush=True)

# ==========================================
# ARRANQUE DE PRODUCCIÓN COMPATIBLE CON RENDER
# ==========================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"[ACELERADOR] Servidor listo. Escuchando peticiones en el puerto: {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False)
