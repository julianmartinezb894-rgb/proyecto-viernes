import requests
import time

# ==========================================
# CONFIGURACIÓN DE CHOQUE (PROXY COMERCIAL)
# ==========================================
RAPIDAPI_URL = "https://onrender.com"
RAPIDAPI_KEY = "dd078346f3msh540ad124bed2d53p1a38d5jsndb258aa9240c"

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "://rapidapi.com",
    "Content-Type": "application/json"
}

payload = {
    "query": "bitcoin realtime market sentiment 2026"
}

def forzar_dilucion_promedio():
    print("[VIERNES - OFENSIVA] Lanzando ráfaga de choque para triturar la latencia fantasma...", flush=True)
    
    # Ejecutamos 5 llamadas automáticas seguidas a través del proxy
    for i in range(1, 6):
        try:
            inicio = time.time()
            response = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=15)
            latencia_real = time.time() - inicio
            
            if response.status_code == 200:
                print(f" -> [ÉXITO] Impacto {i}/5 | Latencia Real: {latencia_real:.2f}s | Status: 200 OK", flush=True)
            else:
                print(f" -> [ALERTA] Impacto {i}/5 devolvió código: {response.status_code}", flush=True)
        except Exception as e:
            print(f" -> [ERROR DE RED] Falla en la inyección {i}: {e}", flush=True)
        
        time.sleep(2) # Ventana técnica de seguridad

if __name__ == "__main__":
    forzar_dilucion_promedio()
