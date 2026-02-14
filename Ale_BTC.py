import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
import pandas as pd
from binance.client import Client

# --- 🌐 1. SERVIDOR DE SALUD PRIORITARIO ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"V136_ALIVE")

def start_health_check():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthServer)
    server.serve_forever()

# --- 🧠 2. MEMORIA REDIS ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini
    try:
        if leer:
            hist = r.lrange("historial_bot", 0, 5)
            cap_act = cap_ini
            for t in reversed(hist):
                tr = json.loads(t)
                cap_act *= (1 + (tr.get('roi', 0) / 100))
            return float(cap_act)
        else:
            r.lpush("historial_bot", json.dumps(datos))
            r.ltrim("historial_bot", 0, 20)
    except: return cap_ini

# --- 📊 3. ANALISTA (Librería Completa + Distancia) ---
def analista(simbolo, cliente):
    try:
        # Menos datos para evitar colapso de RAM
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=40)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        c = df['c']
        ema9 = c.ewm(span=9, adjust=False).mean().iloc[-1]
        ema27 = c.ewm(span=27, adjust=False).mean().iloc[-1]
        dist = (abs(ema9 - ema27) / ema27) * 100
        
        v = df.iloc[-2]
        v_ant = df.iloc[-3]
        env_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
        env_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']

        if env_alc and ema9 > ema27 and dist > 0.02: return True, "LONG"
        if env_baj and ema9 < ema27 and dist > 0.02: return True, "SHORT"
        return False, None
    except: return False, None

# --- 🚀 4. MOTOR PRINCIPAL ---
def bot_run():
    # EL SECRETO: El Health Check arranca primero
    threading.Thread(target=start_health_check, daemon=True).start()
    print("✅ Health Check iniciado. Esperando hosting...")
    time.sleep(2) # Pausa mínima para estabilizar el puerto
    
    cap_total = gestionar_memoria(leer=True)
    operaciones = []
    presas = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'PEPEUSDT']
    
    print(f"🦁 V136 ACTIVADA | Capital: ${cap_total:.2f}")
    client = Client()

    while True:
        t_ini = time.time()
        try:
            # Monitoreo
            ganancia_viva = 0
            for op in operaciones[:]:
                p_act = float(client.get_symbol_ticker(symbol=op['s'])['price'])
                roi = ((p_act - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - p_act)/op['p'])*100*op['x']
                
                if roi > 0.6: op['be'] = True
                pnl = op['c'] * (roi / 100)
                ganancia_viva += pnl

                if (op['be'] and roi <= 0.02) or roi >= 1.6 or roi <= -1.2:
                    print(f"\n✅ CIERRE {op['s']} | ROI: {roi:.2f}%")
                    gestionar_memoria(False, {'roi': roi, 'm': op['s']})
                    operaciones.remove(op)
                    cap_total = gestionar_memoria(leer=True)

            # Entradas
            if len(operaciones) < 2:
                for p in presas:
                    if any(o['s'] == p for o in operaciones): continue
                    puedo, lado = analista(p, client)
                    if puedo:
                        px = float(client.get_symbol_ticker(symbol=p)['price'])
                        print(f"\n🎯 [DISPARO]: {p} {lado} | Distancia EMA ✅")
                        operaciones.append({'s': p, 'l': lado, 'p': px, 'x': 10, 'c': cap_total * 0.45, 'be': False})
                        break

            print(f"💰 TOTAL: ${cap_total + ganancia_viva:.2f} | Base: ${cap_total:.2f}          ", end='\r')

        except: pass
        time.sleep(max(1, 15 - (time.time() - t_ini)))

if __name__ == "__main__":
    bot_run()
