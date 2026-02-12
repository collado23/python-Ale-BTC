import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta actualizado según tu último log 
cap_actual = 18.73 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': '', 'v': ''} for m in ms}

def identificar_vela_maestra(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    
    c_act = df['close'].iloc[-1]; o_act = df['open'].iloc[-1]
    c_ant = df['close'].iloc[-2]; o_ant = df['open'].iloc[-2]
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    
    # Filtro de Fuerza: La vela actual debe ser más grande que la anterior (Envolvente)
    envolvente = abs(c_act - o_act) > abs(c_ant - o_ant)

    # --- DIRECCIÓN: SUBA (LONG) ---
    # Vela Verde + Anterior Roja + Cruce de EMA 9 con fuerza
    if c_act > o_act and c_ant < o_ant and c_act > e9 and e9 > e27 and envolvente:
        return "LONG", "ENVOLVENTE ALCISTA"

    # --- DIRECCIÓN: BAJA (SHORT) ---
    # Vela Roja + Anterior Verde + Cruce de EMA 9 con fuerza
    if c_act < o_act and c_ant > o_ant and c_act < e9 and e9 < e27 and envolvente:
        return "SHORT", "ENVOLVENTE BAJISTA"
        
    return None, None

print(f"🔱 IA QUANTUM PRECISIÓN | MONITOR DE PRECIO VIVO | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px_actual = df['close'].iloc[-1]
            
            # 1. BUSCAR ENTRADA (Más estricta para no entrar mal)
            if not s['e']:
                dir, vela = identificar_vela_maestra(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'] = dir, px_actual, True, vela
                    print(f"🔥 {m} | VELA: {vela} | {dir} en {px_actual}")
            
            # 2. MONITOR CON PRECIO ACTUAL
            elif s['e']:
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                
                # Monitor que pediste: Nombre, Dirección, Entrada, Precio Actual y ROI
                print(f"📊 {m} | {s['v']} ({s['t']}) | Entró: {s['p']} | Ahora: {px_actual} | ROI: {roi:.2f}%")
                
                # Salida técnica (EMA 27) para proteger el neto de $18.73 
                e27 = df['ema_27'].ewm(span=27, adjust=False).mean().iloc[-1]
                if roi >= 2.0 or (s['t'] == "LONG" and px_actual < e27) or (s['t'] == "SHORT" and px_actual > e27):
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    print(f"💰 CIERRE {m} | ROI: {roi:.2f}% | NUEVO NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except Exception as e:
        time.sleep(10); cl = c()
