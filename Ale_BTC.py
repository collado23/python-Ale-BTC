import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA DE CAPITAL (Redis - Guardián de tus $15.95) ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77 
    if not r: return cap_ini
    if leer:
        hist = r.lrange("historial_bot", 0, -1)
        if not hist: return cap_ini
        cap_act = cap_ini
        for t in reversed(hist):
            tr = json.loads(t)
            cap_act *= (1 + (tr.get('roi', 0) / 100))
        return float(cap_act)
    else:
        r.lpush("historial_bot", json.dumps(datos))

# --- 📖 2. LIBRERÍA DE VELAS COMPLETA (Price Action) ---
def leer_libro_velas(df):
    v = df.iloc[-2]      # Vela cerrada
    v_ant = df.iloc[-3]  # Vela anterior
    cuerpo = abs(v['c'] - v['o'])
    m_sup = v['h'] - max(v['c'], v['o'])
    m_inf = min(v['c'], v['o']) - v['l']
    
    # Patrones de Reversión y Continuación
    martillo = m_inf > (cuerpo * 1.8) and m_sup < (cuerpo * 0.6)
    martillo_inv = m_sup > (cuerpo * 1.8) and m_inf < (cuerpo * 0.6)
    envolvente_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
    envolvente_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']
    
    if (martillo or envolvente_alc) and v['c'] > v['o']: return "ALCISTA"
    if (martillo_inv or envolvente_baj) and v['c'] < v['o']: return "BAJISTA"
    return "NEUTRAL"

# --- 📊 3. ANALISTA SUPERIOR (EMAs + RSI + VELAS) ---
def analista_superior(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=35)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        # Filtros de apoyo
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema21 = df['c'].ewm(span=21).mean().iloc[-1]
        delta = df['c'].diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).mean() / -delta.where(delta < 0, 0).mean())))
        
        patron = leer_libro_velas(df)

        # Disparo: La Vela manda, el RSI y EMA confirman
        if patron == "ALCISTA" and rsi < 65 and ema9 >= (ema21 * 0.999):
            return True, "LONG", patron
        if patron == "BAJISTA" and rsi > 35 and ema9 <= (ema21 * 1.001):
            return True, "SHORT", patron
            
        return False, None, rsi
    except: return False, None, 50

# --- 🚀 4. MOTOR DE TRADING (15 Segundos) ---
cap_total = gestionar_memoria(leer=True)
operaciones = []
presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ETHUSDT']

while True:
    t_inicio = time.time()
    try:
        client = Client()
        ganancia_flotante = 0

        # A. CONTROL DE POSICIONES
        for op in operaciones[:]:
            t = client.get_symbol_ticker(symbol=op['s'])
            p_act = float(t['price'])
            roi = ((p_act - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - p_act)/op['p'])*100*op['x']
            
            # X Dinámicas: Subir potencia si ganamos
            if roi > 0.4: op['x'] = min(15, op['x'] + 1)
            
            pnl = op['c'] * (roi / 100)
            ganancia_flotante += pnl
            
            if roi >= 1.6 or roi <= -1.2:
                print(f"\n✅ CIERRE EN {op['s']} | PnL: ${pnl:.2f} | ROI: {roi:.2f}%")
                gestionar_memoria(False, {'roi': roi, 'm': op['s']})
                operaciones.remove(op)
                cap_total = gestionar_memoria(leer=True)

        # B. BÚSQUEDA DE ENTRADAS
        if len(operaciones) < 2:
            for p in presas:
                if any(o['s'] == p for o in operaciones): continue
                puedo, lado, motivo = analista_superior(p, client)
                if puedo:
                    t = client.get_symbol_ticker(symbol=p)
                    print(f"\n🎯 [DISPARO VELAS]: {p} {lado} | {motivo}")
                    operaciones.append({'s': p, 'l': lado, 'p': float(t['price']), 'x': 7, 'c': cap_total * 0.45})
                    if len(operaciones) >= 2: break

        print(f"💰 BILLETERA: ${cap_total + ganancia_flotante:.2f} | Base: ${cap_total:.2f}          ", end='\r')

    except Exception: pass
    time.sleep(max(1, 15 - (time.time() - t_inicio)))
