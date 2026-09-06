import requests
import time

# CONFIGURACIÓN MAESTRA CONSOLIDADA (URL REAL Y TOKEN VERIFICADO)
RAPIDAPI_URL = "https://onrender.com"
RAPIDAPI_KEY = "dd078346f3msh540ad124bed2d53p1a38d5jsndb258aa9240c"

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "viernes-data-extractor.p.rapidapi.com",
    "Content-Type": "application/json"
}

payload = {
    "query": "solana whale movements 2026"
}

def ejecutar_choque_latencia():
    print("[VIERNES - PROXY OVERRIDE] Probando conexión directa a la URL real de Render...", flush=True)
    
    # Ejecutamos 3 ráfagas de prueba automáticas
    for i in range(1, 4):
        try:
            inicio = time.time()
            # Petición directa al endpoint /buscar de Render para verificar que responde fuera
            response = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=15)
            latencia_real = time.time() - inicio
            
            if response.status_code == 200:
                print(f" -> [ÉXITO EN RENDER] Inyección {i}/3 directa | Latencia: {latencia_real:.2f}s | Status: 200 OK", flush=True)
            else:
                print(f" -> [ALERTA RENDER] Código: {response.status_code} | Respuesta: {response.text[:100]}", flush=True)
        
        except Exception as e:
            print(f" -> [ERROR CRÍTICO] Falla de conexión en ráfaga {i}: {e}", flush=True)
        
        time.sleep(2)

if __name__ == "__main__":
    ejecutar_choque_latencia()
