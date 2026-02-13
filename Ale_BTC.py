import os, time
import pandas as pd
import numpy as np
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# CAPITAL ACTUAL (Ajustado según tus logs)
cap_actual = 18.45 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

# Función matemática para el RSI (Sin librerías extra)
def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def detectar_entrada(df):
    # EMAs y RSI calculados internamente
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean()
    df['rsi'] = calcular_rsi(df['close'])
    
    act = df.iloc[-1]
    
    # Filtros de Calidad: Volumen + Vela Sólida
    vol_ok = act['v'] > df['v'].rolling(10).mean().iloc[-1] * 1.1
    cuerpo = abs(act['close'] - act['open'])
    rango = act['high'] - act['low']
    mecha_ok = cuerpo > (rango * 0.7) # Evita velas con mucha mecha (falsos rompimientos)

    # LONG: Tendencia alcista + RSI > 53
    if act['close'] > act['ema_9'] > act['ema_27'] and act['rsi'] > 53:
        if vol_ok and mecha_ok: return "LONG"
    
    # SHORT: Tendencia bajista + RSI < 47
    if act['close'] < act['ema_9'] < act['ema_27'] and act['rsi'] < 47:
        if vol_ok and mecha_ok: return "SHORT"
            
    return None

print(f"🔱 IA QUANTUM V15 | SIN ERRORES DE PANDAS | ESCALERA 20% | CAP: ${cap_actual}")

while True:
    try:
        # CONSULTA RÁPIDA (Evita el bloqueo de 14 segundos)
        tickers = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = tickers[m]
            
            if s['e']:
                # Lógica de ROI y Escalera Blindada
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22 # x10 Apalancamiento
                gan_usd = (MIN_LOT * (roi / 100))
                
                # --- ESCALERA DE 0.5% EN 0.5% ---
                # Esta fórmula detecta niveles (0.5, 1.0, 1.5, 2.0...) automáticamente
                meta_actual = (int(roi * 2) / 2.0)
                if meta_actual > s['nivel'] and meta_actual >= 0.5:
                    s['nivel'] = meta_actual
                    print(f"\n🛡️ {m} BLOQUEÓ NIVEL {s['nivel']}% | ROI: {roi:.2f}%")

                # PISO DE SALIDA: Siempre 0.4% por debajo del nivel más alto
                piso = s['nivel'] - 0.4
                
                if s['nivel'] >= 0.5 and roi <= piso:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE EN PISO {s['nivel']}% | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                
                # Stop Loss Corto de Seguridad
                elif roi <= -0.7:
                    cap_actual += gan_usd
                    print(f"\n❌ SL CORTO en {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False

                print(f"📊 {m}: {roi:.2f}% (N{s['nivel']})", end=' | ')

            else:
                # Análisis de entrada (Solo pide velas si no está operando)
                k = cl.get_klines(symbol=m, interval='1m', limit=50)
                df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                
                res = detectar_entrada(df)
                if res:
                    s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                    print(f"\n🚀 DISPARO {res} en {m} | Px: {px}")

        # Pequeña pausa para no saturar la API
        time.sleep(1)

    except Exception as e:
        print(f"\n⚠️ Re-conectando... {e}")
        time.sleep(2); cl = c()
