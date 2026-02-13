import os, time
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
LIMITE_OPERACIONES = 2 # Bajamos a 2 para concentrar el capital y no dispersar

cap_actual = 17.14 
MIN_LOT = 16.0 
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

def calcular_indicadores(df):
    # EMAs Robustas
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema27'] = df['close'].ewm(span=27, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # ADX Manual (Para medir fuerza de tendencia)
    plus_dm = df['high'].diff()
    minus_dm = df['low'].diff()
    tr = pd.concat([df['high'] - df['low'], abs(df['high'] - df['close'].shift()), abs(df['low'] - df['close'].shift())], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0).rolling(14).mean() / atr)
    minus_di = 100 * (minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0).rolling(14).mean() / atr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx'] = dx.rolling(14).mean()

    # MACD
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['hist'] = df['macd'] - df['signal']
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    
    # FILTRO CLAVE: Solo si el ADX > 25 (Hay tendencia fuerte)
    tendencia_fuerte = act['adx'] > 25
    vol_ok = act['v'] > df['v'].rolling(15).mean().iloc[-1] * 1.4

    if tendencia_fuerte and vol_ok:
        if act['close'] > act['ema200'] and act['ema9'] > act['ema27'] and act['hist'] > 0:
            return "LONG"
        if act['close'] < act['ema200'] and act['ema9'] < act['ema27'] and act['hist'] < 0:
            return "SHORT"
    return None

print(f"🔱 IA QUANTUM V26 | FILTRO ADX ACTIVO | CAP: ${cap_actual}")

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

                if roi > s['nivel'] + 0.2:
                    s['nivel'] = max(s['nivel'], int(roi * 4) / 4.0)

                # PISO MÁS PACIENTE (0.30% de aire)
                piso = s['nivel'] - 0.30
                
                # Salida por piso o Stop Loss
                if (s['nivel'] >= 0.5 and roi <= piso) or roi <= -1.1:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE ESTRATÉGICO {m} | PNL: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}%", end=' | ')
            
            else:
                if ops_abiertas < LIMITE_OPERACIONES:
                    k = cl.get_klines(symbol=m, interval='1m', limit=100)
                    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                    df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                    res = detectar_entrada(df)
                    if res:
                        s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                        ops_abiertas += 1
                        print(f"\n🚀 DISPARO {res} en {m} (ADX: Confirmado)")

        time.sleep(1.5)
    except Exception as e:
        time.sleep(2); cl = c()
