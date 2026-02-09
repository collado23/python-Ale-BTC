import os, time, pandas as pd, numpy as np
import yfinance as yf
from binance.client import Client

# --- CONEXIÓN ---
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
archivo_memoria = "espejo_cuantico.txt"

# ... (Funciones de ADX y ADN se mantienen igual) ...

def ejecutar_v14_3():
    print("🔱 GLADIADOR V14.3: MONITOR DE TESORO Y PROPORCIÓN")
    en_operacion = False
    p_entrada, elast_entrada, max_roi = 0, 0, 0
    acumulado_hoy = 0.0 # Contador de ganancias del día
    t_stop = 0.4

    while True:
        try:
            k = client.futures_klines(symbol="SOLUSDT", interval='1m', limit=100)
            df = pd.DataFrame(k).astype(float)
            p_actual = df[4].iloc[-1]
            ema = df[4].ewm(span=200, adjust=False).mean().iloc[-1]
            dist_actual = ((p_actual - ema) / ema) * 100
            
            # --- TABLERO DE CONTROL ACTUALIZADO ---
            print("\n" + "═"*45)
            print(f"💰 SOL: {p_actual:.2f} | 💵 ACUMULADO HOY: {acumulado_hoy:+.2f}%")
            print(f"🧲 ELÁSTICO: {dist_actual:+.2f}% | 📊 DIST. MÁX: {abs(dist_actual):.2f}%")
            
            if en_operacion:
                roi_actual = ((p_entrada - p_actual) / p_entrada) * 100 if elast_entrada > 0 else ((p_actual - p_entrada) / p_entrada) * 100
                if roi_actual > max_roi: max_roi = roi_actual
                
                # Análisis de Proporción: Si entramos con mucha distancia, el objetivo es más alto
                objetivo_sugerido = abs(elast_entrada) * 0.8 # La física dice que suele recuperar el 80%
                print(f"📈 ROI: {roi_actual:+.2f}% | 🎯 META FÍSICA: {objetivo_sugerido:.2f}%")
                print(f"🛑 TRAILING STOP: {t_stop}%")
            print("═"*45)

            # 1. ENTRADA (Sensibilidad 2.5%)
            if not en_operacion and abs(dist_actual) >= 2.5:
                p_entrada = p_actual
                elast_entrada = dist_actual
                en_operacion = True
                max_roi = 0
                # Si la distancia es enorme (ej. 8%), el Zig-Zag es más fuerte, subimos el stop inicial
                t_stop = 0.4 if abs(dist_actual) < 4 else 0.7
                
                side = 'SELL' if dist_actual > 0 else 'BUY'
                client.futures_create_order(symbol="SOLUSDT", side=side, type='MARKET', quantity=0.1)
                print(f"🚀 DISPARO: Buscando el regreso de {dist_actual:.2f}% de tensión.")

            # 2. GESTIÓN DE COSECHA (1% - 7%)
            if en_operacion:
                # Ajuste dinámico de cosecha (Lo que pediste del 1%)
                if 1.0 < max_roi < 3.0: t_stop = 0.3 # Aseguramos el 1% rápido
                elif max_roi >= 5.0: t_stop = 1.2    # Dejamos correr la gran ganancia

                # CIERRE Y SUMA AL TESORO
                if max_roi > 0.8 and roi_actual < (max_roi - t_stop):
                    acumulado_hoy += roi_actual # Sumamos al contador del día
                    print(f"✅ COBRO REALIZADO: {roi_actual:.2f}% guardado en el acumulado.")
                    
                    with open(archivo_memoria, "a") as f:
                        f.write(f"{int(time.time())},{elast_entrada:.2f},{roi_actual:.2f}\n")
                    
                    en_operacion = False
                    max_roi = 0

            time.sleep(15)
        except Exception as e:
            print(f"⚠️ Alerta: {e}"); time.sleep(20)

if __name__ == "__main__":
    ejecutar_v14_3()
