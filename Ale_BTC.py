import os, time
import pandas as pd
from binance.client import Client

def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Neto actual según tu último log
cap_actual = 20.50 
MIN_LOT = 15.0 # Mínimo de Binance para que no te rebote

st = {m: {'e': False, 'p': 0, 't': '', 'm': -9.0} for m in ms}

def analizar_fisica_ale(df):
    # Definimos los ejes de tu dibujo
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Sigue la vela
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Tu eje central i
    
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    e9_p = df['ema_9'].iloc[-2]; e27_p = df['ema_27'].iloc[-2]
    
    # ENTRADA: Cruce exacto de la 9 sobre la 27
    if e9 < e27 and e9_p >= e27_p: return "🟥" # SHORT (Baja)
    if e9 > e27 and e9_p <= e27_p: return "🟩" # LONG (Suba)
    return "."

print(f"🔱 IA QUANTUM | VOLVIENDO AL DIBUJO | NETO: ${cap_actual}")

while True:
    try:
        op_activas = sum(1 for m in ms if st[m]['e'])
        
        for m in ms:
            s = st[m]
            # Pedimos 100 velas para que la 27 sea estable
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df['close'] = df['close'].astype(float)
            px = df['close'].iloc[-1]
            
            if not s['e']:
                # Solo una operación de $15 a la vez
                if op_activas < 1: 
                    senal = analizar_fisica_ale(df)
                    if senal != ".":
                        s['t'] = "LONG" if senal == "🟩" else "SHORT"
                        s['p'], s['e'], s['m'] = px, True, -9.0
                        op_activas += 1
                        print(f"\n🎯 DISPARO EN {m} ({s['t']}) | Siguiendo la vela...")
            else:
                # ROI con x10 y comisión
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                if roi > s['m']: s['m'] = roi 
                
                ema_27_act = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
                
                # REGLA DE ORO DE TU DIBUJO: Salir solo al tocar la 27
                toca_27 = (s['t'] == "LONG" and px <= ema_27_act) or (s['t'] == "SHORT" and px >= ema_27_act)
                
                # Mantengo el Trailing alto (1.8) solo por si hay un salto brusco
                trail = (s['m'] >= 1.8 and roi <= (s['m'] - 0.4))

                if toca_27 or trail or roi <= -1.2:
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    op_activas -= 1
                    mot = "TRAILING" if trail else "EJE 27"
                    print(f"⏱️ SALIDA {m} ({mot}) | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15) # Seguridad de Binance
    except:
        time.sleep(10); cl = c()
