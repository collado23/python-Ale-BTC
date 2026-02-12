import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta
cap_actual = 19.52 
MIN_LOT = 15.0 
ops_count = 0
ops_ganadas = 0
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'be': False} for m in ms}

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

print(f"🔱 IA QUANTUM: PERSISTENCIA ACTIVADA | NETO: ${cap_actual}")

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
                    s['t'], s['p'], s['e'], s['v'], s['be'] = dir, px_actual, True, vela, False
                    print(f"🔥 {m} | ENTRADA: {dir} en {px_actual}")
            
            elif s['e']:
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                
                # 🛡️ BREAK EVEN (1.2%)
                if roi >= 1.2 and not s['be']:
                    s['be'] = True; print(f"🛡️ BE ACTIVADO en {m}")

                # 💰 COSECHA (2%) + RE-ENTRADA SI SIGUE LA TENDENCIA
                if roi >= 2.0:
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1; ops_ganadas += 1
                    print(f"💰 COSECHA {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")
                    
                    # ¿Sigue la tendencia?
                    sigue_long = (s['t'] == "LONG" and e9 > e27)
                    sigue_short = (s['t'] == "SHORT" and e9 < e27)
                    
                    if sigue_long or sigue_short:
                        s['p'] = px_actual; s['be'] = False; s['v'] = "PERSISTENCIA"
                        print(f"🔄 {m} CONTINÚA LA TENDENCIA. Re-entrando en {s['t']}...")
                    else:
                        s['e'] = False

                # 🛡️ SALIDA PROTEGIDA
                elif s['be'] and roi <= 0.2:
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1; s['e'] = False
                    print(f"🛡️ SALIDA SEGURA {m} | NETO: ${cap_actual:.2f}")

                # 🔄 GIRO POR STOP LOSS (-3%)
                elif roi <= -3.0:
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1
                    print(f"🔄 GIRO {m}: SL 3% tocado. Entrando en {nueva_dir}...")
                    s['t'], s['p'], s['v'], s['be'] = nueva_dir, px_actual, "VELA DE GIRO", False

            time.sleep(1); del df
        time.sleep(10)
    except Exception as e:
        time.sleep(5); cl = c()
