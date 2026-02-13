import os, time, csv
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN ---
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

try:
    cl = c()
    print("✅ MOTOR BIDIRECCIONAL V40: LONG/SHORT + 9/27 ONLINE")
except:
    print("❌ ERROR DE CONEXIÓN")

# --- CONFIGURACIÓN ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv"
cap_inicial = 16.54  

# --- 🧠 MEMORIA DINÁMICA ---
def gestionar_memoria(moneda="", tipo="", modo="", roi=0, resultado="", leer=False):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            writer = csv.writer(f).writerow(['fecha', 'moneda', 'tipo', 'modo', 'roi', 'resultado'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            if len(df) < 1: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
            ganancia_total = df['roi'].sum()
            capital_actual = cap_inicial + (cap_inicial * (ganancia_total / 100))
            
            ultimas = df.tail(3)
            fallos = (ultimas['resultado'] == "LOSS").sum()
            if fallos >= 2: return 1.3, capital_actual, "🛡️ DEFENSIVO"
            if (ultimas['resultado'] == "WIN").sum() >= 2: return 0.7, capital_actual, "🔥 BERSERKER"
            return 1.0, capital_actual, "⚔️ FRANCOTIRADOR"
        except: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            csv.writer(f).writerow([time.strftime('%Y-%m-%d %H:%M:%S'), moneda, tipo, modo, roi, resultado])

# --- ⚔️ ANÁLISIS DE ENTRADA BIDIRECCIONAL ---
def analizar_entrada(m, factor):
    try:
        k = cl.get_klines(symbol=m, interval='1m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).astype(float)
        
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        vol_avg = df['v'].tail(15).mean()
        px = df['c'].iloc[-1]
        
        inyeccion = df['v'].iloc[-1] > (vol_avg * 2.3)
        fuerza_x = int(np.clip(12 / factor, 5, 15))

        # 🚀 LÓGICA PARA LONG (Subida)
        if inyeccion and ema9 > ema27 and px > ema9:
            return "LONG", "INYECC_UP", fuerza_x
            
        # 🔻 LÓGICA PARA SHORT (Caída)
        if inyeccion and ema9 < ema27 and px < ema9:
            return "SHORT", "INYECC_DOWN", fuerza_x
            
        return None, None, 0
    except: return None, None, 0

# --- 🚀 BUCLE PRINCIPAL ---
st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'modo': '', 'x': 10} for m in ms}
factor_actual, capital_trabajo, rango = gestionar_memoria(leer=True)

print(f"🔱 INICIANDO SISTEMA BIDIRECCIONAL... CAP: ${capital_trabajo:.2f}")

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            
            if not s['e']:
                print(f"[{rango}] 🔭 Acechando {m} (L/S) | Cap: ${capital_trabajo:.2f}", end='\r')
                tipo, modo, fx = analizar_entrada(m, factor_actual)
                if tipo:
                    s['e'], s['p'], s['t'], s['modo'], s['x'], s['max'] = True, px, tipo, modo, fx, px
                    print(f"\n⚡ ¡ATAQUE {tipo}! {m} | Modo: {modo} | {fx}X")
            else:
                # GESTIÓN DE ROI PARA AMBOS LADOS
                if s['t'] == "LONG":
                    roi = ((px - s['p']) / s['p'] * 100 * s['x'])
                    s['max'] = max(s['max'], px)
                else: # SHORT
                    roi = ((s['p'] - px) / s['p'] * 100 * s['x'])
                    s['max'] = min(s['max'], px) if s['max'] > 0 else px

                roi -= 0.24 # Comisiones aproximadas
                retroceso = abs(s['max'] - px) / s['p'] * 100 * s['x']
                
                print(f"📊 {m} {s['t']} ROI: {roi:.2f}% | Max: {s['max']}", end='\r')

                if (roi > 0.45 and retroceso > 0.15) or roi <= -1.1:
                    res = "WIN" if roi > 0 else "LOSS"
                    capital_trabajo += (capital_trabajo * (roi / 100))
                    gestionar_memoria(m, s['t'], s['modo'], round(roi, 2), res)
                    s['e'] = False
                    print(f"\n✅ POSICIÓN CERRADA | {res} | Nuevo Cap: ${capital_trabajo:.2f}")
                    factor_actual, _, rango = gestionar_memoria(leer=True)

        time.sleep(0.5)
    except: time.sleep(2)
