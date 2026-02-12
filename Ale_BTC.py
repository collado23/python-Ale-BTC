import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de tu cuenta (Neto actual según logs)
cap_actual = 20.38 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': ''} for m in ms}

def fisica_velas_japonesas(df):
    # Definimos las EMAs para la estructura
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Amarilla
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Azul
    
    # Datos de la vela actual y la anterior
    c_actual = df['close'].iloc[-1]
    o_actual = df['open'].iloc[-1]
    c_ant = df['close'].iloc[-2]
    o_ant = df['open'].iloc[-2]
    e9 = df['ema_9'].iloc[-1]
    e27 = df['ema_27'].iloc[-1]
    
    # LÓGICA DE VELAS (REBOTE LARGO)
    # Si la vela actual es VERDE y la anterior fue ROJA, y estamos sobre la amarilla:
    if c_actual > o_actual and c_ant < o_ant and c_actual > e9 and e9 > e27:
        return "LONG"
    # Si la vela actual es ROJA y la anterior fue VERDE, y estamos bajo la amarilla:
    if c_actual < o_actual and c_ant > o_ant and c_actual < e9 and e9 < e27:
        return "SHORT"
    return None

print(f"🔱 TRIPLE ENTRADA ACTIVADA | ESTRATEGIA: VELAS JAPONESAS | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            # Traemos las velas
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px = df['close'].iloc[-1]
            
            # Análisis de entrada
            if not s['e']:
                senal = fisica_velas_japonesas(df)
                if senal:
                    s['t'], s['p'], s['e'] = senal, px, True
                    print(f"🔥 DISPARO JAPONÉS en {m}: {senal} a {px}")
            
            # Análisis de salida (Cosecha rápida + Seguro)
            elif s['e']:
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                e27 = df['ema_27'].iloc[-1]
                
                # Cerramos si ganamos el 2% rápido O si el precio rompe la línea azul (EMA 27)
                if roi >= 2.0 or (s['t'] == "LONG" and px < e27) or (s['t'] == "SHORT" and px > e27):
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    estado = "GANANCIA" if roi >= 2.0 else "SALIDA TÉCNICA"
                    print(f"💰 {estado} en {m} | ROI: {roi:.2f}% | NUEVO NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except Exception as e:
        time.sleep(10); cl = c()
