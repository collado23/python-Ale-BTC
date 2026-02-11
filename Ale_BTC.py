import os 
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === PARÁMETROS DE PRECISIÓN ===
espera_segundos = 14
palanca = 10
ganancia_neta_ale = 0.50 
comision = 0.20
meta_bruta = ganancia_neta_ale + comision # 0.70% ROI para ganar
archivo_memoria = "memoria_quantum.txt"

# === ESTADO ===
capital_base = 30.00
ganancia_hoy = 0.0
perdida_hoy = 0.0
contador_ops = 0
en_operacion = False

def registrar(tipo, msg, valor=0):
    global contador_ops, ganancia_hoy, perdida_hoy
    ts = datetime.now().strftime('%H:%M:%S')
    with open(archivo_memoria, "a") as f:
        f.write(f"[{ts}] {tipo} | {msg}\n")
    if tipo == "CIERRE":
        contador_ops += 1
        if valor > 0: ganancia_hoy += valor
        else: perdida_hoy += abs(valor)

print("🚀 IA QUANTUM: MODO LECTURA DE VELAS ACTIVADO")

while True:
    try:
        # 1. ANÁLISIS DE LA VELA ACTUAL Y ANTERIORES
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=5)
        
        # Vela actual (en formación)
        v_actual_open = float(klines[-1][1])
        v_actual_last = float(klines[-1][4])
        
        # Velas cerradas para tendencia
        v1_close = float(klines[-2][4])
        v1_open = float(klines[-2][1])
        
        # BTC para confirmar dirección
        p_btc = float(client.get_symbol_ticker(symbol="BTCUSDT")['price'])
        
        neto_total = ganancia_hoy - perdida_hoy

        # 2. TABLERO DE MANDO
        print(f"\n🔱 VELAS | SOL: ${v_actual_last:.2f} | BTC: ${p_btc:.0f}")
        print(f"💰 NETO: ${neto_total:.2f} | OPS: {contador_ops}/20")
        print(f"🕯️ VELA ACTUAL: {'SUBIENDO 🟢' if v_actual_last > v_actual_open else 'BAJANDO 🔴'}")
        print("-" * 45)

        if not en_operacion:
            # LÓGICA DE ANTICIPACIÓN
            # Entra LONG si la actual supera el cierre anterior y es verde
            if v_actual_last > v_actual_open and v_actual_last > v1_close:
                en_operacion = True
                p_entrada = v_actual_last
                tipo_op = "LONG 🟢"
                registrar("ENTRADA", f"LONG Anticipado a ${v_actual_last} (Fuerza alcista)")
            
            # Entra SHORT si la actual rompe el mínimo anterior y es roja
            elif v_actual_last < v_actual_open and v_actual_last < v1_close:
                en_operacion = True
                p_entrada = v_actual_last
                tipo_op = "SHORT 🔴"
                registrar("ENTRADA", f"SHORT Anticipado a ${v_actual_last} (Fuerza bajista)")
        
        else:
            # GESTIÓN DE SALIDA (Ametralladora 0.5% Neto)
            diff = ((v_actual_last - p_entrada) / p_entrada) if "LONG" in tipo_op else ((p_entrada - v_actual_last) / p_entrada)
            roi_neto = (diff * 100 * palanca) - comision
            
            if roi_neto >= ganancia_neta_ale or roi_neto <= -0.7:
                res = (capital_base * (roi_neto / 100))
                registrar("CIERRE", f"{tipo_op} ROI: {roi_neto:.2f}%", res)
                en_operacion = False

        time.sleep(espera_segundos)
    except:
        time.sleep(5)
