import os, time
import pandas as pd
from binance.client import Client 

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 24.17 # Capital para reiniciar recuperación
st = {m: {'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def calcular_cerebro(df):
    # Volvemos a la configuración estable de EMAs
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_35'] = df['close'].ewm(span=35, adjust=False).mean()
    df['rango'] = df['high'] - df['low']
    # Z-Score de 20 velas para filtrar entradas tardías
    df['z_score'] = (df['rango'] - df['rango'].rolling(20).mean()) / df['rango'].rolling(20).std()
    return df

def ni(df):
    act = df.iloc[-1]; prev = df.iloc[-2]
    cuerpo = abs(act['close'] - act['open']) or 0.001
    l_ok = (act['close'] > act['ema_200']) and (act['ema_35'] > act['ema_50'])
    s_ok = (act['close'] < act['ema_200']) and (act['ema_35'] < act['ema_50'])
    
    # LONG (Martillo o Rompe Techo)
    m_inf = act['open'] - act['low'] if act['close'] > act['open'] else act['close'] - act['low']
    if l_ok and (m_inf > cuerpo * 3.2) and (act['close'] > act['open']): return "🔨"
    if l_ok and (act['close'] > prev['high']) and (act['z_score'] < 1.7): return "V"
    
    # SHORT (Estrella o Rompe Suelo)
    m_sup = act['high'] - act['close'] if act['close'] > act['open'] else act['high'] - act['open']
    if s_ok and (m_sup > cuerpo * 2.8) and (act['close'] < act['open']): return "☄️"
    if s_ok and (act['close'] < prev['low']) and (act['z_score'] < 1.9): return "R"
    return "."

print(f"🔱 REGRESO AL MODO EQUILIBRIO | CAP: ${cap_actual} | SL: -0.30%")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=201)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            ptr = ni(df)

            if not s['e']:
                if ptr != ".":
                    s['t'] = "LONG" if ptr in ["🔨", "V"] else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 ENTRADA {m} {s['t']} ({ptr})")
            else:
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                
                # --- GESTIÓN MATEMÁTICA ---
                # 1. Blindaje al 0.10%: Protege capital rápido
                if roi >= 0.10: s['b'] = True 
                
                # 2. Trailing Stop: Solo busca cerrar si ya hay ganancia real (>0.35%)
                dist = 0.10 if s['t'] == "SHORT" else 0.14
                t_stop = (roi <= (s['m'] - dist)) if s['m'] >= 0.35 else False
                
                # 3. Stop Loss Fijo y Estricto (Tu pedido: poca pérdida)
                sl_estricto = roi <= -0.30

                if (s['b'] and roi <= 0.01) or t_stop or sl_estricto:
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
