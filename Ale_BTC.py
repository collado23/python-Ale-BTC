import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN UNICA ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === ADN CAJA 1 (Ametralladora 14s) ===
espera_segundos = 14
palanca = 10
objetivo_neto = 0.50 
comision = 0.20

# === MEMORIA DE CAJA ===
capital_base = 30.00
ganado = 0.0
perdido = 0.0
contador_ops = 0
en_operacion = False

print("🔱 ALE IA QUANTUM - CAJA 1 INICIADA - SCANNER PARA FOTO")

while True:
    try:
        # 1. ESCANEO DE DATOS (Electricidad y Velas)
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=50)
        
        # Cálculos Técnicos
        cierres = [float(k[4]) for k in klines]
        ema = sum(cierres) / 50
        dist_x = abs(((ema - sol) / sol) * 100)
        # DX: Diferencia entre el punto más alto y el más bajo de las últimas 14 velas
        dx = round(((max(cierres[-14:]) - min(cierres[-14:])) / ema * 1000), 2)
        
        # Sentimiento de Vela (Color)
        v_actual_open = float(klines[-1][1])
        v_actual_color = "VERDE 🟢" if sol > v_actual_open else "ROJA 🔴"
        v_ant_color = "VERDE 🟢" if float(klines[-2][4]) > float(klines[-2][1]) else "ROJA 🔴"
        
        neto_total = ganado - perdido

        # --- 📊 TABLERO PARA FOTO (Todo en uno) ---
        print("\n" + "═"*60)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')} | CAJA 1")
        print(f"💰 NETO: ${neto_total:.2f} | CAP. REAL: ${capital_base + neto_total:.2f}")
        print(f"✅ GAN: +${ganado:.2f} | ❌ PERD: -${perdido:.2f} | 🔢 OPS: {contador_ops}")
        print("-" * 60)
        print(f"⚡ ELECTRICIDAD (DX): {dx} {'🔥 FUERTE' if dx >= 20 else '❄️ DÉBIL'}")
        print(f"📏 DISTANCIA X: {dist_x:.2f}%")
        print(f"🕯️ VELAS: [Anterior: {v_ant_color}] -> [Actual: {v_actual_color}]")
        print(f"📈 PRECIO SOL: ${sol:.2f}")
        print("═"*60)

        # 2. GATILLO (Lógica de entrada)
        if not en_operacion:
            # Solo entra si el DX tiene fuerza (>20) y hay distancia
            if dx >= 20 and dist_x >= 0.55:
                # Confirmación de tendencia
                if sol > v_actual_open and v_ant_color == "VERDE 🟢":
                    en_operacion = True
                    p_entrada = sol
                    tipo_op = "LONG 🟢"
                    print(f"🚀 DISPARO COMPRA (LONG) a ${sol}")
                elif sol < v_actual_open and v_ant_color == "ROJA 🔴":
                    en_operacion = True
                    p_entrada = sol
                    tipo_op = "SHORT 🔴"
                    print(f"🚀 DISPARO VENTA (SHORT) a ${sol}")
        
        else:
            # 3. GESTIÓN DE SALIDA (0.5% neto + comisión)
            diff = ((sol - p_entrada) / p_entrada) if "LONG" in tipo_op else ((p_entrada - sol) / p_entrada)
            roi_neto = (diff * 100 * palanca) - comision
            
            if roi_neto >= objetivo_neto or roi_neto <= -0.7:
                resultado = (capital_base * (roi_neto / 100))
                if resultado > 0: ganado += resultado
                else: perdido += abs(resultado)
                contador_ops += 1
                en_operacion = False
                print(f"🎯 COBRADO: {roi_neto:.2f}% NETO")

        time.sleep(espera_segundos)
    except Exception as e:
        time.sleep(10)
