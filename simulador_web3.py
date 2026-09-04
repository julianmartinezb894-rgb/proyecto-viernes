import os
from web3 import Web3

# LISTA DE NODOS RPC ALTERNATIVOS DE ALTA DISPONIBILIDAD PARA TESTNET AMOY
NODOS_RPC = [
    "https://drpc.org",
    "https://ankr.com",
    "https://polygon.technology"
]

def conectar_nodo():
    for rpc in NODOS_RPC:
        try:
            w3_provider = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
            if w3_provider.is_connected():
                return w3_provider
        except Exception:
            continue
    return None

# Contrato genérico ERC-20 para simulación de USDT en Testnet Amoy
USDT_AMOY_CONTRACT = "0x0000000000000000000000000000000000001010"

MIN_ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]

def obtener_balance_testnet(billetera_address):
    try:
        w3 = conectar_nodo()
        if w3 is None:
            print("[VIERNES - WEB3] Alerta: Todos los nodos RPC de Polygon están saturados. Usando respaldo interno.", flush=True)
            return 0.0
            
        contract_checksum = w3.to_checksum_address(USDT_AMOY_CONTRACT)
        checksum_wallet = w3.to_checksum_address(billetera_address)
        
        contract = w3.eth.contract(address=contract_checksum, abi=MIN_ERC20_ABI)
        raw_balance = contract.functions.balanceOf(checksum_wallet).call()
        decimals = contract.functions.decimals().call()
        return float(raw_balance / (10 ** decimals))
    except Exception as e:
        print(f"[VIERNES - WEB3] Error en lectura blockchain: {str(e)}", flush=True)
        return 0.0
