import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de tu cuenta (Actualizado a tu último log)
cap_actual = 18.73 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': '', 'v': ''} for m in ms}

def identificar_vela_y_direccion(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    
    # Datos de velas
    c_act = df['close'].iloc[-1]; o_act = df['open'].iloc[-1]
    c_ant = df['close'].iloc[-2]; o_ant = df['open'].iloc[-2]
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    
    # Lógica de nombres de velas
    es_verde = c_act > o_act
    es_roja = c_act < o_act
    envolvente = abs(c_act - o_act) > abs(c_ant - o_ant)

    # --- DIRECCIÓN: SUBA (LONG) ---
    if es_verde and c_ant < o_ant and c_act > e9 and e9 > e27:
        nombre = "ENVOLVENTE ALCISTA" if envolvente else "CHOQUE VERDE"
        return "LONG", nombre

    # --- DIRECCIÓN: BAJA (SHORT) ---
    if es_roja and c_ant > o_ant and c_act < e9 and e9 < e27:
        nombre = "ENVOLVENTE BAJISTA" if envolvente else "CHOQUE ROJO"
        return "SHORT", nombre
        
    return None, None

print(f"🔱 IA QUANTUM | MONITOR DE VELAS JAPONESAS | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px = df['close'].iloc[-1]
            
            # 1. BUSCAR ENTRADA CON NOMBRE DE VELA
            if not s['e']:
                dir, vela = identificar_vela_y_direccion(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'] = dir, px, True, vela
                    print(f"🔥 {m} | VELA: {vela} | DIRECCIÓN: {dir} | Precio: {px}")
            
            # 2. MONITOR ACTIVO
            elif s['e']:
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                print(f"📊 {m} | {s['v']} ({s['t']}) | ROI: {roi:.2f}%")
                
                # Salida técnica o por ganancia
                e27 = df['ema_27'].ewm(span=27, adjust=False).mean().iloc[-1]
                if roi >= 2.0 or (s['t'] == "LONG" and px < e27) or (s['t'] == "SHORT" and px > e27):
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    print(f"💰 CIERRE {m} | NUEVO NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except Exception as e:
        time.sleep(10); cl = c()
