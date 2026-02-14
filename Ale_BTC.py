import os, time, csv
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN ---
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

try:
    cl = c()
    print("✅ MOTOR BLINDADO V41: FILTRO DE TENDENCIA + RIESGO DINÁMICO")
except:
    print("❌ ERROR DE CONEXIÓN")

# --- CONFIGURACIÓN ESTRATÉGICA ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv"
cap_inicial = 16.54  

# --- 🧠 MEMORIA CON FILTRO DE SEGURIDAD ---
def gestionar_memoria(moneda="", tipo="", modo="", roi=0, resultado="", leer=False):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            csv.writer(f).writerow(['fecha', 'moneda', 'tipo', 'modo', 'roi', 'resultado'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            if len(df) < 1: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
            
            ganancia_acumulada = df['roi'].sum()
            capital_actual = cap_inicial + (cap_inicial * (ganancia_acumulada / 100))
            
            ultimas = df.tail(3)
            fallos = (ultimas['resultado'] == "LOSS").sum()
            
            # Lógica de Rangos
            if capital_actual < 15.80 or fallos >= 2: 
                return 1.4, capital_actual, "🛡️ DEFENSIVO"
            if (ultimas['resultado'] == "WIN").sum() >= 2 and capital_actual > 16.54: 
                return 0.8, capital_actual, "🔥 BERSERKER"
            
            return 1.0, capital_actual, "⚔️ FRANCOTIRADOR"
        except: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            csv.writer(f).writerow([time.strftime('%Y-%m-%d %H:%M:%S'), moneda, tipo, modo, roi, resultado])

# --- ⚔️ MOTOR DE ANÁLISIS V41 (ANTI-SERRUCHO) ---
def analizar_entrada(m, factor, capital):
    try:
        k = cl.get_klines(symbol=m, interval='1m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).astype(float)
        
        # Indicadores Clave
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        
        # FILTRO DE SEPARACIÓN (Evita que el bot entre si las líneas están pegadas)
        distancia = abs(ema9 - ema27) / ema27 * 100
        min_distancia = 0.05 # El "cocodrilo" debe estar abierto
        
        vol_avg = df['v'].tail(15).mean()
        px = df['c'].iloc[-1]
        inyeccion = df['v'].iloc[-1] > (vol_avg * 2.5)

        # RIESGO DINÁMICO: Si el capital es bajo, bajamos la potencia a 8x
        max_x = 15 if capital >= 16.0 else 8 
        fuerza_x = int(np.clip(max_x / factor, 4, max_x))

        # Señal de LONG (Subida clara)
        if inyeccion and ema9 > (ema27 * 1.0006) and px > ema9 and distancia > min_distancia:
            return "LONG", "BULL_RUN", fuerza_x
            
        # Señal de SHORT (Caída clara)
        if inyeccion and ema9 < (ema27 * 0.9994) and px < ema9 and distancia > min_distancia:
            return "SHORT", "BEAR_DROP", fuerza_x
            
        return None, None, 0
    except: return None, None, 0

# --- 🚀 BUCLE DE OPERACIÓN ---
st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'modo': '', 'x': 10} for m in ms}
factor_actual, capital_trabajo, rango = gestionar_memoria(leer=True)

print(f"🔱 SISTEMA V41 ACTIVADO | RANGO: {rango} | CAP: ${capital_trabajo:.2f}")

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            
            if not s['e']:
                print(f"[{rango}] 🔭 Acechando {m} | Cap: ${capital_trabajo:.2f} | X: {8 if capital_trabajo < 16 else 15}", end='\r')
                tipo, modo, fx = analizar_entrada(m, factor_actual, capital_trabajo)
                if tipo:
                    s['e'], s['p'], s['t'], s['modo'], s['x'], s['max'] = True, px, tipo, modo, fx, px
                    print(f"\n⚡ ¡ATAQUE ESTRATÉGICO! {m} {tipo} | {fx}X | Modo: {modo}")
            else:
                # GESTIÓN DE SALIDA (TRAILING STOP)
                if s['t'] == "LONG":
                    roi = ((px - s['p']) / s['p'] * 100 * s['x'])
                    s['max'] = max(s['max'], px)
                else: # SHORT
                    roi = ((s['p'] - px) / s['p'] * 100 * s['x'])
                    s['max'] = min(s['max'], px) if s['max'] > 0 else px

                roi -= 0.25 # Comisiones
                retroceso = abs(s['max'] - px) / s['p'] * 100 * s['x']
                
                print(f"📊 {m} {s['t']} ROI: {roi:.2f}% | Retro: {retroceso:.2f}%", end='\r')

                # Salida: Profit con Trail o Stop Loss estricto
                if (roi > 0.40 and retroceso > 0.15) or roi <= -1.2:
                    res = "WIN" if roi > 0 else "LOSS"
                    capital_trabajo += (capital_trabajo * (roi / 100))
                    gestionar_memoria(m, s['t'], s['modo'], round(roi, 2), res)
                    s['e'] = False
                    print(f"\n✅ CIERRE TÁCTICO | {res} | Capital Actual: ${capital_trabajo:.2f}")
                    factor_actual, _, rango = gestionar_memoria(leer=True)

        time.sleep(0.5)
    except: time.sleep(2)
