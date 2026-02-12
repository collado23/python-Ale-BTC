import os, time
import pandas as pd
from binance.client import Client

def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 23.86 
st = {m: {'e': False, 'p': 0, 't': '', 'm': -9.0} for m in ms}

def calculadora_triple_eje(df):
    act = df.iloc[-1]; prev = df.iloc[-2]
    
    # Ejes Matemáticos
    df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean() # Eje i (Cuerpo)
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Eje j (Sensor)
    
    i = df['ema_20'].iloc[-1]
    j = df['ema_9'].iloc[-1]
    j_prev = df['ema_9'].iloc[-2]
    
    # 1. PREDICCIÓN POR CRUCE (Inercia de arranque)
    # Si la pequeña (j) cruza la mediana (i) hacia abajo:
    if j < i and j < j_prev and act['close'] < prev['low']:
        return "🟥" # Bajada confirmada por sensor 9
        
    # Si la pequeña (j) cruza la mediana (i) hacia arriba:
    if j > i and j > j_prev and act['close'] > prev['high']:
        return "🟩" # Subida confirmada por sensor 9
        
    return "."

print(f"🔱 IA QUANTUM: SENSOR EMA 9 ACTIVADO | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=150)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            
            px = df['close'].iloc[-1]
            prediccion = calculadora_triple_eje(df)

            if not s['e']:
                if prediccion != ".":
                    s['t'] = "LONG" if prediccion == "🟩" else "SHORT"
                    s['p'], s['e'] = px, True
                    print(f"\n🎯 SENSOR 9 DISPARADO: {m} buscando inercia")
            else:
                # GESTIÓN DE SALIDA ULTRA-RÁPIDA
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                
                # Usamos la EMA 9 como "Corte de Cable"
                ema_9_actual = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
                
                # Si el precio cruza la EMA 9 en contra, cerramos YA para no perder
                corte_seguridad = (s['t'] == "LONG" and px < ema_9_actual) or \
                                  (s['t'] == "SHORT" and px > ema_9_actual)

                if corte_seguridad or roi <= -0.20:
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['e'] = False
                    res = "✅" if roi > 0 else "❌"
                    print(f"{res} SALIDA SENSOR 9 {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except:
        time.sleep(10); cl = c()
