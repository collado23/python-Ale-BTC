import os, time, csv
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN ---
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

try:
    cl = c()
    print("✅ Sistema Híbrido V40 (Inyección + EMAs 9/27) Online")
except:
    print("❌ Error de conexión.")

# --- CONFIGURACIÓN ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv"
cap_inicial = 16.54  

# --- 🧠 MEMORIA Y RANGOS ---
def gestionar_memoria(moneda="", tipo="", modo="", roi=0, resultado="", leer=False):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['fecha', 'moneda', 'tipo', 'modo', 'roi', 'resultado'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            if len(df) < 2: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
            ultimas = df.tail(3)
            fallos = (ultimas['resultado'] == "LOSS").sum()
            ganancias = (ultimas['resultado'] == "WIN").sum()
            
            # El capital se actualiza dinámicamente según los logs [cite: 7, 8, 10]
            cap_actual = cap_inicial + (df['roi'].sum() * 0.016)
            
            if fallos >= 2: return 1.4, cap_actual, "🛡️ DEFENSIVO"
            if ganancias >= 2: return 0.8, cap_actual, "🔥 BERSERKER"
            return 1.0, cap_actual, "⚔️ FRANCOTIRADOR"
        except: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), moneda, tipo, modo, roi, resultado])

# --- ⚔️ MOTOR V40 HÍBRIDO (EMAs 9/27 + VOLUMEN) ---
def analizar_entrada(m, factor):
    try:
        k = cl.get_klines(symbol=m, interval='1m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).astype(float)
        
        # Nuevas EMAs solicitadas
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        ema200 = df['c'].ewm(span=200).mean().iloc[-1]
        
        vol_avg = df['v'].tail(15).mean()
        px = df['c'].iloc[-1]
        
        # 1. CONDICIÓN DE INYECCIÓN (BALLENAS)
        inyeccion = df['v'].iloc[-1] > (vol_avg * 2.5)
        
        # 2. CONDICIÓN DE TENDENCIA (9/27)
        tendencia_ok = ema9 > ema27 and px > ema9
        
        # Solo entra si hay inyección Y las EMAs confirman la subida
        if inyeccion and tendencia_ok and px > ema200:
            fuerza_x = int(np.clip(12 / factor, 3, 15))
            return "LONG", "HIBRIDO_9_27", fuerza_x
            
        return None, None, 0
    except: return None, None, 0

# --- 🚀 BUCLE PRINCIPAL ---
print(f"\n🔱 V40 MASTER QUANTUM | EMAs 9/27 ACTIVAS")
st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'modo': '', 'x': 10} for m in ms}
factor_actual, capital_trabajo, rango = gestionar_memoria(leer=True)

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            
            if not s['e']:
                print(f"[{rango}] 🔭 Escaneando {m} | Cap: ${capital_trabajo:.2f}", end='\r')
                tipo, modo, fuerza_x = analizar_entrada(m, factor_actual)
                if tipo:
                    s['e'], s['p'], s['t'], s['modo'], s['x'], s['max'] = True, px, tipo, modo, fuerza_x, px
                    print(f"\n🚀 ¡ATAQUE CONFIRMADO! {m} | 9/27 Cruzadas | {fuerza_x}X")
            else:
                # GESTIÓN DE SALIDA (RESORTE)
                roi = ((px - s['p']) / s['p'] * 100 * s['x']) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 100 * s['x'])
                roi -= 0.22 
                s['max'] = max(s['max'], px)
                retroceso = abs(s['max'] - px) / s['p'] * 100 * s['x']
                
                print(f"📊 {m} ROI: {roi:.2f}% | Max: {s['max']}", end='\r')

                if (roi > 0.45 and retroceso > 0.12) or roi <= -1.2:
                    res = "WIN" if roi > 0 else "LOSS"
                    capital_trabajo += (capital_trabajo * (roi / 100))
                    gestionar_memoria(m, s['t'], s['modo'], round(roi, 2), res)
                    s['e'] = False
                    print(f"\n✅ CIERRE EN {m} | ROI: {roi:.2f}% | Nuevo Cap: ${capital_trabajo:.2f}")
                    factor_actual, _, rango = gestionar_memoria(leer=True)

        time.sleep(0.5)
    except: time.sleep(2)
