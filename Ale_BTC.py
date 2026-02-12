import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta (Neto actual según tu último log)
cap_inicial = 18.73 
cap_actual = 18.73 
MIN_LOT = 15.0 
ops_count = 0
ops_ganadas = 0
st = {m: {'e': False, 'p': 0, 't': '', 'v': ''} for m in ms}

def detectar_entrada_real(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    c_act, o_act = df['close'].iloc[-1], df['open'].iloc[-1]
    c_ant, o_ant = df['close'].iloc[-2], df['open'].iloc[-2]
    e9, e27 = df['ema_9'].iloc[-1], df['ema_27'].iloc[-1]
    
    # REGLA DE ORO: La vela debe ser ENVOLVENTE (más grande que la anterior)
    # y cerrar REALMENTE del otro lado de la EMA 9.
    envolvente = abs(c_act - o_act) > abs(c_ant - o_ant)

    # --- DIRECCIÓN: SUBA (LONG) ---
    if c_act > o_act and c_act > e9 and e9 > e27 and envolvente:
        return "LONG", "ENVOLVENTE ALCISTA"

    # --- DIRECCIÓN: BAJA (SHORT) ---
    if c_act < o_act and c_act < e9 and e9 < e27 and envolvente:
        return "SHORT", "ENVOLVENTE BAJISTA"
        
    return None, None

print(f"🔱 IA QUANTUM: ARREGLO DE PRECISIÓN | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px_actual = df['close'].iloc[-1]
            
            # 1. BUSCAR ENTRADA CON MÁS FILTRO
            if not s['e']:
                dir, vela = detectar_entrada_real(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'] = dir, px_actual, True, vela
                    print(f"🔥 {m} | VELA: {vela} | {dir} en {px_actual}")
            
            # 2. MONITOR Y GIRO (Para que no se quede atrapada)
            elif s['e']:
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                print(f"📊 {m} | {s['t']} | Entró: {s['p']} | Ahora: {px_actual} | ROI: {roi:.2f}%")
                
                # SI VA MAL (-2%): Girar la tortilla
                if roi <= -2.0:
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1
                    print(f"🔄 GIRO EN {m}: Falló {s['t']}, entrando en {nueva_dir} a {px_actual}")
                    s['t'], s['p'], s['v'] = nueva_dir, px_actual, "VELA DE GIRO"
                
                # SI VA BIEN (+2%): Cobrar rápido
                elif roi >= 2.0:
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1
                    ops_ganadas += 1
                    s['e'] = False
                    print(f"💰 COSECHA en {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

                # RESUMEN CADA 5
                if ops_count > 0 and ops_count % 5 == 0:
                    print(f"\n📈 RESUMEN: Ops: {ops_count} | Ganadas: {ops_ganadas} | Neto: ${cap_actual:.2f}\n")
                    ops_count = 0 

        time.sleep(15)
    except Exception as e:
        time.sleep(10); cl = c()
