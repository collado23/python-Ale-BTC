import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA Y CAPITAL (Arreglado) --- 
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini, 0
    hist = r.lrange("historial_bot", 0, -1)
    if leer:
        if not hist: return cap_ini, 0
        cap_act = cap_ini
        racha = 0
        for t in reversed(hist):
            tr = json.loads(t)
            cap_act *= (1 + (tr.get('roi', 0) / 100))
            racha = racha + 1 if tr.get('res') == "LOSS" else 0
        return float(cap_act), int(racha)
    else: r.lpush("historial_bot", json.dumps(datos))

# --- 📊 2. CEREBRO DE X DINÁMICAS (Para que suban y bajen) ---
def calcular_x_viva(simbolo, lado, cliente):
    try:
        klines = cliente.get_klines(symbol=simbolo, interval='1m', limit=10)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
        precios = pd.to_numeric(df['c'])
        
        # Calculamos RSI rápido para ver la fuerza actual
        delta = precios.diff()
        gan = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        per = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rsi = 100 - (100 / (1 + (gan / per))).iloc[-1]
        
        # Si el RSI acompaña nuestra dirección, subimos potencia
        fuerza = (rsi - 50) if lado == "LONG" else (50 - rsi)
        nueva_x = int(5 + (fuerza * 0.3))
        return max(2, min(15, nueva_x))
    except: return 5

# --- 🚀 3. BUCLE MAESTRO ---
cap_total, racha_act = gestionar_memoria(leer=True)
operaciones = [] 

print(f"🦁 BOT V109 | X DINÁMICAS OK | Billetera: ${cap_total:.2f}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    ganancia_flotante = 0
    client = Client()

    # A. MONITOR Y AJUSTE DE POTENCIA (X)
    for op in operaciones[:]:
        try:
            ticker = client.get_symbol_ticker(symbol=op['s'])
            p_act = float(ticker['price'])
            
            # 🔥 Aquí es donde cambian las X según el mercado
            op['x'] = calcular_x_viva(op['s'], op['l'], client)

            roi = ((p_act - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - p_act)/op['p'])*100*op['x']
            pnl = op['c'] * (roi / 100)
            ganancia_flotante += pnl
            
            status = "🟢 G" if roi >= 0 else "🔴 P"
            print(f"📊 {op['s']} {op['l']} ({op['x']}x) | {status}: ${abs(pnl):.2f} ({roi:.2f}%)      ", end='\r')

            if roi >= 1.6 or roi <= -1.3:
                print(f"\n✅ CIERRE {op['s']} | Resultado: ${pnl:.2f}")
                gestionar_memoria(False, {'m': op['s'], 'roi': roi, 'res': 'WIN' if roi > 0 else 'LOSS'})
                operaciones.remove(op)
                cap_total, racha_act = gestionar_memoria(leer=True)
        except: continue

    # Billetera siempre actualizada
    print(f"💰 BILLETERA TOTAL: ${cap_total + ganancia_flotante:.2f} | Base: ${cap_total:.2f}          ")

    # B. ANALIZAR ENTRADAS
    if len(operaciones) < 2:
        for p in presas:
            if any(o['s'] == p for o in operaciones): continue
            # Aquí iría la lógica de analizar_entrada (ya la tenés)
            pass

    time.sleep(15)
