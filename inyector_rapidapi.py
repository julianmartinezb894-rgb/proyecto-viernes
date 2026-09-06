import requests
import time

# CONFIGURACIÓN CORREGIDA CON URL REAL DE RENDER
# Forzamos la llamada al proxy apuntando al subdominio verificado por tus logs
RAPIDAPI_URL = "https://onrender.com"
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
    print("[VIERNES - PROXY OVERRIDE] Probando conexión directa a la URL real de Render...", flush=True)
    
    for i in range(1, 4): # Reducido a 3 intentos para probar el puente
        try:
            inicio = time.time()
            # Probamos directo a Render primero para verificar que la ruta /buscar responde externamente
            response = requests.post(RAPIDAPI_URL, json=payload, timeout=15)
            latencia_real = time.time() - inicio
            
            if response.status_code == 200:
                print(f" -> [ÉXITO EN RENDER] Inyección {i}/3 directa | Latencia: {latencia_real:.2f}s | Status: 200 OK", flush=True)
            else:
                print(f" -> [ALERTA RENDER] Código: {response.status_code} | Respuesta: {response.text[:100]}", flush=True)
        
        except Exception as e:
            print(f" -> [ERROR CRÍTICO] Falla de conexión: {e}", flush=True)
        
        time.sleep(2)

if __name__ == "__main__":
    ejecutar_choque_latencia()
