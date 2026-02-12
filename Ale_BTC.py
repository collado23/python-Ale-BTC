import os, time
import pandas as pd
from binance.client import Client

def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

cap_actual = 20.50 # Actualizado según tu último log 
MIN_LOT = 15.0 

st = {m: {'e': False, 'p': 0, 't': '', 'm': -9.0} for m in ms}

def analizar_fisica_ale(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean()
    
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    e9_p = df['ema_9'].iloc[-2]; e27_p = df['ema_27'].iloc[-2]
    
    # ENTRADA: Cruce directo
    if e9 < e27 and e9_p >= e27_p: return "🟥" # SHORT
    if e9 > e27 and e9_p <= e27_p: return "🟩" # LONG
    return "."

print(f"🔱 IA QUANTUM FLASH 2.0 | NETO: ${cap_actual}")

while True:
    try:
        op_activas = sum(1 for m in ms if st[m]['e'])
        for m in ms:
            s = st[m]
            # Usamos 50 velas para procesar más rápido
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df['close'] = df['close'].astype(float)
            px = df['close'].iloc[-1]
            
            if not s['e']:
                if op_activas < 1: 
                    senal = analizar_fisica_ale(df)
                    if senal != ".":
                        s['t'] = "LONG" if senal == "🟩" else "SHORT"
                        s['p'], s['e'], s['m'] = px, True, -9.0
                        op_activas += 1
                        print(f"\n🎯 ENTRADA $15 EN {m} ({s['t']})")
            else:
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                if roi > s['m']: s['m'] = roi 
                
                # CÁLCULO DE CURVATURA (Anticipación)
                ema_9_actual = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
                ema_9_previa = df['close'].ewm(span=9, adjust=False).mean().iloc[-2]
                ema_27_act = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
                
                # SALIDA POR CURVATURA: La 9 empieza a buscar la 27
                giro = (s['t'] == "LONG" and ema_9_actual < ema_9_previa) or \
                       (s['t'] == "SHORT" and ema_9_actual > ema_9_previa)
                
                # REGLAS DE VELOCIDAD
                toca_27 = (s['t'] == "LONG" and px <= ema_27_act) or (s['t'] == "SHORT" and px >= ema_27_act)
                trail = (s['m'] >= 1.2 and roi <= (s['m'] - 0.3)) # Trailing más agresivo

                if toca_27 or trail or (roi >= 0.5 and giro):
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    op_activas -= 1
                    mot = "GIRO" if giro else ("TRAIL" if trail else "EJE 27")
                    print(f"⏱️ SALIDA {m} ({mot}) | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15) # Mantenemos los 15s para seguridad de API
    except:
        time.sleep(10); cl = c()
