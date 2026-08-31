import os
import shutil
from finanzas import verificar_balance_usdt

# REGLA DE ORO DE VIERNES: Solo autorreplicarse si el negocio genera dinero real.
MINIMO_GANANCIAS_USDT = 50.0

def verificar_rentabilidad_y_replicar():
    print("[VIERNES] Iniciando auditoría en módulo replicacion_rentable.py...")
    
    # Conectamos con el módulo financiero para ver cuánto dinero tenemos ahorrado
    balance_actual = verificar_balance_usdt()
    print(f"[VIERNES] Balance verificado en la red Polygon: {balance_actual} USDT")
    
    # CANDADO FINANCIERO AUTOMÁTICO
    if balance_actual < MINIMO_GANANCIAS_USDT:
        print(f"[VIERNES] ALERTA DE SEGURIDAD: Sistema en modo ahorro o no rentable.")
        print(f"[VIERNES] Replicación ABORTADA. Motivo: Balance inferior a {MINIMO_GANANCIAS_USDT} USDT.")
        return False
        
    print("[VIERNES] ¡VALIDACIÓN EXITOSA! El sistema es rentable. Iniciando proceso de autorreplicación...")
    
    archivos_esenciales = ["app.py", "finanzas.py", "requirements.txt"]
    carpeta_clon = "viernes_nodo_seguro"
    
    try:
        if not os.path.exists(carpeta_clon):
            os.makedirs(carpeta_clon)
            
        for archivo in archivos_esenciales:
            if os.path.exists(archivo):
                shutil.copy(archivo, os.path.join(carpeta_clon, archivo))
                print(f"[VIERNES] Archivo vital empaquetado con éxito: {archivo}")
                
        print("[VIERNES] Clonación local completada de manera aislada en 'viernes_nodo_seguro'.")
        return True
        
    except Exception as e:
        print(f"[VIERNES] Error crítico durante el proceso de replicación: {str(e)}")
        return False

if __name__ == "__main__":
    verificar_rentabilidad_y_replicar()

