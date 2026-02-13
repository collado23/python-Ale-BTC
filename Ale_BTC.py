import os, time
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 18.45 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

# --- CÁLCULOS TÉCNICOS PROPIOS ---
def calcular_indicadores(df):
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    # MACD (12, 26, 9)
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # EMAs de Tendencia
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema27'] = df['close'].ewm(span=27, adjust=False).mean()
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    ant = df.iloc[-2]
    
    # Filtros de Calidad
    vol_ok = act['v'] > df['v'].rolling(10).mean().iloc[-1] * 1.1
    cuerpo = abs(act['close'] - act['open'])
    mecha_ok = cuerpo > ((act['high'] - act['low']) * 0.7)

    # LÓGICA MACD: Cruce de líneas
    macd_alcista = act['macd'] > act['signal']
    macd_bajista = act['macd'] < act['signal']

    # LONG: EMAs + RSI > 50 + MACD Alza
    if act['close'] > act['ema9'] > act['ema27'] and act['rsi'] > 52 and macd_alcista:
        if vol_ok and mecha_ok: return "LONG"
    
    # SHORT: EMAs + RSI < 50 + MACD Baja
    if act['close'] < act['ema9'] < act['ema27'] and act['rsi'] < 48 and macd_bajista:
        if vol_ok and mecha_ok: return "SHORT"
            
    return None

print(f"🔱 IA QUANTUM V16 | FILTRO MACD + RSI | ESCALERA 20% | CAP: ${cap_actual}")

while True:
    try:
        tickers = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = tickers[m]
            
            if s['e']:
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))
                
                # Escalera 0.5% en 0.5%
                meta_actual = (int(roi * 2) / 2.0)
                if meta_actual > s['nivel'] and meta_actual >= 0.5:
                    s['nivel'] = meta_actual
                    print(f"\n🛡️ {m} NIVEL {s['nivel']}% BLOQUEADO")

                piso = s['nivel'] - 0.4
                if s['nivel'] >= 0.5 and roi <= piso:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE MACD-PROTECT {m} | GANASTE: ${gan_usd:.2f}")
                    s['e'] = False
                
                elif roi <= -0.7:
                    cap_actual += gan_usd
                    print(f"\n❌ SL CORTADO | PNL: ${gan_usd:.2f}")
                    s['e'] = False

                print(f"📊 {m}: {roi:.2f}% (N{s['nivel']})", end=' | ')

            else:
                k = cl.get_klines(symbol=m, interval='1m', limit=60)
                df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                
                res = detectar_entrada(df)
                if res:
                    s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                    print(f"\n🚀 DISPARO {res} (CONFIRMADO MACD) en {m}")

        time.sleep(1.5)

    except Exception as e:
        time.sleep(2); cl = c()
