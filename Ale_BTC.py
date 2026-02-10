import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN SEGURA ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === ADN AMETRALLADORA (Ajustado para 1000 operaciones) ===
espera_segundos = 14
distancia_x_gatillo = 0.35   # <--- BAJÍSIMO: Dispara con un suspiro del mercado
palanca = 10
ganancia_neta_ale = 0.50     # Tu ganancia limpia
comision_binance = 0.20      # Lo que cubrimos de costos
meta_bruta = ganancia_neta_ale + comision_binance # El bot busca 0.70% total

archivo_memoria = "memoria_quantum.txt"

# === ESTADO DE CAJA ===
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
        if contador_ops % 20 == 0:
            with open(archivo_memoria, "a") as f:
                f.write(f"\n--- 🧠 ANÁLISIS UNO (OP {contador_ops}) ---\n")

print("🔥 AMETRALLADORA CARGADA - GATILLO ULTRA-FÁCIL ACTIVADO")

while True:
    try:
        # Precios en tiempo real
        sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        btc = float(client.get_symbol_ticker(symbol="BTCUSDT")['price'])
        
        # Análisis de Media rápido (50 periodos para más acción)
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=50)
        ema = sum([float(k[4]) for k in klines]) / 50
        dist_x = abs(((ema - sol) / sol) * 100)
        
        neto_real = ganancia_hoy - perdida_hoy

        # --- TABLERO EN PANTALLA ---
        print("\n" + "═"*50)
        print(f"🔱 ALE IA AMETRALLADORA | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💎 SOL: ${sol:.2f} | 🍊 BTC: ${btc:.0f}")
        print(f"💰 CAP: ${capital_base + neto_real:.2f} | 📈 NETO: ${neto_real:.2f}")
        print(f"✅ GAN: +${ganancia_hoy:.2f} | ❌ PERD: -${perdida_hoy:.2f}")
        print(f"🔢 OPS: {contador_ops}/20 | 📏 DIST X: {dist_x:.3f}%")
        print("═"*50)

        if not en_operacion:
            # DISPARO INMEDIATO: Si hay mínima distancia, entra.
            if dist_x >= distancia_x_gatillo:
                en_operacion = True
                p_entrada = sol
                tipo_op = "LONG 🟢" if sol < ema else "SHORT 🔴"
                registrar("ENTRADA", f"{tipo_op} en ${sol} (BTC: ${btc})")
        else:
            # GESTIÓN DE SALIDA RELÁMPAGO
            diff = ((sol - p_entrada) / p_entrada) if "LONG" in tipo_op else ((p_entrada - sol) / p_entrada)
            roi_neto = (diff * 100 * palanca) - comision_binance
            
            # Cierre rápido: 0.5% neto o -0.6% de protección
            if roi_neto >= ganancia_neta_ale or roi_neto <= -0.6:
                res = (capital_base * (roi_neto / 100))
                registrar("CIERRE", f"{tipo_op} ROI: {roi_neto:.2f}%", res)
                en_operacion = False

        time.sleep(espera_segundos)
    except:
        time.sleep(espera_segundos)
