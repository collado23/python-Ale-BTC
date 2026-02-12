import os, time
import pandas as pd
from binance.client import Client

def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

cap_actual = 22.32 
st = {m: {'e': False, 'p': 0, 't': '', 'm': -9.0} for m in ms}

def analizar_fisica_ale_activa(df):
    # Ejes según tu dibujo
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Sigue a la vela
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Inercia (Salida)
    
    e9 = df['ema_9'].iloc[-1]
    e27 = df['ema_27'].iloc[-1]
    e9_prev = df['ema_9'].iloc[-2]
    e27_prev = df['ema_27'].iloc[-2]
    
    # ENTRADA POR CRUCE DIRECTO (Sin esperar a la 200 para que sea más activo)
    # SHORT: La 9 cruza hacia abajo la 27
    if e9 < e27 and e9_prev >= e27_prev:
        return "🟥"
    # LONG: La 9 cruza hacia arriba la 27
    if e9 > e27 and e9_prev <= e27_prev:
        return "🟩"
    return "."

print(f"🔱 IA QUANTUM | MODO ACTIVO (Eje 9 vs 27) | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            
            px = df['close'].iloc[-1]
            senal = analizar_fisica_ale_activa(df)

            if not s['e']:
                if senal != ".":
                    s['t'] = "LONG" if senal == "🟩" else "SHORT"
                    s['p'], s['e'] = px, True
                    print(f"\n🎯 MOVIMIENTO DETECTADO: {m} ({s['t']}) | Entrando...")
            else:
                # GESTIÓN DE SALIDA: Solo cuando el precio cruza de vuelta la 27
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                e27_act = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
                
                # CONDICIÓN DE TU DIBUJO: Salir al tocar/cruzar la 27
                vender = (s['t'] == "LONG" and px <= e27_act) or (s['t'] == "SHORT" and px >= e27_act)

                if vender:
                    cap_actual += (cap_actual * (roi / 100))
                    s['e'] = False
                    res = "✅" if roi > 0 else "❌"
                    print(f"{res} SALIDA {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except:
        time.sleep(10); cl = c()
