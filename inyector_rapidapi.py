import requests
import time

# CONFIGURACIÓN MAESTRA DE LA OFENSIVA
RAPIDAPI_URL = "https://rapidapi.com"
RAPIDAPI_KEY = "dd078346f3msh540ad124bed2d53p1a38d5jsndb258aa9240c"

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "://rapidapi.com",
    "Content-Type": "application/json"
}

payload = {
    "query": "solana whale movements 2026"
}

def ejecutar_choque_latencia():
    print("[VIERNES - PROXY OVERRIDE] Iniciando ráfaga de choque en el Proxy comercial...", flush=True)
    
    # Lanzamos 5 peticiones rápidas consecutivas para forzar al Analytics de RapidAPI
    for i in range(1, 6):
        try:
            inicio = time.time()
            response = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=15)
            latencia_real = time.time() - inicio
            
            if response.status_code == 200:
                print(f" -> [ÉXITO] Inyección {i}/5 registrada por Proxy | Latencia: {latencia_real:.2f}s | Status: 200 OK", flush=True)
            else:
                print(f" -> [ALERTA] Inyección {i}/5 rechazada | Código Proxy: {response.status_code} | Respuesta: {response.text[:100]}", flush=True)
        
        except Exception as e:
            print(f" -> [ERROR CRÍTICO] Falla de conexión en ráfaga {i}: {e}", flush=True)
        
        time.sleep(2)  # Ventana técnica anti-spam

if __name__ == "__main__":
    ejecutar_choque_latencia()
