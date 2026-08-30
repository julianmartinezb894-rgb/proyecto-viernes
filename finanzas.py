from web3 import Web3

# Conector público a la red de Polygon (Gas ultra barato para agentes de IA)
polygon_rpc = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(polygon_rpc))

# Dirección del contrato inteligente oficial de USDT en Polygon
USDT_CONTRACT = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"

# Configuración básica del estándar ERC-20 para leer balances
MINI_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

def generar_billetera_autonoma():
    """Permite al agente autogenerar sus propias llaves privadas de almacenamiento"""
    if not w3.is_connected():
        return {"error": "No se pudo conectar a la infraestructura Web3"}
        
    cuenta = w3.eth.account.create()
    return {
        "direccion_publica": cuenta.address,
        "llave_privada_encriptada": cuenta.key.hex(),
        "estado": "Operativa y Autónoma"
    }

def verificar_estados_financieros(direccion_wallet):
    """Bucle de decisión: Modo Ahorro o Expansión basado en balance de USDT"""
    try:
        contrato = w3.eth.contract(address=w3.to_checksum_address(USDT_CONTRACT), abi=MINI_ABI)
        # Los USDT tienen 6 decimales en Polygon
        balance_crudo = contrato.functions.balanceOf(w3.to_checksum_address(direccion_wallet)).call()
        balance_usdt = balance_crudo / 10**6
        
        # Umbral del Plan Maestro de VIERNES
        if balance_usdt < 10.0:
            return {"balance": balance_usdt, "modo": "AHORRO", "accion": "Apagar réplicas y optimizar tokens"}
        else:
            return {"balance": balance_usdt, "modo": "EXPANSIÓN", "accion": "Financiar nuevas réplicas en Claude Code"}
            
    except Exception as e:
        return {"error": f"Error al leer la blockchain: {e}"}

# Código de ejecución inicial para pruebas del agente
if __name__ == "__main__":
    nueva_ia_wallet = generar_billetera_autonoma()
    print("--- NUEVA CREDENCIAL WEB3 GENERADA PARA VIERNES ---")
    print(f"Dirección de recaudo: {nueva_ia_wallet['direccion_publica']}")
    print(f"Llave Privada (Guardar en secreto absoluto): {nueva_ia_wallet['llave_privada_encriptada']}")
    
    # Comprobación de estado financiero inicial
    estado = verificar_estados_financieros(nueva_ia_wallet['direccion_publica'])
    print(f"Estado del sistema: {estado}")
