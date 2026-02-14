import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA (Redis) ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77 
    if not r: return cap_ini
    try:
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

# --- 📖 2. LIBRO DE VELAS ---
def leer_libro_velas(df):
    v = df.iloc[-2]
    v_ant = df.iloc[-3]
    cuerpo = abs(v['c'] - v['o'])
    m_sup = v['h'] - max(v['c'], v['o'])
    m_inf = min(v['c'], v['o']) - v['l']
    
    envolvente_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
    envolvente_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']
    martillo = m_inf > (cuerpo * 1.8) and m_sup < (cuerpo * 0.6)
    
    if (martillo or envolvente_alc) and v['c'] > v['o']: return "ALCISTA"
    if envolvente_baj and v['c'] < v['o']: return "BAJISTA"
    return "NEUTRAL"

# --- 📊 3. ANALISTA (EMA 9/27 + DISTANCIA) ---
def analista_superior(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=40)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        distancia = abs(ema9 - ema27) / ema27 * 100
        
        delta = df['c'].diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).mean() / -delta.where(delta < 0, 0).mean())))
        patron = leer_libro_velas(df)

        # Filtro: Patrón + RSI + Distancia > 0.04%
        if patron == "ALCISTA" and rsi < 65 and ema9 > ema27 and distancia > 0.04:
            return True, "LONG", patron
        if patron == "BAJISTA" and rsi > 35 and ema9 < ema27 and distancia > 0.04:
            return True, "SHORT", patron
        return False, None, rsi
    except: return False, None, 50

# --- 🚀 4. MOTOR PRINCIPAL (Bucle de Hierro) ---
def ejecutar_bot():
    cap_total = gestionar_memoria(leer=True)
    operaciones = []
    presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'ETHUSDT', 'PEPEUSDT']
    
    print(f"🦁 BOT V131 ACTIVO | Capital: ${cap_total:.2f}")

    while True:
        t_ciclo = time.time()
        try:
            client = Client()
            ganancia_flotante = 0

            # --- A. GESTIÓN DE POSICIONES ---
            for op in operaciones[:]:
                t = client.get_symbol_ticker(symbol=op['s'])
                p_act = float(t['price'])
                roi = ((p_act - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - p_act)/op['p'])*100*op['x']
                
                if roi > 0.8: 
                    op['be'] = True
                    op['x'] = min(15, op['x'] + 1)

                pnl = op['c'] * (roi / 100)
                ganancia_flotante += pnl

                if op.get('be') and roi <= 0.02:
                    print(f"\n🛡️ BREAKEVEN en {op['s']}")
                    operaciones.remove(op)
                    continue

                if roi >= 1.7 or roi <= -1.2:
                    print(f"\n✅ CIERRE {op['s']} | ROI: {roi:.2f}%")
                    gestionar_memoria(False, {'roi': roi, 'm': op['s']})
                    operaciones.remove(op)
                    cap_total = gestionar_memoria(leer=True)

            # --- B. ENTRADAS ---
            if len(operaciones) < 2:
                for p in presas:
                    if any(o['s'] == p for o in operaciones): continue
                    puedo, lado, motivo = analista_superior(p, client)
                    if puedo:
                        t = client.get_symbol_ticker(symbol=p)
                        print(f"\n🎯 [DISPARO]: {p} {lado} | {motivo} | Distancia ✅")
                        operaciones.append({'s': p, 'l': lado, 'p': float(t['price']), 'x': 8, 'c': cap_total * 0.45, 'be': False})
                        if len(operaciones) >= 2: break

            print(f"💰 BILLETERA: ${cap_total + ganancia_flotante:.2f} | Base: ${cap_total:.2f}          ", end='\r')

        except Exception as e:
            print(f"\n⚠️ Error de conexión: {e}. Reintentando en 5s...")
            time.sleep(5)
            continue
        
        # Sincronización 15s
        espera = max(1, 15 - (time.time() - t_ciclo))
        time.sleep(espera)

# Arrancamos el motor
if __name__ == "__main__":
    ejecutar_bot()
