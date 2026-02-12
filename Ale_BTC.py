import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de tu cuenta
cap_actual = 20.38 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': ''} for m in ms}

def detectar_confirmacion_9(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Amarilla
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Azul
    
    px = df['close'].iloc[-1]
    e9 = df['ema_9'].iloc[-1]
    e27 = df['ema_27'].iloc[-1]
    
    c_act = df['close'].iloc[-1]; o_act = df['open'].iloc[-1]
    c_ant = df['close'].iloc[-2]; o_ant = df['open'].iloc[-2]

    # REBOTE LARGO: Choque de velas + confirmación sobre/bajo la 9
    if c_act > o_act and c_ant < o_ant and px > e9 and e9 > e27:
        return "LONG"
    if c_act < o_act and c_ant > o_ant and px < e9 and e9 < e27:
        return "SHORT"
    return None

print(f"🔱 IA QUANTUM CON MONITOR ACTIVO | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px = df['close'].iloc[-1]
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean()
            
            # 1. SI NO HAY POSICIÓN: BUSCAR ENTRADA
            if not s['e']:
                senal = detectar_confirmacion_9(df)
                if senal:
                    s['t'], s['p'], s['e'] = senal, px, True
                    print(f"🚀 [ENTRADA] {m}: {senal} a {px}")
            
            # 2. SI HAY POSICIÓN: MONITOREAR Y BUSCAR SALIDA
            elif s['e']:
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                
                # AVISO EN VIVO: Esto es lo que pediste
                print(f"📊 [MONITOR {m}] {s['t']} | ROI: {roi:.2f}% | Precio: {px}")
                
                e9 = df['ema_9'].iloc[-1]
                e27 = df['ema_27'].iloc[-1]

                # Lógica de salida: 2% de ganancia o rotura de tendencia
                if roi >= 2.0 or (s['t'] == "LONG" and px < e27) or (s['t'] == "SHORT" and px > e27):
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    print(f"💰 [CIERRE] {m} | ROI FINAL: {roi:.2f}% | NUEVO NETO: ${cap_actual:.2f}")

        time.sleep(15) # Escaneo cada 15 segundos
    except Exception as e:
        time.sleep(10); cl = c()
