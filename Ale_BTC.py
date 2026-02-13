import os, time, csv
import pandas as pd
from binance.client import Client

# Conexión ultra-rápida
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']

print("⚡ INICIANDO MODO FAST-STRATEGIC...")

# --- MEMORIA OPTIMIZADA (Solo lo último) ---
def leer_memoria_veloz():
    if not os.path.exists("memoria_maestra.csv"): return 1.0
    try:
        with open("memoria_maestra.csv", "r") as f:
            lineas = f.readlines()
            # Solo analizamos las últimas 3 operaciones para no perder tiempo
            ultimas = lineas[-3:]
            if any("LOSS" in l for l in ultimas): return 1.2
    except: pass
    return 1.0

# --- ARRANQUE VELOZ ---
def obtener_datos_rapido(moneda):
    # Bajamos el límite a 100 velas para que Binance responda al instante
    k = cl.get_klines(symbol=moneda, interval='1m', limit=100)
    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i']).astype(float)
    return df

cap_actual = 16.54 
st = {m: {'e': False, 'p': 0, 't': '', 'max_px': 0, 'modo': ''} for m in ms}

print("📡 Escaneando mercado ahora mismo...")

while True:
    try:
        factor = leer_memoria_veloz()
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            
            if not s['e']:
                # Pedimos datos solo de la moneda que estamos mirando
                df = obtener_datos_rapido(m)
                
                # --- Lógica de Inyección y Velas (Cálculo Veloz) ---
                ema35 = df['close'].ewm(span=35).mean().iloc[-1]
                vol_avg = df['v'].tail(10).mean()
                
                # ¿Están comprando fuerte? (Inyección)
                if df['v'].iloc[-1] > vol_avg * 2 and df['close'].iloc[-1] > df['open'].iloc[-1]:
                    if px > ema35:
                        s['t'], s['p'], s['e'], s['modo'] = "LONG", px, True, "INYECCION"
                        print(f"\n🚀 DISPARO RÁPIDO: {m} por Inyección de Capital")

            else:
                # Lógica de salida (Resorte dinámico)
                roi = ((px - s['p']) / s['p'] * 1000) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 1000)
                roi -= 0.22 
                if roi > 0.4 or roi <= -1.0:
                    cap_actual += (16.5 * (roi / 100))
                    print(f"\n✅ CIERRE RÁPIDO {m} | ROI: {roi:.2f}%")
                    s['e'] = False

        time.sleep(0.5) # Escaneo cada medio segundo
    except Exception as e:
        time.sleep(1); cl = c()
