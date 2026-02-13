import os, time
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 17.40 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

def calcular_indicadores(df):
    # RSI y MACD Manuales
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema27'] = df['close'].ewm(span=27, adjust=False).mean()
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    # Filtro de volumen más estricto para evitar entradas falsas
    vol_ok = act['v'] > df['v'].rolling(10).mean().iloc[-1] * 1.2
    macd_confirmado = abs(act['macd'] - act['signal']) > (act['macd'] * 0.1) # Pendiente real
    
    if act['close'] > act['ema9'] > act['ema27'] and act['rsi'] > 54 and act['macd'] > act['signal'] and macd_confirmado:
        if vol_ok: return "LONG"
    if act['close'] < act['ema9'] < act['ema27'] and act['rsi'] < 46 and act['macd'] < act['signal'] and macd_confirmado:
        if vol_ok: return "SHORT"
    return None

print(f"🔱 IA QUANTUM V17 | PROTECCIÓN ULTRA-PEGADA | CAP: ${cap_actual}")

while True:
    try:
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        for m in ms:
            s = st[m]
            px = precios[m]
            if s['e']:
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))

                # --- NUEVA ESCALERA CORTA (0.2 en 0.2) ---
                # Si el ROI sube, el nivel sube más rápido para "pegar" el piso
                meta_actual = (int(roi * 5) / 5.0) # Detecta niveles cada 0.2%
                if meta_actual > s['nivel'] and meta_actual >= 0.4:
                    s['nivel'] = meta_actual
                    print(f"\n🛡️ {m} PROTECCIÓN ACTIVADA: {s['nivel']}%")

                # PISO ULTRA AJUSTADO (A solo 0.15% de distancia)
                piso = s['nivel'] - 0.15
                
                if s['nivel'] >= 0.4 and roi <= piso:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE QUIRÚRGICO {m} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                elif roi <= -0.65: # Stop Loss un poco más ajustado
                    cap_actual += gan_usd
                    print(f"\n❌ SL PROTECTOR {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}% (Piso: {piso:.2f}%)", end=' | ')
            else:
                k = cl.get_klines(symbol=m, interval='1m', limit=60)
                df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                res = detectar_entrada(df)
                if res:
                    s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                    print(f"\n🚀 DISPARO {res} en {m}")
        time.sleep(1)
    except Exception as e:
        time.sleep(2); cl = c()
