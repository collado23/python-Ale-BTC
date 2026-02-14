import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
import pandas as pd
from binance.client import Client

# --- 🌐 0. SERVIDOR DE SALUD (Para evitar el bucle del hosting) ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"BOT V133 ACTIVE")

def run_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthServer)
    server.serve_forever()

# --- 🧠 1. MEMORIA ---
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

# --- 📊 2. ANALISTA EMA 9/27 ---
def analista_superior(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=50)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        distancia = abs(ema9 - ema27) / ema27 * 100
        
        rsi = 100 - (100 / (1 + (df['c'].diff().where(df['c'].diff() > 0, 0).mean() / -df['c'].diff().where(df['c'].diff() < 0, 0).mean())))
        
        if rsi < 60 and ema9 > ema27 and distancia > 0.05: return True, "LONG"
        if rsi > 40 and ema9 < ema27 and distancia > 0.05: return True, "SHORT"
        return False, None
    except: return False, None

# --- 🚀 3. MOTOR ---
def bot_run():
    # Lanzar servidor de salud en segundo plano
    threading.Thread(target=run_health_server, daemon=True).start()
    
    cap_total = gestionar_memoria(leer=True)
    operaciones = []
    monedas = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
    
    print(f"🦁 V133 | CAPITAL: ${cap_total:.2f} | HEALTH CHECK OK")

    while True:
        t_loop = time.time()
        try:
            client = Client()
            ganancia_viva = 0

            for op in operaciones[:]:
                curr = float(client.get_symbol_ticker(symbol=op['s'])['price'])
                roi = ((curr - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - curr)/op['p'])*100*op['x']
                
                if roi > 0.7: op['be'] = True
                pnl = op['c'] * (roi / 100)
                ganancia_viva += pnl

                if (op['be'] and roi <= 0.02) or roi >= 1.6 or roi <= -1.1:
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
                        print(f"\n🎯 [ENTRADA]: {m} {lado}")
                        operaciones.append({'s': m, 'l': lado, 'p': px, 'x': 10, 'c': cap_total * 0.45, 'be': False})
                        if len(operaciones) >= 2: break

            print(f"💰 TOTAL: ${cap_total + ganancia_viva:.2f} | Base: ${cap_total:.2f}          ", end='\r')

        except Exception as e:
            time.sleep(10)
            continue
        
        time.sleep(max(1, 15 - (time.time() - t_loop)))

if __name__ == "__main__":
    bot_run()
