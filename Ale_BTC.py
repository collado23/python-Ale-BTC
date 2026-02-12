import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT'] 

# --- CAPITAL ACTUALIZADO ---
cap_actual = 18.61 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    df['vol_ema'] = df['v'].rolling(10).mean()
    act, ant = df.iloc[-1], df.iloc[-2]
    
    vol_ok = act['v'] > df['vol_ema'].iloc[-1]
    cuerpo = abs(act['close'] - act['open'])
    rango = act['high'] - act['low']
    mecha_ok = cuerpo > (rango * 0.75)
    env = cuerpo > abs(ant['close'] - ant['open'])
    
    if act['close'] > act['open'] and act['close'] > act['ema_9'] and act['ema_9'] > act['ema_27']:
        if env and mecha_ok and vol_ok: return "LONG", "ENVOLVENTE"
    if act['close'] < act['open'] and act['close'] < act['ema_9'] and act['ema_9'] < act['ema_27']:
        if env and mecha_ok and vol_ok: return "SHORT", "ENVOLVENTE"
    return None, None

print(f"🔱 IA QUANTUM V6 | ESCALERA 0.5% | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
            px = df['close'].iloc[-1]
            e27 = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
            
            if not s['e']:
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'], s['nivel'] = dir, px, True, vela, 0
                    print(f"\n🚀 {m} | ENTRADA {dir} | Px: {px}")
            
            elif s['e']:
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))
                
                # --- ESCALERA DE 0.5 EN 0.5 (ALTA RESOLUCIÓN) ---
                # Formato: meta : piso (siempre dejamos un margen de 0.3% o 0.4%)
                niv_cfg = {
                    0.5: 0.10, 1.0: 0.60, 1.5: 1.10, 2.0: 1.60, 
                    2.5: 2.10, 3.0: 2.60, 3.5: 3.10, 4.0: 3.60,
                    4.5: 4.10, 5.0: 4.60, 5.5: 5.10, 6.0: 5.60,
                    6.5: 6.10, 7.0: 6.60, 7.5: 7.10, 8.0: 7.60,
                    8.5: 8.10, 9.0: 8.60, 9.5: 9.10, 10.0: 9.60
                }

                # Actualizar Nivel dinámicamente
                for meta in sorted(niv_cfg.keys()):
                    if roi >= meta and meta > s['nivel']:
                        s['nivel'] = meta
                        print(f"\n🛡️ {m} Nivel {meta} | PNL: ${gan_usd:.2f} | Piso: {niv_cfg[meta]}%")

                # --- LÓGICA DE SALIDAS ---
                
                # 1. Salida por Piso (Breakeven 0.5, 1, 1.5...)
                if s['nivel'] in niv_cfg:
                    if roi <= niv_cfg[s['nivel']]:
                        cap_actual += gan_usd
                        print(f"\n✅ PISO {s['nivel']}% ALCANZADO | GANASTE: ${gan_usd:.2f} | TOTAL: ${cap_actual:.2f}")
                        s['e'] = False

                # 2. SALIDA POR GIRO (Si cruza EMA27, cerramos y giramos)
                elif (s['t'] == "LONG" and px < e27) or (s['t'] == "SHORT" and px > e27):
                    cap_actual += gan_usd
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    print(f"\n🔄 GIRO DE TENDENCIA | PNL: ${gan_usd:.2f} | CAMBIO A {nueva_dir}")
                    # Cerramos la anterior y entramos en la nueva tendencia
                    s['t'], s['p'], s['nivel'] = nueva_dir, px, 0

                # 3. STOP LOSS CORTO (Bajado a -0.7% para máxima protección)
                elif roi <= -0.7:
                    cap_actual += gan_usd
                    print(f"\n❌ SL CORTO | PNL: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False

                emoji = "🟢" if gan_usd >= 0 else "🔴"
                print(f"📊 {m} | {emoji} ${gan_usd:.2f} ({roi:.2f}%) | NIV: {s['nivel']}", end='\r')

            time.sleep(1)
            del df
    except Exception as e:
        time.sleep(5); cl = c()
