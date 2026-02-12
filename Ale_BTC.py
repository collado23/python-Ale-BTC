import os, time
import pandas as pd
from binance.client import Client

# Conexión Segura
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta actualizado
cap_inicial = 18.72 
cap_actual = 18.72 
MIN_LOT = 15.0 
ops_count = 0
ops_ganadas = 0
st = {m: {'e': False, 'p': 0, 't': '', 'v': ''} for m in ms}

def detectar_entrada(df):
    # Usamos menos velas (50) para que sea más rápido
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

print(f"🔱 IA QUANTUM FLUIDA | NETO: ${cap_actual} | 3 MONEDAS")

while True:
    try:
        for m in ms:
            s = st[m]
            # Traemos solo lo necesario para no saturar
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px_actual = df['close'].iloc[-1]
            
            if not s['e']:
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'] = dir, px_actual, True, vela
                    print(f"🔥 {m} | VELA: {vela} | {dir} en {px_actual}")
            
            elif s['e']:
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                print(f"📊 {m} | {s['v']} | ROI: {roi:.2f}% | Precio: {px_actual}")
                
                # GIRO (-2%)
                if roi <= -2.0:
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1
                    print(f"🔄 GIRO {m}: Entrando en {nueva_dir} a {px_actual}")
                    s['t'], s['p'], s['v'] = nueva_dir, px_actual, "VELA DE GIRO"
                
                # COSECHA (+2%)
                elif roi >= 2.0:
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1
                    ops_ganadas += 1
                    s['e'] = False
                    print(f"💰 COSECHA {m} | NETO: ${cap_actual:.2f}")

                if ops_count >= 5:
                    print(f"\n📈 RESUMEN: Ops: {ops_count} | Ganadas: {ops_ganadas} | Neto: ${cap_actual:.2f}\n")
                    ops_count = 0
            
            time.sleep(1) # Pausa de 1 segundo entre monedas para no tildarse
            del df # Borra datos de memoria

        time.sleep(10) # Pausa general de ciclo
    except Exception as e:
        time.sleep(5)
        cl = c()
