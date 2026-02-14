import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
import pandas as pd
from binance.client import Client

# --- 🌐 1. HEALTH CHECK MINIMALISTA (Para que el hosting no moleste) ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_health():
    try:
        httpd = HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), HealthServer)
        httpd.serve_forever()
    except: pass

# --- 🧠 2. MEMORIA (Tus $15.77) ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini
    try:
        if leer:
            hist = r.lrange("historial_bot", 0, 0) # Solo leemos el último
            if not hist: return cap_ini
            return float(json.loads(hist[0]).get('nuevo_cap', cap_ini))
        else:
            r.lpush("historial_bot", json.dumps(datos))
            r.ltrim("historial_bot", 0, 10)
    except: return cap_ini

# --- 📊 3. ANALISTA (EMA 9/27 + Velas) ---
def analista(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=35) # Bajamos a 35 velas
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        c = df['c']
        ema9 = c.ewm(span=9, adjust=False).mean().iloc[-1]
        ema27 = c.ewm(span=27, adjust=False).mean().iloc[-1]
        v, v_ant = df.iloc[-2], df.iloc[-3]
        
        env_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
        env_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']

        if env_alc and v['c'] > ema9 and ema9 > (ema27 * 0.999): return True, "LONG"
        if env_baj and v['c'] < ema9 and ema9 < (ema27 * 1.001): return True, "SHORT"
        return False, None
    except: return False, None

# --- 🚀 4. MOTOR LIGERO (1x -> 8x -> 15x) ---
def bot_run():
    threading.Thread(target=start_health, daemon=True).start()
    client = Client()
    cap_total = gestionar_memoria(leer=True)
    operaciones = []
    monedas = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'PEPEUSDT']
    
    print(f"🐊 V141 | Capital: ${cap_total:.2f}")

    while True:
        t_loop = time.time()
        try:
            for op in operaciones[:]:
                px = float(client.get_symbol_ticker(symbol=op['s'])['price'])
                diff = (px - op['p'])/op['p'] if op['l']=="LONG" else (op['p'] - px)/op['p']
                roi = diff * 100 * op['x']
                
                # Escalada de X (1 -> 8 -> 15)
                if roi > 0.3 and op['x'] == 1: op['x'] = 8
                if roi > 0.6 and op['x'] == 8: 
                    op['x'] = 15
                    op['be'] = True

                # Cierre
                if (op['be'] and roi <= 0.02) or roi >= 1.6 or roi <= -1.1:
                    print(f"\n✅ CIERRE {op['s']} | ROI: {roi:.2f}%")
                    nuevo_cap = cap_total * (1 + (roi/100))
                    gestionar_memoria(False, {'roi': roi, 'nuevo_cap': nuevo_cap})
                    operaciones.remove(op)
                    cap_total = nuevo_cap

            if len(operaciones) < 2:
                for m in monedas:
                    if any(o['s'] == m for o in operaciones): continue
                    puedo, lado = analista(m, client)
                    if puedo:
                        px = float(client.get_symbol_ticker(symbol=m)['price'])
                        print(f"\n🎯 ENTRADA {lado}: {m} (1x)")
                        operaciones.append({'s':m, 'l':lado, 'p':px, 'x':1, 'c':cap_total*0.45, 'be':False})
                        break

            print(f"💰 ${cap_total:.2f} | Activas: {len(operaciones)}          ", end='\r')

        except: pass
        time.sleep(max(1, 15 - (time.time() - t_loop)))

if __name__ == "__main__":
    bot_run()
