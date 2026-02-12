import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Parámetros de tu cuenta
cap_actual = 20.38 # Actualizado según tu último log 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': ''} for m in ms}

def detectar_rebote_agresivo(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Amarilla
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Azul
    
    c = df['close'].iloc[-1]; o = df['open'].iloc[-1]
    cp = df['close'].iloc[-2]; op = df['open'].iloc[-2]
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    
    # ENTRADA: Vela actual verde, anterior roja (o viceversa para Short)
    # y el precio cruzando la línea amarilla con fuerza.
    if c > o and cp < op and c > e9 and e9 > e27: return "LONG"
    if c < o and cp > op and c < e9 and e9 < e27: return "SHORT"
    return None

print(f"🔱 CAZADOR DE REBOTES LARGOS | NETO: ${cap_actual} | 3 MONEDAS ACTIVAS")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px = df['close'].iloc[-1]
            
            # 1. BUSCAR ENTRADA
            if not s['e']:
                senal = detectar_rebote_agresivo(df)
                if senal:
                    s['t'], s['p'], s['e'] = senal, px, True
                    print(f"🚀 DISPARO en {m}: Rebote {senal} a {px}")
            
            # 2. GESTIONAR SALIDA (AGUANTE)
            elif s['e']:
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                e27 = df['ema_27'].iloc[-1]
                
                # FILTRO DE AGUANTE: No cierra solo por tocar. 
                # Tiene que romper la línea azul un 0.2% para confirmar que el rebote murió.
                if s['t'] == "LONG":
                    termino_rebote = px < (e27 * 0.998) 
                else: # Para SHORT
                    termino_rebote = px > (e27 * 1.002)
                
                if termino_rebote:
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    print(f"💰 CIERRE en {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except Exception as e:
        time.sleep(10); cl = c()
