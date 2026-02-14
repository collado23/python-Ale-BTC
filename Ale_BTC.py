import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pandas as pd
from binance.client import Client

# --- 🌐 SERVIDOR DE SALUD (Evita reinicios del hosting) ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"BOT V134 ACTIVE")

def run_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthServer)
    server.serve_forever()

# --- 🧠 MEMORIA (Tus $15.77) ---
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

# --- 📖 LIBRO DE VELAS ---
def leer_libro_velas(df):
    v = df.iloc[-2]
    v_ant = df.iloc[-3]
    cuerpo = abs(v['c'] - v['o'])
    m_sup = v['h'] - max(v['c'], v['o'])
    m_inf = min(v['c'], v['o']) - v['l']
    
    env_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
    env_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']
    martillo = m_inf > (cuerpo * 1.5) and m_sup < (cuerpo * 0.5)
    
    if (martillo or env_alc) and v['c'] > v['o']: return "ALCISTA"
    if env_baj and v['c'] < v['o']: return "BAJISTA"
    return "NEUTRAL"

# --- 📊 ANALISTA (EMA 9/27 con más sensibilidad) ---
def analista_superior(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=50)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        
        # Reducimos la distancia mínima a 0.02% para que no se quede mudo
        distancia = abs(ema9 - ema27) / ema27 * 100
        rsi = 100 - (100 / (1 + (df['c'].diff().where(df['c'].diff() > 0, 0).mean() / -df['c'].diff().where(df['c'].diff() < 0, 0).mean())))
        patron = leer_libro_velas(df)

        # GATILLO: El patrón de velas manda, la EMA confirma dirección
        if patron == "ALCISTA" and rsi < 65 and ema9 > ema27 and distancia > 0.02:
            return True, "LONG"
        if patron == "BAJISTA" and rsi > 35 and ema9 < ema27 and distancia > 0.02:
            return True, "SHORT"
        return False, None
    except: return False, None

# --- 🚀 MOTOR DE TRADING ---
def bot_run():
    threading.Thread(target=run_health_server, daemon=True).start()
    cap_total = gestionar_memoria(leer=True)
    operaciones = []
    monedas = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'PEPEUSDT', 'DOGEUSDT']
    
    print(f"🦁 V134 ONLINE | CAPITAL: ${cap_total:.2f}")

    while True:
        t_loop = time.time()
        try:
            client = Client()
            ganancia_viva = 0

            for op in operaciones[:]:
                curr = float(client.get_symbol_ticker(symbol=op['s'])['price'])
                roi = ((curr - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - curr)/op['p'])*100*op['x']
                
                if roi > 0.6: op['be'] = True # Breakeven más temprano
                pnl = op['c'] * (roi / 100)
                ganancia_viva += pnl

                if (op['be'] and roi <= 0.01) or roi >= 1.5 or roi <= -1.1:
                    print(f"\n✅ CIERRE {op['s']} | ROI: {roi:.2f}%")
                    gestionar_memoria(False, {'roi': roi, 'm': op['s']})
                    operaciones.remove(op)
                    cap_total = gestionar_memoria(leer=True)

            if len(operaciones) < 2:
                for m in monedas:
                    if any(o['s'] == m for o in operaciones): continue
                    puedo, lado = analista_superior(m, client)
                    if puedo:
                        px = float(client.get_symbol_ticker(symbol=m)['price'])
                        print(f"\n🎯 [DISPARO]: {m} {lado}")
                        operaciones.append({'s': m, 'l': lado, 'p': px, 'x': 10, 'c': cap_total * 0.45, 'be': False})
                        if len(operaciones) >= 2: break

            print(f"💰 TOTAL: ${cap_total + ganancia_viva:.2f} | Base: ${cap_total:.2f}          ", end='\r')

        except Exception:
            time.sleep(5)
            continue
        
        time.sleep(max(1, 15 - (time.time() - t_loop)))

if __name__ == "__main__":
    bot_run()
