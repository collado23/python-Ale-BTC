import os, time
import pandas as pd
from binance.client import Client

def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Capital inicial para esta corrida (ajustado según logs)
cap_actual = 23.86 
st = {m: {'e': False, 'p': 0, 't': '', 'm': -9.0} for m in ms}

def calculadora_fisica_27_9(df):
    act = df.iloc[-1]; prev = df.iloc[-2]
    
    # Ejes Matemáticos según tu pedido
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Eje i (Centro estable)
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Eje j (Sensor rápido)
    
    i = df['ema_27'].iloc[-1]
    j = df['ema_9'].iloc[-1]
    j_prev = df['ema_9'].iloc[-2]
    
    # 1. CÁLCULO DE DISTANCIA X (Respecto a la 27)
    # Analizamos 100 velas atrás para ver el comportamiento histórico
    distancias_x = (df['close'] - df['ema_27']).tail(100).abs()
    x_limite = distancias_x.mean() + distancias_x.std()

    # 2. DISPARO POR CRUCE Y TRAYECTORIA
    # Si la 9 (sensor) rompe la 27 (centro) hacia abajo:
    if j < i and j < j_prev and act['close'] < prev['low']:
        return "🟥" # Trayectoria de bajada confirmada
        
    # Si la 9 (sensor) rompe la 27 (centro) hacia arriba:
    if j > i and j > j_prev and act['close'] > prev['high']:
        return "🟩" # Trayectoria de subida confirmada
        
    return "."

print(f"🔱 IA QUANTUM: EJE i(27) - SENSOR j(9) | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            # Pedimos 200 para que la EMA 27 se calcule perfecta
            k = cl.get_klines(symbol=m, interval='1m', limit=200)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            
            px = df['close'].iloc[-1]
            prediccion = calculadora_fisica_27_9(df)

            if not s['e']:
                if prediccion != ".":
                    s['t'] = "LONG" if prediccion == "🟩" else "SHORT"
                    s['p'], s['e'], s['m'] = px, True, -9.0
                    print(f"\n🎯 DISPARO {s['t']} EN {m} | Centro 27 | Sensor 9")
            else:
                # GESTIÓN DE LA "X" EN TIEMPO REAL
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                
                ema_9_actual = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
                ema_27_actual = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]

                # SALIDA: Si el precio cruza la EMA 9 (primer aviso) 
                # o si la tendencia pierde la física del eje 27
                corte_sensor = (s['t'] == "LONG" and px < ema_9_actual) or \
                               (s['t'] == "SHORT" and px > ema_9_actual)

                if corte_sensor or roi <= -0.25:
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['e'] = False
                    res = "✅" if roi > 0 else "❌"
                    print(f"{res} SALIDA {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except:
        time.sleep(10); cl = c()
