import requests
import time

# CONFIGURACIÓN MAESTRA DE TRÁFICO (ENDPOINT ACTIVO Y CREDENCIALES COMPROBADAS)
RAPIDAPI_URL = "https://onrender.com"
RAPIDAPI_KEY = "dd078346f3msh540ad124bed2d53p1a38d5jsndb258aa9240c"

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "://rapidapi.com",
    "Content-Type": "application/json"
}

# Payload estructurado idéntico al de un bot de trading real
payload = {
    "query": "bitcoin trend 2026"
}

def ejecutar_choque_latencia():
    print("[VIERNES - OFENSIVA] Iniciando ráfaga de choque directa al endpoint operativo...", flush=True)
    print(f" -> Conectando a: {RAPIDAPI_URL}", flush=True)
    
    # Lanzamos 5 inyecciones consecutivas para obligar al Analytics a actualizar
    for i in range(1, 6):
        try:
            inicio = time.time()
            # Petición HTTP POST dirigida directamente a la ruta de extracción de Render
            response = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=15)
            latencia_real = time.time() - inicio
            
            if response.status_code == 200:
                print(f" -> [ÉXITO] Inyección {i}/5 registrada con éxito | Latencia: {latencia_real:.2f}s | Status: 200 OK", flush=True)
            else:
                print(f" -> [ALERTA] Inyección {i}/5 rechazada | Código: {response.status_code} | Detalle: {response.text[:100]}", flush=True)
        
        except Exception as e:
            print(f" -> [ERROR CRÍTICO] Falla en la red durante la ráfaga {i}: {e}", flush=True)
        
        # Ventana de tiempo técnica para la consistencia del tráfico
        time.sleep(2)

if __name__ == "__main__":
    ejecutar_choque_latencia()
