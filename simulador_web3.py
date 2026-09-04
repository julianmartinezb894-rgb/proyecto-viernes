import os
from web3 import Web3

# RPC Público Estable para Polygon Testnet (Amoy)
RPC_AMOY = "https://polygon.technology"
w3 = Web3(Web3.HTTPProvider(RPC_AMOY))

# Contrato genérico ERC-20 para simulación de USDT en Testnet Amoy
USDT_AMOY_CONTRACT = w3.to_checksum_address("0x0000000000000000000000000000000000001010") 

MIN_ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]

def obtener_balance_testnet(billetera_address):
    try:
        if not w3.is_connected():
            print("[VIERNES - WEB3] Alerta: Falló conexión con nodo RPC de Polygon.", flush=True)
            return 0.0
        checksum_wallet = w3.to_checksum_address(billetera_address)
        contract = w3.eth.contract(address=USDT_AMOY_CONTRACT, abi=MIN_ERC20_ABI)
        raw_balance = contract.functions.balanceOf(checksum_wallet).call()
        decimals = contract.functions.decimals().call()
        return float(raw_balance / (10 ** decimals))
    except Exception as e:
        print(f"[VIERNES - WEB3] Error en lectura blockchain: {str(e)}", flush=True)
        return 0.0
