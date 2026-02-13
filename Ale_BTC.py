import os, time
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
LIMITE_OPERACIONES = 2

cap_actual = 16.54 
MIN_LOT = 16.5 # Ajustado para cuidar el margen restante
st = {m: {'e': False, 'p': 0, 't': '', 'max_px': 0} for m in ms}

def calcular_indicadores(df):
    # EMAs de 35 y 50 (Tu nueva configuración)
    df['ema35'] = df['close'].ewm(span=35, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # MACD para confirmar el momentum
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['hist'] = df['macd'] - df['signal']
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    ant = df.iloc[-2]
    
    # Filtro de fuerza: La distancia entre EMAs debe aumentar
    distancia_act = abs(act['ema35'] - act['ema50'])
    distancia_ant = abs(ant['ema35'] - ant['ema50'])
    tendencia_abriendose = distancia_act > distancia_ant

    vol_ok = act['v'] > df['v'].rolling(20).mean().iloc[-1] * 1.3
    
    # LONG: Precio > 200 y 35 > 50 confirmando apertura
    if act['close'] > act['ema200'] and act['ema35'] > act['ema50'] and tendencia_abriendose and act['hist'] > 0:
        if vol_ok: return "LONG"
    
    # SHORT: Precio < 200 y 35 < 50 confirmando apertura
    if act['close'] < act['ema200'] and act['ema35'] < act['ema50'] and tendencia_abriendose and act['hist'] < 0:
        if vol_ok: return "SHORT"
    return None

print(f"🔱 IA QUANTUM V28 | ESTRATEGIA EMAs 35/50 | CAP: ${cap_actual}")

while True:
    try:
        ops_abiertas = sum(1 for m in ms if st[m]['e'])
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            if s['e']:
                # Lógica del Resorte mejorada para tendencias largas
                if s['t'] == "LONG":
                    s['max_px'] = max(s['max_px'], px)
                    retroceso = (s['max_px'] - px) / s['p'] * 1000
                else:
                    s['max_px'] = min(s['max_px'], px) if s['max_px'] > 0 else px
                    retroceso = (px - s['max_px']) / s['p'] * 1000

                roi = ((px - s['p']) / s['p'] * 1000) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 1000)
                roi -= 0.22 # Comisiones
                gan_usd = (MIN_LOT * (roi / 100))

                # Ajuste de salida: si ya ganamos 0.5%, el resorte se activa a los 0.3% de retroceso
                if roi > 0.50 and retroceso > 0.30:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE TENDENCIA {m} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                elif roi <= -1.2: # SL más amplio para aguantar la EMA 50
                    cap_actual += gan_usd
                    print(f"\n❌ STOP LOSS {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}% (Máx: {s['max_px']})", end=' | ')
            
            else:
                if ops_abiertas < LIMITE_OPERACIONES:
                    k = cl.get_klines(symbol=m, interval='1m', limit=300) # Más velas para EMAs largas
                    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                    df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                    res = detectar_entrada(df)
                    if res:
                        s['t'], s['p'], s['e'], s['max_px'] = res, px, True, px
                        ops_abiertas += 1
                        print(f"\n🎯 TENDENCIA DETECTADA {res} en {m} (EMAs 35/50)")

        time.sleep(1.2)
    except Exception as e:
        time.sleep(2); cl = c()
