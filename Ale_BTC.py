import os, time, redis, json
import pandas as pd
from binance.client import Client 

# --- 🧠 1. MEMORIA (Persistencia de tus $15.77) ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77 
    try:
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
    except: return cap_ini

# --- 📖 2. LIBRO DE VELAS (Price Action) ---
def leer_libro_velas(df):
    v = df.iloc[-2]
    v_ant = df.iloc[-3]
    cuerpo = abs(v['c'] - v['o'])
    m_sup = v['h'] - max(v['c'], v['o'])
    m_inf = min(v['c'], v['o']) - v['l']
    
    env_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
    env_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']
    martillo = m_inf > (cuerpo * 2) and m_sup < (cuerpo * 0.5)
    
    if (martillo or env_alc) and v['c'] > v['o']: return "ALCISTA"
    if env_baj and v['c'] < v['o']: return "BAJISTA"
    return "NEUTRAL"

# --- 📊 3. ANALISTA (Distancia EMA 9/27) ---
def analista_superior(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=50)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        
        # Separación entre EMAs (Filtro de tendencia fuerte)
        distancia = abs(ema9 - ema27) / ema27 * 100
        
        rsi = 100 - (100 / (1 + (df['c'].diff().where(df['c'].diff() > 0, 0).mean() / -df['c'].diff().where(df['c'].diff() < 0, 0).mean())))
        patron = leer_libro_velas(df)

        if patron == "ALCISTA" and rsi < 65 and ema9 > ema27 and distancia > 0.05:
            return True, "LONG", patron
        if patron == "BAJISTA" and rsi > 35 and ema9 < ema27 and distancia > 0.05:
            return True, "SHORT", patron
        return False, None, rsi
    except: return False, None, 50

# --- 🚀 4. MOTOR PRINCIPAL ---
def bot_run():
    cap_total = gestionar_memoria(leer=True)
    operaciones = []
    monedas = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'PEPEUSDT']
    
    print(f"🦁 V132 ONLINE | Capital: ${cap_total:.2f}")

    while True:
        t_loop = time.time()
        try:
            client = Client()
            ganancia_viva = 0

            # GESTIÓN DE POSICIONES
            for op in operaciones[:]:
                curr = float(client.get_symbol_ticker(symbol=op['s'])['price'])
                roi = ((curr - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - curr)/op['p'])*100*op['x']
                
                # BREAKEVEN: Si sube a 0.7%, protegemos
                if roi > 0.7: op['be'] = True
                if roi > 0.4: op['x'] = min(15, op['x'] + 1) # X Dinámicas

                pnl = op['c'] * (roi / 100)
                ganancia_viva += pnl

                # Salida por BE o por Objetivo
                if (op['be'] and roi <= 0.01) or roi >= 1.75 or roi <= -1.25:
                    motivo = "🛡️ BE" if (op['be'] and roi <= 0.01) else "🏁 TP/SL"
                    print(f"\n{motivo} en {op['s']} | ROI: {roi:.2f}%")
                    gestionar_memoria(False, {'roi': roi, 'm': op['s']})
                    operaciones.remove(op)
                    cap_total = gestionar_memoria(leer=True)

            # BÚSQUEDA DE ENTRADAS
            if len(operaciones) < 2:
                for m in monedas:
                    if any(o['s'] == m for o in operaciones): continue
                    puedo, lado, mot = analista_superior(m, client)
                    if puedo:
                        px = float(client.get_symbol_ticker(symbol=m)['price'])
                        print(f"\n🎯 [DISPARO]: {m} {lado} | {mot} | Emas OK")
                        operaciones.append({'s': m, 'l': lado, 'p': px, 'x': 8, 'c': cap_total * 0.45, 'be': False})
                        if len(operaciones) >= 2: break

            print(f"💰 TOTAL: ${cap_total + ganancia_viva:.2f} | Base: ${cap_total:.2f}          ", end='\r')

        except Exception as e:
            print(f"\n⚠️ Reintentando... {e}")
            time.sleep(5)
            continue
        
        # Sincronización Binance 15s
        time.sleep(max(1, 15 - (time.time() - t_loop)))

if __name__ == "__main__":
    bot_run()
