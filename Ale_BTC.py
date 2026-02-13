import os, time
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
LIMITE_OPERACIONES = 3

cap_actual = 16.68 
MIN_LOT = 16.0 # Subimos un poquito para recuperar terreno
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

def calcular_indicadores(df):
    # RSI y MACD
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['hist'] = df['macd'] - df['signal']
    
    # EMAs: 9, 27 y la 200 para tendencia mayor
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema27'] = df['close'].ewm(span=27, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    ant = df.iloc[-2]
    
    # Solo entramos si el histograma del MACD está creciendo con fuerza
    fuerza_macd = abs(act['hist']) > abs(ant['hist'])
    vol_ok = act['v'] > df['v'].rolling(10).mean().iloc[-1] * 1.2
    
    # LONG: Precio > EMA 200 + MACD Alza + RSI > 54
    if act['close'] > act['ema200'] and act['ema9'] > act['ema27'] and act['rsi'] > 54 and act['hist'] > 0 and fuerza_macd:
        if vol_ok: return "LONG"
    
    # SHORT: Precio < EMA 200 + MACD Baja + RSI < 46
    if act['close'] < act['ema200'] and act['ema9'] < act['ema27'] and act['rsi'] < 46 and act['hist'] < 0 and fuerza_macd:
        if vol_ok: return "SHORT"
    return None

print(f"🔱 IA QUANTUM V22 | FILTRO EMA 200 | MÁX OPS: 3 | CAP: ${cap_actual}")

while True:
    try:
        ops_abiertas = sum(1 for m in ms if st[m]['e'])
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            if s['e']:
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))

                # Niveles cada 0.25% para no ser tan "nerviosos"
                meta_actual = (int(roi * 4) / 4.0) 
                if meta_actual > s['nivel'] and meta_actual >= 0.5:
                    s['nivel'] = meta_actual
                    print(f"\n🛡️ {m} NIVEL: {s['nivel']}%")

                # PISO CON AIRE: 0.25% de distancia para aguantar el ruido
                piso = s['nivel'] - 0.25
                
                if s['nivel'] >= 0.5 and roi <= piso:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE TÉCNICO {m} | GANASTE: ${gan_usd:.2f} | TOTAL: ${cap_actual:.2f}")
                    s['e'] = False
                elif roi <= -0.90: # SL un poquito más ancho para no morir en el intento
                    cap_actual += gan_usd
                    print(f"\n❌ SL PROTECTOR {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}% (Piso: {piso:.2f}%)", end=' | ')
            
            else:
                if ops_abiertas < LIMITE_OPERACIONES:
                    k = cl.get_klines(symbol=m, interval='1m', limit=250) # Más velas para la EMA 200
                    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                    df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                    res = detectar_entrada(df)
                    if res:
                        s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                        ops_abiertas += 1
                        print(f"\n🚀 DISPARO {res} en {m} (Tendencia Confirmada)")
        time.sleep(1.2)
    except Exception as e:
        time.sleep(2); cl = c()
