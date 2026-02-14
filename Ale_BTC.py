import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD (OBLIGATORIO) ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 2. MEMORIA REDIS (Tus $15.77) ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    c_i = 15.77
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v142")
            return float(h) if h else c_i
        else: r.set("cap_v142", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V142 (1x -> 8x -> 15x) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(); cap = g_m(leer=True); ops = []
    print(f"🦁 V142 | ${cap}")

    while True:
        t_l = time.time()
        try:
            # GESTIÓN DE POSICIONES Abiertas
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                # Escalada de X (Tu estrategia 1-8-15)
                if roi > 0.3 and o['x'] == 1: o['x'] = 8; print(f"⚡ {o['s']} 8x")
                if roi > 0.6 and o['x'] == 8: o['x'] = 15; o['be'] = True; print(f"🔥 {o['s']} 15x")

                # Cierre
                if (o['be'] and roi <= 0.01) or roi >= 1.6 or roi <= -1.1:
                    n_c = cap * (1 + (roi/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"✅ FIN {o['s']} | {roi:.2f}%")

            # BUSCAR ENTRADAS (EMA 9/27 + Velas)
            if len(ops) < 2:
                for m in ['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT']:
                    if any(x['s'] == m for x in ops): continue
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k] # Cierres
                    op = [float(x[1]) for x in k] # Aperturas
                    
                    # EMAs rápidas manuales para no cargar librerías
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, v_a = cl[-2], cl[-3]
                    o_v, o_a = op[-2], op[-3]

                    # Señal: Envolvente + EMA
                    if v > o_v and o_a > cl[-3] and v > o_a and v > e9 and e9 > e27:
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':1,'be':False})
                        print(f"🎯 LONG {m}")
                        break
                    if v < o_v and o_a < cl[-3] and v < o_a and v < e9 and e9 < e27:
                        ops.append({'s':m,'l':'SHORT','p':cl[-1],'x':1,'be':False})
                        print(f"🎯 SHORT {m}")
                        break

            print(f"💰 ${cap:.2f} | Activas: {len(ops)}", end='\r')
        except: time.sleep(10)
        time.sleep(max(1, 15 - (time.time() - t_l)))

if __name__ == "__main__": bot()
