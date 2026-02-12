import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta (Neto según tu último log)
cap_actual = 19.27 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    c_act, o_act = df['close'].iloc[-1], df['open'].iloc[-1]
    c_ant, o_ant = df['close'].iloc[-2], df['open'].iloc[-2]
    e9, e27 = df['ema_9'].iloc[-1], df['ema_27'].iloc[-1]
    envolvente = abs(c_act - o_act) > abs(c_ant - o_ant)

    if c_act > o_act and c_act > e9 and e9 > e27 and envolvente:
        return "LONG", "ENVOLVENTE ALCISTA"
    if c_act < o_act and c_act < e9 and e9 < e27 and envolvente:
        return "SHORT", "ENVOLVENTE BAJISTA"
    return None, None

print(f"🔱 IA QUANTUM: ESCALERA DE 7 NIVELES | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px_actual = df['close'].iloc[-1]
            e9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
            e27 = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
            
            if not s['e']:
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'], s['nivel'] = dir, px_actual, True, vela, 0
                    print(f"🚀 {m} | DISPARO: {dir} en {px_actual}")
            
            elif s['e']:
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                
                # --- ESCALERA DE BLINDAJE (BREAKING BAD) ---
                if roi >= 1.2 and s['nivel'] < 1:
                    s['nivel'] = 1; print(f"🛡️ N1 (1.2%): Piso en 0.2% en {m}")
                elif roi >= 2.0 and s['nivel'] < 2:
                    s['nivel'] = 2; print(f"🔥 N2 (2.0%): Piso en 1.2% en {m}")
                elif roi >= 2.5 and s['nivel'] < 3:
                    s['nivel'] = 3; print(f"💎 N3 (2.5%): Piso en 2.0% en {m}")
                elif roi >= 3.5 and s['nivel'] < 4:
                    s['nivel'] = 4; print(f"🔱 N4 (3.5%): Piso en 2.5% en {m}")
                elif roi >= 4.0 and s['nivel'] < 5:
                    s['nivel'] = 5; print(f"⚡ N5 (4.0%): Piso en 3.5% en {m}")
                elif roi >= 4.5 and s['nivel'] < 6:
                    s['nivel'] = 6; print(f"🌟 N6 (4.5%): Piso en 4.0% en {m}")
                elif roi >= 5.0 and s['nivel'] < 7:
                    s['nivel'] = 7; print(f"👑 N7 (5.0%): Piso en 4.5% en {m}")
                
                # CIERRE TOTAL A 5.5% (META FINAL)
                if roi >= 5.5:
                    cap_actual += (MIN_LOT * (roi / 100))
                    print(f"💰 COSECHA TOTAL 5.5% en {m} | NETO: ${cap_actual:.2f}")
                    # Persistencia
                    if (s['t'] == "LONG" and e9 > e27) or (s['t'] == "SHORT" and e9 < e27):
                        s['p'], s['nivel'] = px_actual, 0
                        print(f"🔄 Sigue tendencia, re-entrando...")
                    else: s['e'] = False

                # --- CONTROL DE RETROCESOS (ZIG ZAG) ---
                salidas = {1: 0.2, 2: 1.2, 3: 2.0, 4: 2.5, 5: 3.5, 6: 4.0, 7: 4.5}
                if s['nivel'] in salidas and roi <= salidas[s['nivel']]:
                    cap_actual += (MIN_LOT * (roi / 100))
                    s['e'] = False
                    print(f"🛡️ SALIDA PROTEGIDA N{s['nivel']} en {m} | NETO: ${cap_actual:.2f}")

                # STOP LOSS / GIRO (-3%)
                elif roi <= -3.0:
                    cap_actual += (MIN_LOT * (roi / 100))
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    print(f"🔄 GIRO {m}: SL 3%. Entrando en {nueva_dir}")
                    s['t'], s['p'], s['nivel'] = nueva_dir, px_actual, 0

                print(f"📊 {m} | ROI: {roi:.2f}% | Nivel: {s['nivel']}", end='\r')

            time.sleep(1); del df
        time.sleep(10)
    except Exception as e:
        time.sleep(5); cl = c()
