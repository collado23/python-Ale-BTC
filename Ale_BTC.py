import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))  

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# --- CONFIGURACIÓN DE CAPITAL (Ajustado a tu balance actual) ---
cap_actual = 18.89 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    df['vol_ema'] = df['v'].rolling(10).mean()
    
    act = df.iloc[-1]
    ant = df.iloc[-2]
    
    volumen_fuerte = act['v'] > df['vol_ema'].iloc[-1]
    cuerpo = abs(act['close'] - act['open'])
    rango_total = act['high'] - act['low']
    mecha_ok = cuerpo > (rango_total * 0.7) 
    envolvente = cuerpo > abs(ant['close'] - ant['open'])
    distancia_ema = abs(act['close'] - act['ema_9']) / act['ema_9']
    cerca_ema = distancia_ema < 0.0025

    if act['close'] > act['open'] and act['close'] > act['ema_9'] and act['ema_9'] > act['ema_27']:
        if envolvente and mecha_ok and cerca_ema and volumen_fuerte:
            return "LONG", "VOLUMEN + ENVOLVENTE"
            
    if act['close'] < act['open'] and act['close'] < act['ema_9'] and act['ema_9'] < act['ema_27']:
        if envolvente and mecha_ok and cerca_ema and volumen_fuerte:
            return "SHORT", "VOLUMEN + ENVOLVENTE"
            
    return None, None

print(f"🔱 IA QUANTUM V3 PRO | BREAKEVEN 0.5% ACTIVADO | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
            px_actual = df['close'].iloc[-1]
            
            e9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
            e27 = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
            
            if not s['e']:
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'], s['nivel'] = dir, px_actual, True, vela, 0
                    print(f"\n🚀 {m} | DISPARO {dir} | Precio: {px_actual}")
            
            elif s['e']:
                diff = (px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']
                roi = (diff * 100 * 10) - 0.22
                ganancia_usd = (MIN_LOT * (roi / 100))
                
                # --- NUEVA ESCALERA: ARRANCA EN 0.5% ---
                # Formato: Nivel: (Meta para activar, Piso de protección)
                niv_cfg = {
                    0.5: (0.5, 0.1),  # <-- NUEVO BREAKEVEN RÁPIDO
                    1: (1.2, 0.5), 
                    2: (2.0, 1.2), 
                    3: (2.5, 2.0), 
                    4: (3.5, 2.5),
                    5: (4.0, 3.5), 
                    6: (4.5, 4.0), 
                    7: (5.0, 4.5), 
                    8: (5.5, 5.0),
                    9: (6.0, 5.5), 
                    10: (6.5, 6.0), 
                    11: (7.5, 7.0), 
                    12: (8.5, 8.0),
                    13: (9.0, 8.5), 
                    14: (9.5, 9.0), 
                    15: (10.0, 9.5)
                }

                # Actualizar Nivel
                for n, (meta, piso) in niv_cfg.items():
                    if roi >= meta and s['nivel'] < n:
                        s['nivel'] = n
                        print(f"\n🛡️ {m} NIVEL {n} ALCANZADO (Protección en {piso}%)")

                # --- LÓGICA DE SALIDAS ---
                
                # 1. Salida por Piso (Blindaje)
                if s['nivel'] in niv_cfg:
                    if roi <= niv_cfg[s['nivel']][1]:
                        cap_actual += ganancia_usd
                        print(f"\n✅ CIERRE EN NIVEL {s['nivel']} | PNL: ${ganancia_usd:.2f} | NETO: ${cap_actual:.2f}")
                        s['e'] = False

                # 2. Salida por Cruce Inverso (Emergencia)
                elif (s['t'] == "LONG" and px_actual < e27) or (s['t'] == "SHORT" and px_actual > e27):
                    cap_actual += ganancia_usd
                    print(f"\n⚠️ SALIDA CRUCE INVERSO | PNL: ${ganancia_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False

                # 3. Stop Loss Final
                elif roi <= -1.5: # Lo bajamos a 1.5% para proteger más
                    cap_actual += ganancia_usd
                    print(f"\n❌ STOP LOSS | PNL: ${ganancia_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False

                # MONITOR
                emoji = "🟢" if ganancia_usd >= 0 else "🔴"
                print(f"📊 {m} | {emoji} PNL: ${ganancia_usd:.2f} ({roi:.2f}%) | NIVEL: {s['nivel']}", end='\r')

            time.sleep(1)
            del df
    except Exception as e:
        print(f"\n⚠️ Re-conectando... {e}")
        time.sleep(5); cl = c()
