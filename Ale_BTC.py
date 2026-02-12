import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# --- CAPITAL ACTUAL ---
cap_actual = 18.61 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    # Reducimos indicadores al mínimo para ganar milisegundos
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    df['vol_ema'] = df['v'].rolling(10).mean()
    act, ant = df.iloc[-1], df.iloc[-2]
    
    vol_ok = act['v'] > (df['vol_ema'].iloc[-1] * 0.8)
    cuerpo = abs(act['close'] - act['open'])
    rango = act['high'] - act['low']
    mecha_ok = cuerpo > (rango * 0.70)
    env = cuerpo > abs(ant['close'] - ant['open'])
    
    if act['close'] > act['open'] and act['close'] > act['ema_9'] and act['ema_9'] > act['ema_27']:
        if env and mecha_ok and vol_ok: return "LONG", "ENVOLVENTE"
    if act['close'] < act['open'] and act['close'] < act['ema_9'] and act['ema_9'] < act['ema_27']:
        if env and mecha_ok and vol_ok: return "SHORT", "ENVOLVENTE"
    return None, None

print(f"🔱 IA QUANTUM V10 | MODO TURBO (BYPASS 14s) | ESCALERA 20% | CAP: ${cap_actual}")

while True:
    try:
        # CONSULTA MULTI-PRECIO (Consume casi nada de API)
        prices = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px_actual = prices[m]
            
            # 1. SI ESTÁ EN OPERACIÓN: Monitoreo Ultra-Rápido
            if s['e']:
                diff = (px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))
                
                # Escalera 0.5% -> 20.0%
                niv_cfg = {round(x * 0.5, 1): round((x * 0.5) - 0.4, 2) for x in range(1, 41)}
                niv_cfg[0.5] = 0.10

                for meta in sorted(niv_cfg.keys()):
                    if roi >= meta and meta > s['nivel']:
                        s['nivel'] = meta
                        print(f"\n🛡️ {m} Nivel {meta}% | Piso: {niv_cfg[meta]}% | GAN: ${gan_usd:.2f}")

                # Salida por Piso (Asegurar ganancia)
                if s['nivel'] in niv_cfg and roi <= niv_cfg[s['nivel']]:
                    cap_actual += gan_usd
                    print(f"\n✅ PISO {s['nivel']} ALCANZADO | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False

                # Stop Loss Corto (-0.7%)
                elif roi <= -0.7:
                    cap_actual += gan_usd
                    print(f"\n❌ SL CORTO | PNL: ${gan_usd:.2f}")
                    s['e'] = False

                print(f"📊 {m}: {roi:.2f}% (N{s['nivel']})", end=' | ')

            # 2. SI BUSCA ENTRADA: Solo aquí pedimos velas
            else:
                # Pedimos solo 30 velas (lo mínimo necesario)
                k = cl.get_klines(symbol=m, interval='1m', limit=30)
                df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'], s['nivel'] = dir, px_actual, True, vela, 0
                    print(f"\n🚀 DISPARO {dir} en {m} | Px: {px_actual}")
                del df

        # Pausa mínima de 0.3 segundos (para estar debajo del radar de Binance)
        time.sleep(0.3)

    except Exception as e:
        time.sleep(1); cl = c()
