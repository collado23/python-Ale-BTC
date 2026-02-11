import os, time
import pandas as pd
from binance.client import Client

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
# Capital actualizado tras el último desastre en los logs
cap_actual = 24.17 
st = {m: {'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def calcular_cerebro(df):
    df['ema_rápida'] = df['close'].ewm(span=7, adjust=False).mean()
    df['cuerpo'] = df['close'] - df['open']
    return df

def analizar_fuerza_real(df):
    act = df.iloc[-1]; prev = df.iloc[-2]
    promedio_volatilidad = abs(df['cuerpo']).tail(30).mean()
    
    # Solo entra si la vela tiene "nafta" (fuerza)
    vela_con_fuerza = abs(act['cuerpo']) > (promedio_volatilidad * 1.3)
    
    # LONG: Verde + Fuerza + Rompe Techo anterior
    if act['close'] > act['open'] and act['close'] > prev['high'] and vela_con_fuerza:
        return "🟩"
    # SHORT: Roja + Fuerza + Rompe Suelo anterior
    if act['close'] < act['open'] and act['close'] < prev['low'] and vela_con_fuerza:
        return "🟥"
    return "."

print(f"🔱 IA QUANTUM ANTIPÉRDIDA | CAP: ${cap_actual} | SALIDA INSTANTÁNEA")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            senal = analizar_fuerza_real(df)

            if not s['e']:
                if senal != ".":
                    s['t'] = "LONG" if senal == "🟩" else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 {senal} DISPARO EN {m} | PX: {px}")
            else:
                # --- GESTIÓN DE RIESGO RADICAL ---
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                
                # CIERRE POR REBOTE O CAMBIO DE COLOR (Tu pedido)
                # Si estamos en LONG y la vela actual es ROJA, salimos.
                # Si estamos en SHORT y la vela actual es VERDE, salimos.
                es_roja = df['close'].iloc[-1] < df['open'].iloc[-1]
                es_verde = df['close'].iloc[-1] > df['open'].iloc[-1]
                
                cambio_fatal = (s['t'] == "LONG" and es_roja) or (s['t'] == "SHORT" and es_verde)
                
                # Blindaje de ganancia mínima
                if roi >= 0.05: s['b'] = True 
                
                # REGLA: Si hay cambio de color, o perdemos -0.15%, o baja 0.05 desde el máximo -> AFUERA
                if cambio_fatal or roi <= -0.15 or (s['b'] and roi <= 0.01) or (roi > 0.15 and roi < s['m'] - 0.05):
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['o'] += 1; s['e'] = False
                    est = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{est} {s['t']} {roi:.2f}%")
                    print(f"\n{est} OUT {m} {roi:.2f}% | CAP: ${cap_actual:.2f}")

                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*32}╗\n║ 📊 REPORTE PROTEGIDO - {m[:3]} ║")
                        for line in s['h']: print(f"║ {line.ljust(28)} ║")
                        print(f"╠{'═'*32}╣\n║ SALDO ACTUAL: ${cap_actual:.2f}    ║\n╚{'═'*32}╝\n")
                        s['h'] = []
        time.sleep(15)
    except:
        time.sleep(10); cl = c()
