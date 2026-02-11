import os, time
import pandas as pd
from binance.client import Client 

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
# Capital actualizado tras el último log
cap_actual = 28.01 
st = {m: {'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def calcular_cerebro(df):
    # Análisis profundo de 30 velas para predecir color
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['vel'] = df['close'].diff()
    df['acel'] = df['vel'].diff()
    # Z-Score sobre 30 velas para evitar el final del movimiento
    df['rango'] = df['high'] - df['low']
    df['z_score'] = (df['rango'] - df['rango'].rolling(30).mean()) / df['rango'].rolling(30).std()
    return df

def predictor_color(df):
    act = df.iloc[-1]; prev = df.iloc[-2]; ant = df.iloc[-3]
    
    # Identificación de colores
    v1 = act['close'] > act['open'] # Actual Verde
    v2 = prev['close'] > prev['open'] # Anterior Verde
    r1 = act['close'] < act['open'] # Actual Roja
    r2 = prev['close'] < prev['open'] # Anterior Roja
    
    cuerpo_act = abs(act['close'] - act['open'])
    promedio_cuerpo = abs(df['close'] - df['open']).tail(30).mean()
    
    # Solo entramos si la vela tiene fuerza (cuerpo mayor al promedio)
    fuerza = cuerpo_act > promedio_cuerpo

    # GATILLO LONG: 2 Verdes seguidas + Fuerza + Tendencia
    if (act['close'] > act['ema_200']) and v1 and v2 and fuerza:
        if act['z_score'] < 1.3: return "🟩" # Predice continuación verde

    # GATILLO SHORT: 2 Rojas seguidas + Fuerza + Tendencia
    if (act['close'] < act['ema_200']) and r1 and r2 and fuerza:
        if act['z_score'] < 1.3: return "🟥" # Predice continuación roja
            
    return "."

print(f"🔱 IA QUANTUM BLINDADA | CAP: ${cap_actual} | 30 VELAS")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=150)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            senal = predictor_color(df)

            if not s['e']:
                if senal != ".":
                    s['t'] = "LONG" if senal == "🟩" else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 {senal} ENTRADA {m} | CAP: ${cap_actual:.2f}")
            else:
                # --- GESTIÓN DE RIESGO CERO ---
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                
                # BLINDAJE ULTRA RÁPIDO: Si toca 0.05%, ya no perdemos.
                if roi >= 0.05: s['b'] = True 
                
                # Trailing Stop pegado para asegurar centavos
                t_stop = (roi <= (s['m'] - 0.05)) if s['m'] >= 0.15 else False
                
                # Stop Loss Quirúrgico (Para que no haya pérdida grande)
                sl_micro = roi <= -0.20

                if (s['b'] and roi <= 0.01) or t_stop or sl_emergencia:
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['o'] += 1; s['e'] = False
                    est = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{est} {s['t']} {roi:.2f}%")
                    print(f"\n{est} SALIDA {m} {roi:.2f}% | NETO: ${cap_actual:.2f}")

                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*32}╗\n║ 📊 REPORTE 5 OPS - {m[:3]} ║")
                        for line in s['h']: print(f"║ {line.ljust(28)} ║")
                        print(f"╠{'═'*32}╣\n║ CAP FINAL: ${cap_actual:.2f}   ║\n╚{'═'*32}╝\n")
                        s['h'] = []
        time.sleep(15)
    except:
        time.sleep(10); cl = c()
