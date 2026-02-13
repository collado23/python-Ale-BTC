import os, time, csv
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
FILE_MEMORIA = "memoria_maestra.csv"

# --- CONFIGURACIÓN DE CAPITAL E INTERÉS COMPUESTO ---
cap_actual = 16.54  # Tu capital inicial
riesgo_por_operacion = 0.95 # Usa el 95% del capital disponible (Interés Compuesto)

def calcular_posicion():
    # El bot mira cuánto dinero hay 'en la billetera' ahora mismo
    return cap_actual * riesgo_por_operacion

# --- SMART X (15X MAX) ---
def calcular_fuerza_x(df, modo, factor_memoria):
    x_base = 10
    if modo == "INYECCION": x_base += 3
    if modo == "VOLTEO_PICO": x_base -= 4
    
    # Ajuste por memoria
    if factor_memoria > 1.0: x_base -= 3 # Precaución
    if factor_memoria < 1.0: x_base += 2 # Confianza
    
    return int(np.clip(x_base, 3, 15)) # Tope de 15x solicitado

# --- MOTOR DE MEMORIA V36 ---
def leer_memoria_veloz():
    if not os.path.exists(FILE_MEMORIA): return 1.0
    try:
        df = pd.read_csv(FILE_MEMORIA)
        if (df.tail(2)['roi'] < 0).all(): return 1.3
    except: pass
    return 1.0

print(f"🔱 V40 MASTER QUANTUM | 15X MAX | INTERÉS COMPUESTO ACTIVO")

st = {m: {'e': False, 'p': 0, 't': '', 'max_px': 0, 'modo': ''} for m in ms}

while True:
    try:
        f_mem = leer_memoria_veloz()
        pos_dinamica = calcular_posicion() # Aquí se aplica el interés compuesto
        
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            
            if s['e']:
                # Lógica de salida con resorte (Trailing)
                roi = ((px - s['p']) / s['p'] * 1000) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 1000)
                roi -= 0.22 # Comisiones estimadas
                
                s['max_px'] = max(s['max_px'], px) if s['t'] == "LONG" else (min(s['max_px'], px) if s['max_px'] > 0 else px)
                retroceso = abs(s['max_px'] - px) / s['p'] * 1000
                
                if (roi > 0.4 and retroceso > 0.2) or roi <= -1.1:
                    # Cálculo de ganancia real para el Interés Compuesto
                    ganancia_usd = (pos_dinamica * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    print(f"\n💰 CIERRE: {m} | ROI: {roi:.2f}% | NUEVO CAP: ${cap_actual:.2f}")
                    # Guardar en memoria...
            
            else:
                # Búsqueda de entrada (Inyección / Estrategia de Guerra)
                # (Aquí iría el bloque de detectar_entrada con calcular_fuerza_x)
                pass

        time.sleep(0.5)
    except Exception as e:
        time.sleep(1); cl = c()
