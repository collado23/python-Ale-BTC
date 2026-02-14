import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA Y CAPITAL ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini, 0
    hist = r.lrange("historial_bot", 0, -1)
    if leer:
        if not hist: return cap_ini, 0
        cap_act = cap_ini
        for t in reversed(hist):
            tr = json.loads(t)
            cap_act *= (1 + (tr.get('roi', 0) / 100))
        return cap_act
    else: r.lpush("historial_bot", json.dumps(datos))

# --- 📊 2. ANALISTA DE X DINÁMICAS ---
def calcular_fuerza_x(rsi, racha=0):
    # El bot analiza qué tan "segura" es la jugada para subir o bajar las X
    distancia_extremo = abs(50 - rsi)
    nueva_x = int(min(15, 5 + (distancia_extremo * 0.5)))
    if racha > 0: nueva_x = max(1, nueva_x - (racha * 2))
    return nueva_x

# --- 🚀 3. BUCLE MAESTRO (X QUE SUBEN Y BAJAN) ---
cap_total = gestionar_memoria(leer=True)
operaciones = [] 
print(f"🦁 BOT V108 | X DINÁMICAS EN VIVO | Cap: ${cap_total:.2f}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT', 'ETHUSDT']

while True:
    ganancia_flotante = 0
    client = Client()

    # A. MONITOREAR Y AJUSTAR X EN VIVO
    for op in operaciones[:]:
        try:
            ticker = client.get_symbol_ticker(symbol=op['s'])
            p_act = float(ticker['price'])
            
            # --- NUEVO: El bot vuelve a mirar el RSI para ajustar las X ---
            klines = client.get_klines(symbol=op['s'], interval='1m', limit=20)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
            df['close'] = pd.to_numeric(df['c'])
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi_actual = 100 - (100 / (1 + (gain / loss))).iloc[-1]
            
            # Ajustamos la X según lo que está pasando ahora
            op['x'] = calcular_fuerza_x(rsi_actual)

            # Cálculo ROI con la X actualizada
            roi = ((p_act - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - p_act)/op['p'])*100*op['x']
            gan_usd = op['c'] * (roi / 100)
            ganancia_flotante += gan_usd
            
            status = "🟢 G" if roi >= 0 else "🔴 P"
            print(f"📊 {op['s']} {op['l']} ({op['x']}x) | {status}: ${abs(gan_usd):.2f} ({roi:.2f}%)      ", end='\r')

            if roi >= 1.8 or roi <= -1.4:
                print(f"\n✅ CIERRE {op['s']} | Resultado final: ${gan_usd:.2f}")
                gestionar_memoria(False, {'m': op['s'], 'roi': roi})
                operaciones.remove(op)
                cap_total = gestionar_memoria(leer=True)
        except: continue

    print(f"💰 BILLETERA TOTAL: ${cap_total + ganancia_flotante:.2f} | Base: ${cap_total:.2f}          ")

    # B. ANALIZAR ENTRADAS (Si hay espacio para 2)
    if len(operaciones) < 2:
        for p in presas:
            if any(o['s'] == p for o in operaciones): continue
            # (Aquí va la lógica de análisis de entrada similar a la anterior...)
            # Si da señal, se agrega a la lista 'operaciones'
            pass

    time.sleep(15)
