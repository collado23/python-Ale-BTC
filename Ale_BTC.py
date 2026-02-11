import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === PARÁMETROS ===
espera_segundos = 14
palanca = 10
ganancia_neta_ale = 0.50 
comision = 0.20
archivo_memoria = "memoria_quantum.txt"

# === ESTADO ===
capital_base = 30.00
ganancia_hoy = 0.0
perdida_hoy = 0.0
contador_ops = 0
en_operacion = False

def registrar_seguro(tipo, msg, valor=0):
    """Escribe en el txt sin bloquear el programa"""
    global contador_ops, ganancia_hoy, perdida_hoy
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linea = f"[{ts}] {tipo} | {msg}\n"
    
    try:
        # Intentamos escribir el evento
        with open(archivo_memoria, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception as e:
        print(f"⚠️ Error escribiendo TXT: {e}")

    if tipo == "CIERRE":
        contador_ops += 1
        if valor > 0: ganancia_hoy += valor
        else: perdida_hoy += abs(valor)
        
        # Bloque de Análisis cada 20 operaciones
        if contador_ops % 20 == 0:
            resumen = f"\n--- 🧠 ANÁLISIS UNO (OP {contador_ops}) | NETO: ${ganancia_hoy - perdida_hoy:.2f} ---\n"
            try:
                with open(archivo_memoria, "a", encoding="utf-8") as f:
                    f.write(resumen)
            except: pass

print("🚀 IA QUANTUM: LEYENDO VELAS Y ESCRIBIENDO MEMORIA")

while True:
    try:
        # 1. DATOS DE MERCADO
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        p_sol = float(ticker['price'])
        
        # Lectura de velas para el patrón de 3
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=3)
        v_actual_open = float(klines[-1][1])
        v_anterior_close = float(klines[-2][4])
        
        neto_total = ganancia_hoy - perdida_hoy

        # --- TABLERO EN PANTALLA ---
        print("\n" + "═"*50)
        print(f"🔱 ALE IA | SOL: ${p_sol:.2f} | NETO: ${neto_total:.2f}")
        print(f"🕯️ VELA: {'VERDE 🟢' if p_sol > v_actual_open else 'ROJA 🔴'}")
        print(f"🔢 OPS: {contador_ops}/20 (ANÁLISIS UNO)")
        print("═"*50)

        if not en_operacion:
            # ENTRADA: Rompe el máximo anterior (LONG) o el mínimo (SHORT)
            if p_sol > v_actual_open and p_sol > v_anterior_close:
                en_operacion = True
                p_entrada = p_sol
                tipo_op = "LONG 🟢"
                registrar_seguro("ENTRADA", f"LONG a ${p_sol}")
            
            elif p_sol < v_actual_open and p_sol < v_anterior_close:
                en_operacion = True
                p_entrada = p_sol
                tipo_op = "SHORT 🔴"
                registrar_seguro("ENTRADA", f"SHORT a ${p_sol}")
        
        else:
            # SALIDA: Objetivo 0.5% NETO para Ale
            diff = ((p_sol - p_entrada) / p_entrada) if "LONG" in tipo_op else ((p_entrada - p_sol) / p_entrada)
            roi_neto = (diff * 100 * palanca) - comision
            
            if roi_neto >= ganancia_neta_ale or roi_neto <= -0.7:
                res = (capital_base * (roi_neto / 100))
                registrar_seguro("CIERRE", f"{tipo_op} Fin ROI: {roi_neto:.2f}%", res)
                en_operacion = False
                print(f"🎯 OPERACIÓN CERRADA: {roi_neto:.2f}% Neto")

        time.sleep(espera_segundos)

    except Exception as e:
        print(f"⚠️ Error en ciclo: {e}")
        time.sleep(10)
