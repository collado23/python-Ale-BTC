import os, time
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
LIMITE_OPERACIONES = 2

cap_actual = 17.14 
MIN_LOT = 17.0 
st = {m: {'e': False, 'p': 0, 't': '', 'max_px': 0, 'atr': 0} for m in ms}

def calcular_indicadores(df):
    # EMAs de Referencia
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema27'] = df['close'].ewm(span=27, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # ATR para el "Resorte"
    high_low = df['high'] - df['low']
    high_cp = abs(df['high'] - df['close'].shift())
    low_cp = abs(df['low'] - df['close'].shift())
    df['tr'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    df['atr'] = df['tr'].rolling(14).mean()
    
    # MACD para el gatillo
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['hist'] = df['macd'] - df['signal']
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    # Filtro de volumen
    vol_ok = act['v'] > df['v'].rolling(15).mean().iloc[-1] * 1.3
    
    if act['close'] > act['ema200'] and act['ema9'] > act['ema27'] and act['hist'] > 0 and vol_ok:
        return "LONG", act['atr']
    if act['close'] < act['ema200'] and act['ema9'] < act['ema27'] and act['hist'] < 0 and vol_ok:
        return "SHORT", act['atr']
    return None, 0

print(f"🔱 IA QUANTUM V27 | SISTEMA DE RESORTE (ATR) | CAP: ${cap_actual}")

while True:
    try:
        ops_abiertas = sum(1 for m in ms if st[m]['e'])
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            if s['e']:
                # Actualizar el punto máximo alcanzado (el estiramiento del resorte)
                if s['t'] == "LONG":
                    s['max_px'] = max(s['max_px'], px)
                    distancia_retroceso = (s['max_px'] - px) / s['p'] * 100 * 10
                else:
                    s['max_px'] = min(s['max_px'], px) if s['max_px'] > 0 else px
                    distancia_retroceso = (px - s['max_px']) / s['p'] * 100 * 10

                roi = ((px - s['p']) / s['p'] * 100 * 10) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 100 * 10)
                roi -= 0.22 # Comisiones
                gan_usd = (MIN_LOT * (roi / 100))

                # EL RESORTE: Si el precio retrocede más de 1.5 veces el ATR (en escala ROI)
                # o si el ROI cae 0.25% desde el máximo, saltamos.
                limite_resorte = 0.25 
                
                if roi > 0.4 and distancia_retroceso > limite_resorte:
                    cap_actual += gan_usd
                    print(f"\n🚀 RESORTE DISPARADO en {m} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                elif roi <= -0.90:
                    cap_actual += gan_usd
                    print(f"\n❌ STOP LOSS {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}% (Máx: {s['max_px']})", end=' | ')
            
            else:
                if ops_abiertas < LIMITE_OPERACIONES:
                    k = cl.get_klines(symbol=m, interval='1m', limit=100)
                    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                    df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                    res, atr_val = detectar_entrada(df)
                    if res:
                        s['t'], s['p'], s['e'], s['max_px'], s['atr'] = res, px, True, px, atr_val
                        ops_abiertas += 1
                        print(f"\n🎯 ENTRADA {res} en {m} | Resorte cargado")

        time.sleep(1)
    except Exception as e:
        time.sleep(2); cl = c()
