import requests
import time

# CONFIGURACIÓN MAESTRA DEFINITIVA (ENDPOINT ACTIVO Y CREDENCIALES REALES)
RAPIDAPI_URL = "https://onrender.com"
RAPIDAPI_KEY = "dd078346f3msh540ad124bed2d53p1a38d5jsndb258aa9240c"

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "://rapidapi.com",
    "Content-Type": "application/json"
}

# Carga de datos de prueba idéntica a la que usaría un bot comercial de criptomonedas
payload = {
    "query": "bitcoin trend 2026"
}

def ejecutar_choque_latencia():
    print("[VIERNES - OFENSIVA] Lanzando ráfagas de choque al endpoint verificado...", flush=True)
    print(f" -> Apuntando a: {RAPIDAPI_URL}", flush=True)
    
    # Forzamos 3 inyecciones seguidas para verificar el comportamiento del puente
    for i in range(1, 4):
        try:
            inicio = time.time()
            # Petición HTTP POST enviando las cabeceras requeridas y el JSON estructurado
            response = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=15)
            latencia_real = time.time() - inicio
            
            if response.status_code == 200:
                print(f" -> [ÉXITO] Inyección {i}/3 completada | Latencia: {latencia_real:.2f}s | Status: 200 OK", flush=True)
            else:
                print(f" -> [ALERTA] Inyección {i}/3 devolvió código: {response.status_code} | Detalle: {response.text[:100]}", flush=True)
        
        except Exception as e:
            print(f" -> [ERROR CRÍTICO] Falla en la conexión de la ráfaga {i}: {e}", flush=True)
        
        # Pausa de seguridad para no saturar las cuotas de red del contenedor
        time.sleep(2)

if __name__ == "__main__":
    ejecutar_choque_latencia()
