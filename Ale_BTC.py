import os, time
import pandas as pd
from binance.client import Client

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 23.86 # Capital según el último log
st = {m: {'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def calcular_cerebro(df):
    df['ema_rápida'] = df['close'].ewm(span=7, adjust=False).mean()
    df['ema_lenta'] = df['close'].ewm(span=25, adjust=False).mean()
    # RSI para detectar si el precio ya cayó demasiado (agotamiento)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def detectar_giro_real(df):
    act = df.iloc[-1]; prev = df.iloc[-2]
    
    # Lógica para detectar el despegue tras la bajada (LONG)
    # 1. El RSI debe estar saliendo de la zona baja (despegue)
    # 2. La vela actual debe ser verde y cerrar por encima de la media
    despegue_verde = act['close'] > act['open'] and act['close'] > act['ema_rápida'] and prev['rsi'] < 40
    
    # Lógica para evitar el SHORT en el piso
    # Si el RSI es muy bajo (< 30), prohibido vender, porque viene el rebote
    caida_agotada = act['rsi'] < 30

    if despegue_verde: return "🟩"
    if (act['close'] < act['open'] and act['close'] < act['ema_rápida']) and not caida_agotada:
        return "🟥"
        
    return "."

print(f"🔱 IA QUANTUM: FILTRO DE AGOTAMIENTO | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            senal = detectar_giro_real(df)

            if not s['e']:
                if senal != ".":
                    s['t'] = "LONG" if senal == "🟩" else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 {senal} CAMBIO DETECTADO EN {m} | PX: {px}")
            else:
                # GESTIÓN PARA CERO PÉRDIDAS
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                
                # Salida por "Rebote de Seguridad"
                # Si estamos en LONG y la vela actual pierde fuerza, cerramos.
                v_act = df.iloc[-1]
                perdio_fuerza = (s['t'] == "LONG" and px < v_act['open']) or (s['t'] == "SHORT" and px > v_act['open'])

                if roi <= -0.20 or (roi > 0.10 and roi < s['m'] - 0.08) or perdio_fuerza:
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['o'] += 1; s['e'] = False
                    est = "✅" if roi > 0 else "❌"
                    print(f"\n{est} SALIDA {m} {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except:
        time.sleep(10); cl = c()
