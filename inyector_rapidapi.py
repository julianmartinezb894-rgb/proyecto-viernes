import os
import time
import threading
import requests
from flask import Flask, jsonify

# ==========================================
# REGLA DE CONGELACIÓN: IMPORTACIÓN COMPATIBLE
# ==========================================
# Importamos el objeto 'app' y las funciones desde el backend base congelado
from app import app, scraping_alternativo

# ==========================================
# INYECCIÓN QUIRÚRGICA EN RAM (SOLUCIÓN 404)
# ==========================================
@app.route('/')
def raiz_puente_rapidapi():
    """
    Inyección dinámica en memoria RAM para rescatar las peticiones base.
    Evita que los validadores de RapidAPI y Render reboten con un código 404.
    """
    return jsonify({"status": "online", "message": "VIERNES Oracle Node Live"}), 200

@app.route('/despertar', methods=['GET', 'HEAD'])
def despertar_ram():
    """Ruta anti-suspensión inyectada para responder de forma ultra-rápida"""
    return jsonify({"status": "despierto", "latencia_interna": "optima"}), 200

# ==========================================
# ORQUESTACIÓN DEL NÚCLEO ASÍNCRONO
# ==========================================
def lanzar_orquestador_seguro():
    """Hilo secundario para ejecutar los ciclos sin congelar el servidor Flask"""
    try:
        # Importación protegida para prevenir el ImportError cíclico destructivo
        from nucleo_autonomo import ejecutar_ciclo_agentico
        print("[VIERNES - ENLACE] Puente de compatibilidad agéntica enlazado con éxito.", flush=True)
        ejecutar_ciclo_agentico()
    except Exception as e:
        print(f"[VIERNES - ERROR CRÍTICO] Error al levantar el núcleo asíncrono: {e}", flush=True)

# Inicialización segura del hilo antes de arrancar la aplicación web
hilo_nucleo = threading.Thread(target=lanzar_orquestador_seguro, daemon=True)
hilo_nucleo.start()
print("[V] Hilo asíncrono del Núcleo Autónomo desplegado correctamente.", flush=True)

# ==========================================
# ARRANQUE DE PRODUCCIÓN COMPATIBLE CON RENDER
# ==========================================
if __name__ == "__main__":
    # Arranca el servidor nativamente en el puerto de red asignado por el contenedor de la nube
    port = int(os.environ.get("PORT", 10000))
    print(f"[ACELERADOR] Servidor listo. Escuchando peticiones en el puerto: {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False)
