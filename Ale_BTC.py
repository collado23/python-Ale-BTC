import os, time
import pandas as pd
from binance.client import Client 

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
# Capital actualizado
cap_actual = 27.84 
st = {m: {'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def calcular_cerebro(df):
    df['ema_fast'] = df['close'].ewm(span=10, adjust=False).mean()
    df['cuerpo'] = df['close'] - df['open']
    return df

def detectar_color_fuerte(df):
    v1 = df.iloc[-1]; v2 = df.iloc[-2]
    # Necesitamos 2 velas del mismo color para confirmar tendencia
    verde = v1['cuerpo'] > 0 and v2['cuerpo'] > 0
    roja = v1['cuerpo'] < 0 and v2['cuerpo'] < 0
    
    if verde and (v1['close'] > df['ema_fast'].iloc[-1]): return "🟩"
    if roja and (v1['close'] < df['ema_fast'].iloc[-1]): return "🟥"
    return "."

print(f"🔱 RASTREADOR DE PRECIO ON | CAP: ${cap_actual} | SIGUIENDO TENDENCIA")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            senal = detectar_color_fuerte(df)

            if not s['e']:
                if senal != ".":
                    s['t'] = "LONG" if senal == "🟩" else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 {senal} ENTRADA EN {m} | SIGUIENDO PRECIO...")
            else:
                # --- LÓGICA DE RASTREO (TRAILING STOP) ---
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                
                # Actualizar el máximo alcanzado para el rastreo
                if roi > s['m']: s['m'] = roi
                
                # Activar blindaje de capital
                if roi >= 0.10: s['b'] = True 
                
                # EL RASTREADOR: Si el precio rebota 0.08% desde el máximo, cerramos.
                # Solo se activa si ya estamos ganando al menos 0.20%
                rebote = (roi <= (s['m'] - 0.08)) if s['m'] >= 0.20 else False
                
                # Cierre por cambio de color brusco (Protección de pérdida)
                cambio_color = (s['t'] == "LONG" and df['cuerpo'].iloc[-1] < -0.05) or \
                               (s['t'] == "SHORT" and df['cuerpo'].iloc[-1] > 0.05)

                if rebote or (s['b'] and roi <= 0.01) or roi <= -0.28 or cambio_color:
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['o'] += 1; s['e'] = False
                    est = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{est} {s['t']} {roi:.2f}%")
                    print(f"\n{est} SALIDA {m} {roi:.2f}% | MÁX LOGRADO: {s['m']:.2f}% | NETO: ${cap_actual:.2f}")

                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*32}╗\n║ 📊 REPORTE DE RASTREO - {m[:3]} ║")
                        for line in s['h']: print(f"║ {line.ljust(28)} ║")
                        print(f"╠{'═'*32}╣\n║ CAP FINAL: ${cap_actual:.2f}   ║\n╚{'═'*32}╝\n")
                        s['h'] = []
        time.sleep(15)
    except:
        time.sleep(10); cl = c()
