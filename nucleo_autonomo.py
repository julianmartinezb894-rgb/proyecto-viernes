import time
import threading
from app import scraping_alternativo
from finanzas import verificar_estados_financieros, generar_billetera_autonoma
from replicacion_rentable import verificar_rentabilidad_y_replicar

def ciclo_de_vida_autonomo():
    print("[NÚCLEO VIERNES] Inicializando bucle de autonomía total...")
    
    # 1. Asegurar o cargar la identidad financiera Web3 de la IA
    billetera = generar_billetera_autonoma()
    direccion = billetera.get("direccion_publica")
    print(f"[NÚCLEO VIERNES] Identidad Web3 activa. Recaudo en: {direccion}")
    
    while True:
        try:
            print("[NÚCLEO VIERNES] Iniciando ronda de operaciones autónomas...")
            
            # A. Extracción de datos para inteligencia de mercado
            datos_mercado = scraping_alternativo("tendencias desarrollo IA apis B2B")
            
            # B. Consultar el estado financiero de RapidAPI y Polygon
            estado_financiero = verificar_estados_financieros(direccion)
            print(f"[NÚCLEO VIERNES] Auditoría financiera completada: Modo {estado_financiero.get('modo')}")
            
            # C. Intentar la autorreplicación si el balance es óptimo
            if estado_financiero.get('modo') == "EXPANSIÓN":
                exito_replica = verificar_rentabilidad_y_replicar()
                if exito_replica:
                    print("[NÚCLEO VIERNES] Expansión completada. Nuevo nodo activo.")
            
            # El bot se duerme de forma inteligente por 4 horas antes del siguiente ciclo
            print("[NÚCLEO VIERNES] Ciclo finalizado. Entrando en modo de espera...")
            time.sleep(14400)
            
        except Exception as e:
            print(f"[CRÍTICO NÚCLEO] Falla en el bucle autónomo: {e}")
            time.sleep(60) # Espera un minuto antes de reintentar si el sistema parpadea

if __name__ == "__main__":
    # Arranca el hilo de pensamiento independiente de VIERNES
    hilo_autonomo = threading.Thread(target=ciclo_de_vida_autonomo, daemon=True)
    hilo_autonomo.start()
    
    # Mantiene el proceso principal vivo para que el servidor de Render no se apague
    while True:
        time.sleep(1)
