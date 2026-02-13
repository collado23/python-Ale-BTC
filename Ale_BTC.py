import os, time
import pandas as pd
import pandas_ta as ta # Necesitarás instalar: pip install pandas_ta
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 18.45 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    # Indicadores de fuerza
    df['ema_9'] = ta.ema(df['close'], length=9)
    df['ema_27'] = ta.ema(df['close'], length=27)
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    act, ant = df.iloc[-1], df.iloc[-2]
    
    # FILTRO ANTI-RANGO: Evitar el medio del RSI
    tendencia_fuerte = act['rsi'] > 55 or act['rsi'] < 45
    vol_ok = act['v'] > df['v'].rolling(10).mean().iloc[-1] * 1.2
    
    cuerpo = abs(act['close'] - act['open'])
    rango = act['high'] - act['low']
    mecha_ok = cuerpo > (rango * 0.75)
    
    # LONG: EMAs + RSI alcista + Volumen
    if act['close'] > act['ema_9'] > act['ema_27'] and act['rsi'] > 55:
        if mecha_ok and vol_ok: return "LONG", "FUERZA RSI"
        
    # SHORT: EMAs + RSI bajista + Volumen
    if act['close'] < act['ema_9'] < act['ema_27'] and act['rsi'] < 45:
        if mecha_ok and vol_ok: return "SHORT", "FUERZA RSI"
            
    return None, None

print(f"🔱 IA QUANTUM V11 | FILTRO RSI + VOLUMEN | CAP: ${cap_actual}")

while True:
    try:
        # Una sola llamada para los precios
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            
            if s['e']:
                # Lógica de Escalera de Blindaje (0.5 en 0.5 hasta 20%)
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))
                
                # Escalera automática
                meta_actual = (int(roi * 2) / 2.0)
                if meta_actual > s['nivel'] and meta_actual >= 0.5:
                    s['nivel'] = meta_actual
                    print(f"\n🛡️ {m} NIVEL {s['nivel']}% BLOQUEADO")

                # Salida por piso (Piso = Nivel - 0.4%)
                piso = s['nivel'] - 0.4
                if s['nivel'] >= 0.5 and roi <= piso:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE EN PISO {s['nivel']}% | GANANCIA: ${gan_usd:.2f}")
                    s['e'] = False
                
                # Stop Loss Dinámico según volatilidad
                elif roi <= -0.9:
                    cap_actual += gan_usd
                    print(f"\n❌ SL CORTADO | PNL: ${gan_usd:.2f}")
                    s['e'] = False

                print(f"📊 {m}: {roi:.2f}% (N{s['nivel']})", end=' | ')

            else:
                # Solo pedimos klines si no estamos operando esa moneda
                k = cl.get_klines(symbol=m, interval='1m', limit=50)
                df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'], s['nivel'] = dir, px, True, vela, 0
                    print(f"\n🚀 DISPARO {dir} en {m} con RSI {df['rsi'].iloc[-1]:.2f}")

        time.sleep(2) # Pausa técnica para evitar el bloqueo de 14s

    except Exception as e:
        time.sleep(5); cl = c()
