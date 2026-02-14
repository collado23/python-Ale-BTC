import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pandas as pd
from binance.client import Client

# --- 🌐 SERVIDOR DE SALUD MINIMALISTA ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    try:
        server = HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), HealthServer)
        server.serve_forever()
    except: pass

# --- 🧠 MEMORIA OPTIMIZADA ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini
    try:
        if leer:
            hist = r.lrange("historial_bot", 0, 5) # Solo leemos lo último para ahorrar memoria
            cap_act = cap_ini
            for t in reversed(hist):
                tr = json.loads(t)
                cap_act *= (1 + (tr.get('roi', 0) / 100))
            return float(cap_act)
        else:
            r.lpush("historial_bot", json.dumps(datos))
            r.ltrim("historial_bot", 0, 50) # Mantenemos la base de datos limpia
    except: return cap_ini

# --- 📊 ANALISTA RÁPIDO (EMA 9/27 + LIBRO) ---
def analista_lite(simbolo, cliente):
    try:
        # Pedimos menos velas para que el servidor no se cuelgue (50 en vez de 100)
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=50)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        c = df['c']
        ema9 = c.ewm(span=9, adjust=False).mean().iloc[-1]
        ema27 = c.ewm(span=27, adjust=False).mean().iloc[-1]
        dist = abs(ema9 - ema27) / ema27 * 100
        
        # Libro de Velas simplificado para velocidad
        v = df.iloc[-2]
        v_ant = df.iloc[-3]
        cuerpo = abs(v['c'] - v['o'])
        env_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
        env_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']

        # Disparo con distancia mínima de 0.03
        if env_alc and ema9 > ema27 and dist > 0.03: return True, "LONG"
        if env_baj and ema9 < ema27 and dist > 0.03: return True, "SHORT"
        return False, None
    except: return False, None

# --- 🚀 MOTOR V135 ---
def bot_run():
    threading.Thread(target=run_health_server, daemon=True).start()
    cap_total = gestionar_memoria(leer=True)
    operaciones = []
    monedas = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'PEPEUSDT']
    
    print(f"🦁 V135 LITE | CAPITAL: ${cap_total:.2f}")

    client = Client() # Creamos el cliente una sola vez fuera del bucle

    while True:
        t_loop = time.time()
        try:
            ganancia_viva = 0
            for op in operaciones[:]:
                curr = float(client.get_symbol_ticker(symbol=op['s'])['price'])
                roi = ((curr - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - curr)/op['p'])*100*op['x']
                
                if roi > 0.6: op['be'] = True
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
                    puedo, lado = analista_lite(m, client)
                    if puedo:
                        px = float(client.get_symbol_ticker(symbol=m)['price'])
                        print(f"\n🎯 [DISPARO]: {m} {lado}")
                        operaciones.append({'s': m, 'l': lado, 'p': px, 'x': 10, 'c': cap_total * 0.45, 'be': False})
                        break

            print(f"💰 TOTAL: ${cap_total + ganancia_viva:.2f} | Base: ${cap_total:.2f}          ", end='\r')

        except: 
            time.sleep(5)
            continue
        
        time.sleep(max(1, 15 - (time.time() - t_loop)))

if __name__ == "__main__":
    bot_run()
