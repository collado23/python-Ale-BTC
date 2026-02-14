import os, time, csv
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN ---
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

try:
    cl = c()
    print("✅ MOTOR V42 BLINDADO: BREAK-EVEN + CONTROL DE RACHAS")
except:
    print("❌ ERROR DE CONEXIÓN")

# --- CONFIGURACIÓN ESTRATÉGICA ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv"
cap_inicial = 16.54  

# --- 🧠 MEMORIA CON GESTIÓN DE RIESGO ---
def gestionar_memoria(moneda="", tipo="", modo="", roi=0, resultado="", leer=False):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            csv.writer(f).writerow(['fecha', 'moneda', 'tipo', 'modo', 'roi', 'resultado'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            if len(df) < 1: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
            ganancia_total = df['roi'].sum()
            capital_actual = cap_inicial + (cap_inicial * (ganancia_total / 100))
            
            ultimas = df.tail(3)
            fallos = (ultimas['resultado'] == "LOSS").sum()
            
            if capital_actual < 16.00 or fallos >= 2: return 1.5, capital_actual, "🛡️ DEFENSIVO"
            if (ultimas['resultado'] == "WIN").sum() >= 2 and capital_actual > 17.50: return 0.8, capital_actual, "🔥 BERSERKER"
            return 1.0, capital_actual, "⚔️ FRANCOTIRADOR"
        except: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            csv.writer(f).writerow([time.strftime('%Y-%m-%d %H:%M:%S'), moneda, tipo, modo, roi, resultado])

# --- ⚔️ MOTOR DE ANÁLISIS V42 ---
def analizar_entrada(m, factor, capital):
    try:
        k = cl.get_klines(symbol=m, interval='1m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).astype(float)
        
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        distancia = abs(ema9 - ema27) / ema27 * 100
        
        vol_avg = df['v'].tail(15).mean()
        px = df['c'].iloc[-1]
        inyeccion = df['v'].iloc[-1] > (vol_avg * 2.8) # Filtro de volumen más estricto

        # Potencia limitada para evitar devoluciones bruscas
        max_x = 15 if capital >= 17.0 else 10 
        fuerza_x = int(np.clip(max_x / factor, 5, max_x))

        # Señales con filtro de tendencia clara
        if inyeccion and ema9 > (ema27 * 1.0008) and px > ema9 and distancia > 0.06:
            return "LONG", "BULL_V42", fuerza_x
        if inyeccion and ema9 < (ema27 * 0.9992) and px < ema9 and distancia > 0.06:
            return "SHORT", "BEAR_V42", fuerza_x
            
        return None, None, 0
    except: return None, None, 0

# --- 🚀 BUCLE DE OPERACIÓN ---
st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'modo': '', 'x': 10, 'be': False} for m in ms}
factor_actual, capital_trabajo, rango = gestionar_memoria(leer=True)

print(f"🔱 INICIANDO PROTECCIÓN V42 | CAP: ${capital_trabajo:.2f}")

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            
            if not s['e']:
                print(f"[{rango}] 🔭 Acechando {m} | Cap: ${capital_trabajo:.2f} | X_MAX: {15 if capital_trabajo >= 17 else 10}", end='\r')
                tipo, modo, fx = analizar_entrada(m, factor_actual, capital_trabajo)
                if tipo:
                    s['e'], s['p'], s['t'], s['modo'], s['x'], s['max'], s['be'] = True, px, tipo, modo, fx, px, False
                    print(f"\n⚡ ¡DISPARO CONFIRMADO! {m} {tipo} | {fx}X")
            else:
                # CÁLCULO DE ROI
                if s['t'] == "LONG":
                    roi = ((px - s['p']) / s['p'] * 100 * s['x'])
                    s['max'] = max(s['max'], px)
                else: # SHORT
                    roi = ((s['p'] - px) / s['p'] * 100 * s['x'])
                    s['max'] = min(s['max'], px) if s['max'] > 0 else px

                roi -= 0.26 # Comisiones
                retroceso = abs(s['max'] - px) / s['p'] * 100 * s['x']

                # --- 🛡️ LÓGICA DE BREAK-EVEN (NUEVO) ---
                if roi > 0.45 and not s['be']:
                    s['be'] = True
                    print(f"\n🔒 BREAK-EVEN ACTIVADO en {m}. Ya no se puede perder en este trade.")

                print(f"📊 {m} ROI: {roi:.2f}% | Max: {s['max']}", end='\r')

                # SALIDA: Profit, Stop Loss o Protección Break-even
                if (roi > 0.40 and retroceso > 0.18) or (s['be'] and roi < 0.05) or roi <= -1.2:
                    res = "WIN" if roi > 0 else "LOSS"
                    capital_trabajo += (capital_trabajo * (roi / 100))
                    gestionar_memoria(m, s['t'], s['modo'], round(roi, 2), res)
                    s['e'] = False
                    print(f"\n✅ CIERRE ESTRATÉGICO | {res} | Capital: ${capital_trabajo:.2f}")
                    factor_actual, _, rango = gestionar_memoria(leer=True)

        time.sleep(0.5)
    except: time.sleep(2)
