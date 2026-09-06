import requests
import time

# CONFIGURACIÓN CRÍTICA COMERCIAL
# Tu endpoint real en el proxy de RapidAPI
RAPIDAPI_URL = "https://rapidapi.com" 

# REGLA DE ORO: Reemplaza esto con tu clave "X-RapidAPI-Key" real de RapidAPI Studio
RAPIDAPI_KEY = "TU_X_RAPIDAPI_KEY_AQUÍ" 

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "://rapidapi.com",
    "Content-Type": "application/json"
}

payload = {
    "query": "solana whale movements 2026"  # Simulación de consulta de un bot cliente
}

def forzar_dilucion_latencia():
    print("[VIERNES - OFENSIVA] Iniciando ráfaga de choque a través del Proxy de RapidAPI...", flush=True)
    
    # Forzamos 5 llamadas consecutivas a través de RapidAPI para alterar el algoritmo
    for i in range(1, 6):
        try:
            inicio = time.time()
            response = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=15)
            latencia_real = time.time() - inicio
            
            if response.status_code == 200:
                print(f" -> Inyección {i}/5 exitosa por Proxy | Latencia: {latencia_real:.2f}s | Status: 200", flush=True)
            else:
                print(f" -> Alerta en Inyección {i}/5 | Código RapidAPI: {response.status_code}", flush=True)
        
        except Exception as e:
            print(f" -> Error de conexión en ráfaga {i}: {e}", flush=True)
        
        time.sleep(2)  # Pausa técnica anti-bloqueo

if __name__ == "__main__":
    forzar_dilucion_latencia()
