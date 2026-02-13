import os, time, csv
import pandas as pd
import numpy as np
from binance.client import Client

# Conexión Segura
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
FILE_MEMORIA = "memoria_ia.csv"

# --- FUNCIONES DE APRENDIZAJE ---
def guardar_operacion(moneda, tipo, modo, roi, resultado):
    existe = os.path.exists(FILE_MEMORIA)
    with open(FILE_MEMORIA, 'a', newline='') as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(['fecha', 'moneda', 'tipo', 'modo', 'roi', 'resultado'])
        writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), moneda, tipo, modo, roi, resultado])

def obtener_aprendizaje():
    if not os.path.exists(FILE_MEMORIA): return 1.0 # Factor de riesgo normal
    try:
        df = pd.read_csv(FILE_MEMORIA)
        if len(df) < 2: return 1.0
        ultimas = df.tail(3)
        # Si hay rachas de pérdidas, devuelve un factor para ser más estricto (1.5 = 50% más estricto)
        if (ultimas['roi'] < 0).sum() >= 2: return 1.5 
        return 0.8 # Si viene ganando, se vuelve un poco más agresivo
    except: return 1.0

# --- CEREBRO DE TRADING ---
cap_actual = 16.54 
MIN_LOT = 16.5
st = {m: {'e': False, 'p': 0, 't': '', 'max_px': 0, 'modo': ''} for m in ms}

def analizar_todo(df):
    # Indicadores Maestro
    df['ema35'] = df['close'].ewm(span=35, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['dist'] = ((df['ema35'] - df['ema200']) / df['ema200']) * 100
    
    # RSI y Velas
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    act, ant = df.iloc[-1], df.iloc[-2]
    # Patrón Envolvente (Engulfing)
    e_l = act['close'] > ant['open'] and act['open'] < ant['close'] and act['close'] > act['open']
    e_s = act['close'] < ant['open'] and act['open'] > ant['close'] and act['close'] < act['open']
    # Patrón de Agotamiento (Mechas)
    p_a = (act['high'] - max(act['close'], act['open'])) > (abs(act['close'] - act['open']) * 2)
    
    return df, e_l, e_s, p_a

def detectar_entrada(df):
    df, e_l, e_s, p_a = analizar_todo(df)
    act = df.iloc[-1]
    factor = obtener_aprendizaje() # El bot "recuerda" si debe ser estricto
    
    vol_ok = act['v'] > df['v'].rolling(20).mean().iloc[-1] * (1.5 * factor)
    dist_val = abs(act['dist'])

    # 1. TENDENCIA (Zig-Zag normal o subida larga)
    if vol_ok and (0.05 < dist_val < (1.1 / factor)):
        if act['ema35'] > act['ema50'] and e_l and act['rsi'] > 50:
            return "LONG", "TENDENCIA"
        if act['ema35'] < act['ema50'] and e_s and act['rsi'] < 50:
            return "SHORT", "TENDENCIA"

    # 2. VOLTEO (Pico alto y reversión fuerte)
    if dist_val > 1.2 or act['rsi'] > 75 or act['rsi'] < 25:
        if act['rsi'] > 75 and (p_a or e_s): return "SHORT", "VOLTEO"
        if act['rsi'] < 25 and (p_a or e_l): return "LONG", "VOLTEO"
            
    return None, ""

print(f"🔱 IA QUANTUM V36 | MEMORIA & APRENDIZAJE | CAP: ${cap_actual}")

while True:
    try:
        ops_abiertas = sum(1 for m in ms if st[m]['e'])
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            if s['e']:
                roi = ((px - s['p']) / s['p'] * 1000) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 1000)
                roi -= 0.22 
                
                s['max_px'] = max(s['max_px'], px) if s['t'] == "LONG" else (min(s['max_px'], px) if s['max_px'] > 0 else px)
                retroceso = abs(s['max_px'] - px) / s['p'] * 1000
                
                # Resorte adaptativo según ROI y Modo
                freno = 0.15 if (roi > 1.2 or s['modo'] == "VOLTEO") else 0.35
                
                if (roi > 0.35 and retroceso > freno) or roi <= -1.1:
                    gan_usd = (MIN_LOT * (roi / 100))
                    cap_actual += gan_usd
                    # GUARDAR EN MEMORIA PARA LA PRÓXIMA VEZ
                    resultado = "WIN" if roi > 0 else "LOSS"
                    guardar_operacion(m, s['t'], s['modo'], round(roi, 2), resultado)
                    
                    print(f"\n✅ CIERRE {s['modo']} {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                
                print(f"📊 {m} ({s['t']}): {roi:.2f}%", end=' | ')
            
            else:
                if ops_abiertas < 2:
                    k = cl.get_klines(symbol=m, interval='1m', limit=150)
                    df_raw = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i']).astype(float)
                    res, modo = detectar_entrada(df_raw)
                    if res:
                        s['t'], s['p'], s['e'], s['max_px'], s['modo'] = res, px, True, px, modo
                        ops_abiertas += 1
                        print(f"\n🚀 DISPARO {modo} {res} en {m} (Aprendizaje Aplicado)")

        time.sleep(1)
    except Exception as e:
        time.sleep(2); cl = c()
