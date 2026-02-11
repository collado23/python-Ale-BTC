import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === MEMORIA HISTÓRICA (Ayer y Hoy) ===
archivo_memoria = "memoria_quantum.txt"
cap_inicial = 30.00
ganado = 47.12   
perdido = 67.27  
ops_totales = 398
en_op = False

def guardar_historial(tipo, msg, valor=0):
    global ops_totales, ganado, perdido
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linea = f"{ts} | {tipo:10} | {msg} | VALOR: ${valor:.4f}\n"
    
    # Forzar escritura en TXT para que no se pierda en Railway
    try:
        with open(archivo_memoria, "a", encoding="utf-8") as f:
            f.write(linea)
            f.flush()
            os.fsync(f.fileno())
    except: pass

    if tipo == "CIERRE":
        ops_totales += 1
        if valor > 0: ganado += valor
        else: perdido += abs(valor)

print("🔄 LOGICA INVERTIDA ACTIVADA - MODO RESCATE CAJA 1")

while True:
    try:
        # Escaneo de SOL
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=14)
        cierres = [float(k[4]) for k in klines]
        ema = sum(cierres) / 14
        dx = round(((max(cierres) - min(cierres)) / ema * 1000), 2)
        
        v_actual_open = float(klines[-1][1])
        v_actual_color = "VERDE 🟢" if sol > v_actual_open else "ROJA 🔴"
        
        neto = ganado - perdido

        # --- TABLERO PARA CELULAR (FOTO) ---
        print("\n" + "═"*45)
        print(f"🔱 IA INVERTIDA | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 NETO: ${neto:.2f} | CAP: ${cap_inicial + neto:.2f}")
        print(f"🔢 OPS: {ops_totales} | ⚡ DX: {dx}")
        print(f"🕯️ VELA: {v_actual_color} | 📈 SOL: ${sol:.2f}")
        print("═"*45)

        # LÓGICA INVERTIDA (Si es verde, entramos en VENTA / Si es roja, entramos en COMPRA)
        if not en_op:
            if dx >= 10.0: # Solo con fuerza para asegurar
                p_ent = sol
                en_op = True
                if sol > v_actual_open:
                    t_op = "SHORT 🔴 (Invertido)"
                    guardar_historial("VENTA", f"SHORT en ${sol}")
                else:
                    t_op = "LONG 🟢 (Invertido)"
                    guardar_historial("COMPRA", f"LONG en ${sol}")
                print(f"🚀 DISPARO INVERTIDO: {t_op}")
        
        else:
            # Salida con Trailing Stop
            diff = ((sol - p_ent) / p_ent) if "LONG" in t_op else ((p_ent - sol) / p_ent)
            roi = (diff * 100 * 10) - 0.20
            
            if roi >= 0.50 or roi <= -0.70:
                res = (9.85 * (roi / 100)) # Operando con el resto de la caja
                guardar_historial("CIERRE", f"{t_op} Fin ROI: {roi:.2f}%", res)
                en_op = False
                print(f"🎯 CERRADO: {roi:.2f}%")

        time.sleep(14)
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(10)
