import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA Y PERSISTENCIA (Redis) --- 
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

# --- 📖 2. EL LIBRO COMPLETO DE VELAS ---
def leer_libro_velas(df):
    v = df.iloc[-2]
    v_ant = df.iloc[-3]
    cuerpo = abs(v['c'] - v['o'])
    m_sup = v['h'] - max(v['c'], v['o'])
    m_inf = min(v['c'], v['o']) - v['l']
    
    # Alcistas
    martillo = m_inf > (cuerpo * 2.5) and m_sup < (cuerpo * 0.5)
    martillo_inv = m_sup > (cuerpo * 2.5) and m_inf < (cuerpo * 0.5)
    envolvente_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
    
    # Bajistas
    estrella_fugaz = m_sup > (cuerpo * 2.5) and m_inf < (cuerpo * 0.5)
    colgado = m_inf > (cuerpo * 2.5) and m_sup < (cuerpo * 0.5)
    envolvente_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']

    if martillo or (martillo_inv and v['c'] > v['o']) or envolvente_alc: return "ALCISTA"
    if estrella_fugaz or colgado or envolvente_baj: return "BAJISTA"
    return "NEUTRAL"

# --- 📊 3. ANALISTA SUPERIOR ---
def analista_total(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=35)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema21 = df['c'].ewm(span=21).mean().iloc[-1]
        delta = df['c'].diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).mean() / -delta.where(delta < 0, 0).mean())))
        vol_act = df['v'].iloc[-1]
        vol_avg = df['v'].rolling(10).mean().iloc[-1]
        patron = leer_libro_velas(df)

        if patron == "ALCISTA" and rsi < 45 and ema9 > ema21 and vol_act > vol_avg:
            return True, "LONG", patron
        if patron == "BAJISTA" and rsi > 55 and ema9 < ema21 and vol_act > vol_avg:
            return True, "SHORT", patron
        return False, None, rsi
    except: return False, None, 50

# --- 🚀 4. BUCLE MAESTRO (EL MOTOR) ---
cap_total = gestionar_memoria(leer=True)
operaciones = []
presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

print(f"🦁 BOT V126 ACTIVO | Capital: ${cap_total:.2f}")

while True: # <--- ACÁ ESTÁ EL SECRETO, NO SE DETIENE
    t_inicio = time.time()
    try:
        client = Client()
        ganancia_flotante = 0

        # A. MONITOREO
        for op in operaciones[:]:
            t = client.get_symbol_ticker(symbol=op['s'])
            p_act = float(t['price'])
            roi = ((p_act - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - p_act)/op['p'])*100*op['x']
            if roi > 0.5: op['x'] = min(15, op['x'] + 1)
            pnl = op['c'] * (roi / 100)
            ganancia_flotante += pnl
            
            print(f"📊 {op['s']} {op['l']} ({op['x']}x) | ROI: {roi:.2f}% | PnL: ${pnl:.2f}      ", end='\r')

            if roi >= 1.6 or roi <= -1.2:
                print(f"\n✅ CIERRE EN {op['s']} | PnL: ${pnl:.2f} | ROI: {roi:.2f}%")
                gestionar_memoria(False, {'roi': roi, 'm': op['s']})
                operaciones.remove(op)
                cap_total = gestionar_memoria(leer=True)

        # B. ENTRADAS
        if len(operaciones) < 2:
            for p in presas:
                if any(o['s'] == p for o in operaciones): continue
                puedo, lado, motivo = analista_total(p, client)
                if puedo:
                    t = client.get_symbol_ticker(symbol=p)
                    print(f"\n🎯 [ENTRADA LIBRO]: {p} {lado} | {motivo}")
                    operaciones.append({'s': p, 'l': lado, 'p': float(t['price']), 'x': 5, 'c': cap_total * 0.4})
                    if len(operaciones) >= 2: break

        print(f"💰 BILLETERA: ${cap_total + ganancia_flotante:.2f} | Base: ${cap_total:.2f}          ", end='\r')

    except Exception as e:
        print(f"\n⚠️ Reintentando conexión...")
    
    # ⏱️ Sincronización 15s
    time.sleep(max(1, 15 - (time.time() - t_inicio)))
