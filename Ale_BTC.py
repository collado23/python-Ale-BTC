import os, time, pandas as pd, numpy as np
import yfinance as yf
from binance.client import Client

# --- CONEXIÓN ---
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
archivo_memoria = "espejo_cuantico.txt"

def analizar_adn_4_anios():
    print("📡 Escaneando 4 años de ciclos físicos (Yahoo Finance)...")
    data = yf.download("SOL-USD", period="5y", interval="1d", progress=False)
    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
    df = data.copy()
    df['ema'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['dist'] = ((df['Close'] - df['ema']) / df['ema']) * 100
    return df

MEMORIA = analizar_adn_4_anios()

def ejecutar_v14_1():
    print("🔱 GLADIADOR V14.1: PROTECCIÓN DE GANANCIA (5%+) ACTIVADA")
    en_operacion = False
    p_entrada, elast_entrada, max_roi = 0, 0, 0
    t_stop = 0.6 # Base acordada

    while True:
        try:
            k = client.futures_klines(symbol="SOLUSDT", interval='1m', limit=100)
            df = pd.DataFrame(k).astype(float)
            p_actual = df[4].iloc[-1]
            ema = df[4].ewm(span=200, adjust=False).mean().iloc[-1]
            dist_actual = ((p_actual - ema) / ema) * 100
            
            # --- MONITOR ---
            print(f"\n" + "-"*40)
            print(f"📊 SOL: {p_actual:.2f} | 🧲 ELÁSTICO: {dist_actual:+.2f}%")

            # 1. ENTRADA (Mínimo 2.5% de tensión)
            if not en_operacion and abs(dist_actual) >= 2.5:
                p_entrada = p_actual
                elast_entrada = dist_actual
                en_operacion = True
                max_roi = 0
                t_stop = 0.6 if abs(dist_actual) < 5 else 1.0 # Ajuste inicial por volatilidad
                
                side = 'SELL' if dist_actual > 0 else 'BUY'
                client.futures_create_order(symbol="SOLUSDT", side=side, type='MARKET', quantity=0.1)
                print(f"🚀 ENTRADA: {side} | T-Stop Inicial: {t_stop}%")

            # 2. GESTIÓN DE LA OPERACIÓN (ZIG-ZAG)
            if en_operacion:
                roi_actual = ((p_entrada - p_actual) / p_entrada) * 100 if elast_entrada > 0 else ((p_actual - p_entrada) / p_entrada) * 100
                if roi_actual > max_roi: max_roi = roi_actual

                # --- PROTECCIÓN DE GANANCIA GORDA (TU PEDIDO) ---
                if max_roi >= 5.0 and t_stop != 1.5:
                    t_stop = 1.5
                    print("🛡️ PROTECCIÓN 5%+: Trailing Stop subido a 1.5% para el gran Zig-Zag.")

                # ¿Pasamos la EMA?
                paso_ema = (elast_entrada > 0 and p_actual < ema) or (elast_entrada < 0 and p_actual > ema)
                print(f"📈 ROI: {roi_actual:+.2f}% | 🎯 MÁX: {max_roi:+.2f}% | 🛑 STOP: {t_stop}%")
                print(f"🚩 {'ZONA INERCIA' if paso_ema else 'ZONA REGRESO'}")

                # 3. CIERRE POR TRAILING
                if max_roi > 1.0 and roi_actual < (max_roi - t_stop):
                    print(f"💰 CIERRE ESTRATÉGICO: ROI {roi_actual:.2f}%")
                    with open(archivo_memoria, "a") as f:
                        f.write(f"{int(time.time())},{elast_entrada:.2f},{roi_actual:.2f},{1 if paso_ema else 0}\n")
                    en_operacion = False
                    max_roi = 0

            time.sleep(15)
        except Exception as e:
            print(f"⚠️ Error: {e}"); time.sleep(20)

if __name__ == "__main__":
    ejecutar_v14_1()
