import os, time
import pandas as pd
import numpy as np
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()

# CONFIGURACIÓN: 6 Monedas, Máximo 3 simultáneas
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
LIMITE_OPERACIONES = 3

cap_actual = 17.29 
MIN_LOT = 17.0 
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

def calcular_indicadores(df):
    # EMAs CORREGIDAS (9 para reacción, 21 para tendencia corta, 200 para tendencia larga)
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # RSI y MACD con Histograma
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
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
    
    # Filtros de Impulso y Volumen
    impulso_ok = abs(act['hist']) > abs(ant['hist'])
    vol_ok = act['v'] > df['v'].rolling(12).mean().iloc[-1] * 1.3
    
    # LÓGICA DE ENTRADA: Cruce de EMAs 9/21 + Tendencia 200 + MACD
    if act['close'] > act['ema200'] and act['ema9'] > act['ema21'] and act['rsi'] > 54 and act['hist'] > 0 and impulso_ok:
        if vol_ok: return "LONG"
    
    if act['close'] < act['ema200'] and act['ema9'] < act['ema21'] and act['rsi'] < 46 and act['hist'] < 0 and impulso_ok:
        if vol_ok: return "SHORT"
    return None

print(f"🔱 IA QUANTUM V25 | EMAs 9-21-200 | MÁX OPS: 3 | CAP: ${cap_actual}")

while True:
    try:
        ops_abiertas = sum(1 for m in ms if st[m]['e'])
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            
            if s['e']:
                # Monitoreo de indicadores en tiempo real para la salida
                k_fast = cl.get_klines(symbol=m, interval='1m', limit=50)
                df_fast = pd.DataFrame(k_fast, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                df_fast[['open','close']] = df_fast[['open','close']].astype(float)
                ema9_act = df_fast['close'].ewm(span=9, adjust=False).mean().iloc[-1]
                
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))

                # Escalera de niveles (cada 0.15%)
                meta_actual = (int(roi * 6.66) / 6.66)
                if meta_actual > s['nivel'] and meta_actual >= 0.4:
                    s['nivel'] = meta_actual

                # PISO DINÁMICO (Ajuste según nivel)
                distancia = 0.20 if s['nivel'] < 1.0 else 0.12
                piso = s['nivel'] - distancia
                
                # --- LÓGICA DE SALIDA V25 ---
                # 1. Salida por Piso (Trailing Stop)
                # 2. FRENO DE MANO: Si el precio cruza la EMA 9 en contra, cerramos para salvar el retroceso
                freno_ema = (s['t'] == "LONG" and px < ema9_act) or (s['t'] == "SHORT" and px > ema9_act)
                
                if (s['nivel'] >= 0.4 and roi <= piso) or (roi > 0.5 and freno_ema):
                    cap_actual += gan_usd
                    razon = "PISO" if not freno_ema else "EMA9-REVER"
                    print(f"\n✅ CIERRE {razon} en {m} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                elif roi <= -0.80:
                    cap_actual += gan_usd
                    print(f"\n❌ SL PROTECTOR {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}% (Piso: {piso:.2f}%)", end=' | ')
            
            else:
                if ops_abiertas < LIMITE_OPERACIONES:
                    k = cl.get_klines(symbol=m, interval='1m', limit=250)
                    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                    df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                    res = detectar_entrada(df)
                    if res:
                        s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                        ops_abiertas += 1
                        print(f"\n🚀 DISPARO {res} en {m} (Cruce 9/21)")

        time.sleep(0.8)
    except Exception as e:
        time.sleep(2); cl = c()
