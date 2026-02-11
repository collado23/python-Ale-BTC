import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN UNICA ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === PARÁMETROS ADN (Ametralladora + Trailing) ===
espera_segundos = 14
palanca = 10
objetivo_minimo_neto = 0.50  # Meta base para activar Trailing
comision = 0.20
trail_distancia = 0.15       # Margen de retroceso para el Trailing

# === CONTADORES DE CAJA 1 (No se borran en el ciclo) ===
capital_base = 30.00
ganado = 0.0
perdido = 0.0
contador_ops = 0
en_operacion = False
max_roi_alcanzado = 0.0

print("🔱 INICIANDO CAJA 1: AMETRALLADORA + TRAILING + SCANNER TÉCNICO")

while True:
    try:
        # 1. ESCANEO TÉCNICO COMPLETO
        ticker_sol = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker_sol['price'])
        ticker_btc = client.get_symbol_ticker(symbol="BTCUSDT")
        btc = float(ticker_btc['price'])
        
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=50)
        cierres = [float(k[4]) for k in klines]
        ema = sum(cierres) / 50
        dist_x = abs(((ema - sol) / sol) * 100)
        dx = round(((max(cierres[-14:]) - min(cierres[-14:])) / ema * 1000), 2)
        
        # Sentimiento de Velas
        v_actual_open = float(klines[-1][1])
        v_actual_color = "VERDE 🟢" if sol > v_actual_open else "ROJA 🔴"
        v_ant_color = "VERDE 🟢" if float(klines[-2][4]) > float(klines[-2][1]) else "ROJA 🔴"
        
        neto_total = ganado - perdido

        # --- 📊 TABLERO INTEGRAL PARA FOTO ---
        print("\n" + "═"*60)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')} | CAJA 1")
        print(f"💰 NETO: ${neto_total:.2f} | CAP. REAL: ${capital_base + neto_total:.2f}")
        print(f"✅ GAN: +${ganado:.2f} | ❌ PERD: -${perdido:.2f} | 🔢 OPS: {contador_ops}")
        print("-" * 60)
        print(f"📈 SOL: ${sol:.2f} | 🍊 BTC: ${btc:.0f}")
        print(f"⚡ ELECTRICIDAD (DX): {dx} | 📏 DISTANCIA X: {dist_x:.2f}%")
        print(f"🕯️ VELAS: [Ant: {v_ant_color}] -> [Hoy: {v_actual_color}]")
        
        if en_operacion:
            # Cálculo de ROI en tiempo real para el Trailing
            diff = ((sol - p_entrada) / p_entrada) if "LONG" in tipo_op else ((p_entrada - sol) / p_entrada)
            roi_neto = (diff * 100 * palanca) - comision
            if roi_neto > max_roi_alcanzado: max_roi_alcanzado = roi_neto
            
            print(f"🏃 OPERANDO: {tipo_op} | ROI: {roi_neto:.2f}%")
            print(f"🔝 MAX: {max_roi_alcanzado:.2f}% | 🎯 PISO: {max_roi_alcanzado - trail_distancia:.2f}%")
        else:
            print("📡 ESTADO: ESCANEANDO OPORTUNIDAD...")
        print("═"*60)

        # 2. GATILLO DE ENTRADA (Filtros bajos para acción inmediata)
        if not en_operacion:
            # Si hay un mínimo de movimiento (DX > 1.5) y color de vela
            if dx >= 1.5 and dist_x >= 0.05:
                p_entrada = sol
                en_operacion = True
                max_roi_alcanzado = -99.0
                tipo_op = "LONG 🟢" if sol > v_actual_open else "SHORT 🔴"
                print(f"🚀 DISPARO {tipo_op} EN ${sol}")
        
        else:
            # 3. GESTIÓN DE SALIDA (Trailing Stop)
            # A. Cierre por Trailing (si ya pasó la meta del 0.5%)
            if max_roi_alcanzado >= objetivo_minimo_neto:
                if roi_neto <= (max_roi_alcanzado - trail_distancia):
                    res = (capital_base * (roi_neto / 100))
                    if res > 0: ganado += res
                    else: perdido += abs(res)
                    contador_ops += 1
                    en_operacion = False
                    print(f"🎯 TRAILING STOP COBRADO: {roi_neto:.2f}%")
            
            # B. Stop Loss de seguridad
            elif roi_neto <= -0.65:
                res = (capital_base * (roi_neto / 100))
                perdido += abs(res)
                contador_ops += 1
                en_operacion = False
                print(f"🛡️ STOP LOSS CERRADO: {roi_neto:.2f}%")

        time.sleep(espera_segundos)
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(10)
