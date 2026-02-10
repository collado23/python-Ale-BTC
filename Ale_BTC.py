import os
import time
from datetime import datetime
from binance.client import Client

# === CONFIGURACIÓN ===
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
client = Client(API_KEY, API_SECRET)

# === PARÁMETROS MAESTROS AJUSTADOS ===
espera_segundos = 14        # <--- Subido a 14 como pediste
distancia_x_gatillo = 2.0   
dx_minimo = 25              
dx_maximo = 65              
objetivo_neto = 1.5         
palanca = 10
archivo_memoria = "memoria_quantum.txt"

# === ESTADO DE CAJA ===
capital_base = 30.00
ganancia_hoy = 0.0
perdida_hoy = 0.0
contador_ops = 0
en_operacion = False

def escribir_biblioteca(tipo, mensaje, resultado=0):
    global contador_ops, ganancia_hoy, perdida_hoy
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(archivo_memoria, "a") as f:
        f.write(f"[{ts}] {tipo} | {mensaje}\n")
    if tipo == "CIERRE":
        contador_ops += 1
        if resultado > 0: ganancia_hoy += resultado
        else: perdida_hoy += abs(resultado)
        if contador_ops % 20 == 0:
            with open(archivo_memoria, "a") as f:
                f.write(f"\n--- 🧠 ANÁLISIS UNO (OP {contador_ops}) ---\n")

def obtener_datos():
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        precio = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=100)
        cierre = [float(k[4]) for k in klines]
        ema_200 = sum(cierre) / len(cierre)
        dx = round(((max(cierre[-14:]) - min(cierre[-14:])) / ema_200 * 1000), 2)
        v_verdes = sum(1 for i in range(-3, 0) if float(klines[i][4]) > float(klines[i][1]))
        return precio, ema_200, dx, v_verdes, (3 - v_verdes)
    except: return 0, 0, 0, 0, 0

print(f"🚀 MOTOR REINICIADO - FRECUENCIA: {espera_segundos}s")

while True:
    try:
        precio, ema, dx, verdes, rojas = obtener_datos()
        if precio == 0: continue
        
        distancia_x = abs(((ema - precio) / precio) * 100)
        neto_hoy = ganancia_hoy - perdida_hoy

        # --- CUADRO DE MANDO ACTUALIZADO ---
        print("\n" + "═"*55)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💎 PRECIO SOL: ${precio:.2f}")
        print(f"💰 CAP: ${capital_base + neto_hoy:.2f} | 📈 NETO HOY: ${neto_hoy:.2f}")
        print(f"✅ GAN: +${ganancia_hoy:.2f} | ❌ PERD: -${perdida_hoy:.2f}")
        print("-" * 55)
        print(f"📏 DIST X: {distancia_x:.2f}% | ⚡ DX: {dx} | 🕯️ {verdes}V/{rojas}R")
        print(f"🔢 OPS: {contador_ops}/20 (ANÁLISIS UNO)")
        print("═"*55)

        # Lógica de operación (Dual y 1.5% Neto)
        if not en_operacion:
            sentido = "LONG 🟢" if precio < ema else "SHORT 🔴"
            confirmacion = (verdes >= 1 if sentido == "LONG 🟢" else rojas >= 1)
            if distancia_x >= distancia_x_gatillo and dx_minimo <= dx <= dx_maximo and confirmacion:
                en_operacion = True
                precio_entrada = precio
                tipo_op = sentido
                escribir_biblioteca("GATILLO", f"Entrada {sentido} a ${precio}")
        else:
            roi = (((precio - precio_entrada) / precio_entrada) * 100 * palanca) if "LONG" in tipo_op else (((precio_entrada - precio) / precio_entrada) * 100 * palanca)
            roi_neto = roi - 0.20
            if roi_neto >= objetivo_neto or roi_neto <= -0.8:
                escribir_biblioteca("CIERRE", f"{tipo_op} Fin", (capital_base * (roi_neto/100)))
                en_operacion = False

        time.sleep(espera_segundos)
    except Exception as e:
        time.sleep(espera_segundos)
