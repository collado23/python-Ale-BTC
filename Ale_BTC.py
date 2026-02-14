import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
import pandas as pd
from binance.client import Client

# --- 🌐 SERVIDOR DE SALUD (Antireinicio) ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"V138_OK")

def start_health_check():
    try:
        server = HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), HealthServer)
        server.serve_forever()
    except: pass

# --- 🧠 MEMORIA INTELIGENTE ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini
    try:
        if leer:
            hist = r.lrange("historial_bot", 0, 3)
            cap_act = cap_ini
            for t in reversed(hist):
                cap_act *= (1 + (json.loads(t).get('roi', 0) / 100))
            return float(cap_act)
        else:
            r.lpush("historial_bot", json.dumps(datos))
            r.ltrim("historial_bot", 0, 10)
    except: return cap_ini

# --- 📊 ANALISTA V138 (Ruptura de EMA + Velas) ---
def analista_precision(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=40)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        c = df['c']
        ema9 = c.ewm(span=9, adjust=False).mean().iloc[-1]
        ema27 = c.ewm(span=27, adjust=False).mean().iloc[-1]
        
        v = df.iloc[-2]      # Vela actual cerrada
        v_ant = df.iloc[-3]  # Vela anterior
        
        # PATRONES DE VELAS
        env_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
        env_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']
        
        # 🎯 LÓGICA DE ENTRADA QUIRÚRGICA:
        # Para LONG: Vela Envolvente Y que el cierre esté POR ENCIMA de la EMA 9.
        if env_alc and v['c'] > ema9 and ema9 > (ema27 * 0.999):
            return True, "LONG"
            
        # Para SHORT: Vela Envolvente Y que el cierre esté POR DEBAJO de la EMA 9.
        if env_baj and v['c'] < ema9 and ema9 < (ema27 * 1.001):
            return True, "SHORT"
            
        return False, None
    except: return False, None

# --- 🚀 MOTOR ---
def bot_run():
    threading.Thread(target=start_health_check, daemon=True).start()
    client = Client()
    cap_total = gestionar_memoria(leer=True)
    operaciones = []
    presas = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'PEPEUSDT']
    
    print(f"🦁 V138 PRECISION | Capital: ${cap_total:.2f}")

    while True:
        t_loop = time.time()
        try:
            ganancia_viva = 0
            for op in operaciones[:]:
                p_act = float(client.get_symbol_ticker(symbol=op['s'])['price'])
                roi = ((p_act - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - p_act)/op['p'])*100*op['x']
                
                # Breakeven ultra rápido para no perder los $15.77
                if roi > 0.5: op['be'] = True
                
                pnl = op['c'] * (roi / 100)
                ganancia_viva += pnl

                if (op['be'] and roi <= 0.01) or roi >= 1.4 or roi <= -1.0:
                    print(f"\n✅ CIERRE {op['s']} | ROI: {roi:.2f}%")
                    gestionar_memoria(False, {'roi': roi, 'm': op['s']})
                    operaciones.remove(op)
                    cap_total = gestionar_memoria(leer=True)

            if len(operaciones) < 2:
                for p in presas:
                    if any(o['s'] == p for o in operaciones): continue
                    puedo, lado = analista_precision(p, client)
                    if puedo:
                        px = float(client.get_symbol_ticker(symbol=p)['price'])
                        print(f"\n🎯 DISPARO {lado}: {p} (Confirmado por Vela y EMA)")
                        operaciones.append({'s': p, 'l': lado, 'p': px, 'x': 10, 'c': cap_total * 0.45, 'be': False})
                        break

            print(f"💰 TOTAL: ${cap_total + ganancia_viva:.2f} | Buscando entrada...", end='\r')

        except: time.sleep(5)
        time.sleep(max(1, 15 - (time.time() - t_loop)))

if __name__ == "__main__":
    bot_run()
