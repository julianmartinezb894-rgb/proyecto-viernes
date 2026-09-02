# FILE: cuotas.py
# OBJETIVO: Monitorear el consumo para evitar bloqueos y optimizar ganancias.

import time

# Base de datos temporal en memoria para registrar accesos
REGISTRO_CLIENTES = {}

def verificar_limite_cliente(cliente_id, limite_gratis=5):
    """
    Monitorea de forma independiente el tráfico para asegurar 
    que los bots de prueba no saturen el backend de Render.
    """
    ahora = time.time()
    
    if cliente_id not in REGISTRO_CLIENTES:
        REGISTRO_CLIENTES[cliente_id] = {"peticiones": 1, "primer_acceso": ahora}
        return True
        
    datos = REGISTRO_CLIENTES[cliente_id]
    
    # Resetear cuota mensual/diaria si pasó el tiempo (ej. 24 horas)
    if ahora - datos["primer_acceso"] > 86400:
        datos["peticiones"] = 1
        datos["primer_acceso"] = ahora
        return True
        
    if datos["peticiones"] < limite_gratis:
        datos["peticiones"] += 1
        return True
        
    return False
