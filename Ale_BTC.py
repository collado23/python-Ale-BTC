import os, time, csv
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN ---
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

try:
    cl = c()
    print("✅ MOTOR HÍBRIDO V40: INYECCIÓN + EMAs 9/27 ONLINE")
except:
    print("❌ ERROR DE CONEXIÓN")

# --- CONFIGURACIÓN DE BATALLA ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv"
cap_inicial = 16.54  

# --- 🧠 GESTIÓN DE MEMORIA Y RACHAS ---
def gestionar_memoria(moneda="", tipo="", modo="", roi=0, resultado="", leer=False):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['fecha', 'moneda', 'tipo', 'modo', 'roi', 'resultado'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            if len(df) < 1: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
            
            # Calculamos el capital actual sumando/restando ROIs de la memoria
            # Esto permite que el bot "recuerde" las ganadas y perdidas previas
            ganancia_acumulada = df['roi'].sum()
            capital_actual = cap_inicial + (cap_inicial * (ganancia_acumulada / 100))
            
            # Analizar racha para el Rango
            ultimas = df.tail(3)
            fallos = (ultimas['resultado'] == "LOSS").sum()
            ganancias = (ultimas['resultado'] == "WIN").sum()
            
            if fallos >= 2: return 1.3, capital_actual, "🛡️ DEFENSIVO"
            if ganancias >= 2: return 0.7, capital_actual, "🔥 BERSERKER"
            return 1.0, capital_actual, "⚔️ FRANCOTIRADOR"
        except: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), moneda, tipo, modo, roi, resultado])

# --- ⚔️ LÓGICA DE ENTRADA (EL FILTRO DE ALE) ---
def analizar_entrada(m, factor):
    try:
        k = cl.get_klines(symbol=m, interval='1m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).astype(float)
        
        # EMAs de tu estrategia ganadora
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        vol_avg = df['v'].tail(15).mean()
        px = df['c'].iloc[-1]
        
        # 1. Inyección de volumen (Fuerza)
        inyeccion = df['v'].iloc[-1] > (vol_avg * 2.2)
        
        # 2. Cruce de EMAs (Tu Racha Ganadora)
        # El precio debe estar por encima de ambas y la 9 sobre la 27
        confirmacion_ema = ema9 > ema27 and px > ema9
        
        if inyeccion and confirmacion_ema:
            # Si venimos ganando (factor bajo), el apalancamiento sube a 15x
            fuerza_x = int(np.clip(12 / factor, 5, 15))
            return "LONG", "INYECC+EMA9/27", fuerza_x
            
        return None, None, 0
    except: return None, None, 0

# --- 🚀 BUCLE DE OPERACIÓN ---
print(f"\n🔱 CARGANDO ESTRATEGIA HÍBRIDA...")
st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'modo': '', 'x': 10} for m in ms}
factor_actual, capital_trabajo, rango = gestionar_memoria(leer=True)

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            
            if not s['e']:
                print(f"[{rango}] 🔭 Buscando en {m} | Cap: ${capital_trabajo:.2f}", end='\r')
                tipo, modo, fuerza_x = analizar_entrada(m, factor_actual)
                if tipo:
                    s['e'], s['p'], s['t'], s['modo'], s['x'], s['max'] = True, px, tipo, modo, fuerza_x, px
                    print(f"\n🚀 ¡SEÑAL CONFIRMADA! {m} | EMAs 9/27 OK | {fuerza_x}X")
            else:
                # Gestión de Salida (Resorte Quantum)
                roi = ((px - s['p']) / s['p'] * 100 * s['x']) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 100 * s['x'])
                roi -= 0.22 
                s['max'] = max(s['max'], px)
                retroceso = abs(s['max'] - px) / s['p'] * 100 * s['x']
                
                print(f"📊 {m} ROI: {roi:.2f}% | Max: {s['max']}", end='\r')

                # Salida por Profit o Stop Loss
                if (roi > 0.45 and retroceso > 0.15) or roi <= -1.1:
                    res = "WIN" if roi > 0 else "LOSS"
                    # Aquí se aplica el interés compuesto real
                    capital_trabajo += (capital_trabajo * (roi / 100))
                    gestionar_memoria(m, s['t'], s['modo'], round(roi, 2), res)
                    s['e'] = False
                    print(f"\n✅ OPERACIÓN CERRADA | Resultado: {res} | Nuevo Cap: ${capital_trabajo:.2f}")
                    # Re-leer memoria para actualizar rango y factor
                    factor_actual, _, rango = gestionar_memoria(leer=True)

        time.sleep(0.5)
    except: time.sleep(2)
