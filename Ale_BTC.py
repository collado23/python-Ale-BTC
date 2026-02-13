import os, time
import pandas as pd
import pandas_ta as ta
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# CAPITAL ACTUALIZADO (Ajustar según tu balance real)
cap_actual = 18.45 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

def obtener_datos(m):
    # Pedimos solo 50 velas para no saturar la API
    k = cl.get_klines(symbol=m, interval='1m', limit=50)
    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
    df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
    
    # Indicadores Clave
    df['ema_9'] = ta.ema(df['close'], length=9)
    df['ema_27'] = ta.ema(df['close'], length=27)
    df['rsi'] = ta.rsi(df['close'], length=14)
    adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
    df['adx'] = adx_df['ADX_14']
    return df

print(f"🔱 IA QUANTUM V13 | ESCALERA 20% | BYPASS 14s | CAP: ${cap_actual}")

while True:
    try:
        # CONSULTA RÁPIDA: Trae precios de TODO Binance de una sola vez
        # Esto es lo que evita que te bloqueen por 14 segundos
        precios_all = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios_all[m]
            
            if s['e']:
                # --- LÓGICA DE MONITOREO (DENTRO DE OPERACIÓN) ---
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))
                
                # ESCALERA DE 0.5 EN 0.5 HASTA EL 20%
                # Si el ROI es 1.57, meta_actual es 1.5
                meta_actual = (int(roi * 2) / 2.0) 
                
                if meta_actual > s['nivel'] and meta_actual >= 0.5:
                    s['nivel'] = meta_actual
                    print(f"\n🛡️ {m} SUBIÓ A NIVEL {s['nivel']}% | ASEGURANDO GANANCIA")

                # PISO DE SALIDA: Siempre 0.4% por debajo del nivel alcanzado
                piso = s['nivel'] - 0.4
                
                if s['nivel'] >= 0.5 and roi <= piso:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE EN PISO {s['nivel']}% | GANASTE: ${gan_usd:.2f} | TOTAL: ${cap_actual:.2f}")
                    s['e'] = False
                
                elif roi <= -0.7: # Stop Loss corto para proteger
                    cap_actual += gan_usd
                    print(f"\n❌ SL CORTADO en {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False

                print(f"📊 {m}: {roi:.2f}% (N{s['nivel']})", end=' | ')

            else:
                # --- LÓGICA DE ENTRADA (BUSCANDO OPORTUNIDAD) ---
                df = obtener_datos(m)
                act = df.iloc[-1]
                
                # Filtros: Fuerza (ADX > 20) + Tendencia (RSI) + Volumen
                vol_ok = act['v'] > df['v'].rolling(10).mean().iloc[-1] * 1.1
                fuerza = act['adx'] > 20
                
                # LONG
                if fuerza and vol_ok and act['close'] > act['ema_9'] > act['ema_27'] and act['rsi'] > 53:
                    s['t'], s['p'], s['e'], s['nivel'] = "LONG", px, True, 0
                    print(f"\n🚀 DISPARO LONG en {m} | Px: {px}")
                
                # SHORT
                elif fuerza and vol_ok and act['close'] < act['ema_9'] < act['ema_27'] and act['rsi'] < 47:
                    s['t'], s['p'], s['e'], s['nivel'] = "SHORT", px, True, 0
                    print(f"\n🚀 DISPARO SHORT en {m} | Px: {px}")
                
                del df

        # Pausa de 1 segundo para mantener la API "fresca"
        time.sleep(1)

    except Exception as e:
        print(f"\n⚠️ Error: {e}")
        time.sleep(2); cl = c()
