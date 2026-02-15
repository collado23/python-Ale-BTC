import os, time, redis, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 2. MEMORIA REDIS ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    c_i = 15.77
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v195")
            return float(h) if h else c_i
        else: r.set("cap_v195", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V195 (1 SOLA OPERACIÓN) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    cap = g_m(leer=True)
    ops = []
    bloq = {} # Memoria de errores
    
    print(f"🦁 V195 - UNA SOLA OPERACIÓN - ${cap}")

    while True:
        t_l = time.time()
        try:
            # Limpiar memoria de errores (5 min)
            ahora = time.time()
            bloq = {m: t for m, t in bloq.items() if ahora - t < 300}

            # --- SEGUIMIENTO DE LA OPERACIÓN ÚNICA ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                # ROI Neto (Comisión 0.1% incluida)
                roi = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # Salto a 15x (Turbo)
                if roi > 0.2 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"\n🔥 SALTO 15X: {o['s']}")

                # Cierre dinámico (Profit/Stop/BE)
                if (o['be'] and roi <= 0.05) or roi >= 1.5 or roi <= -0.9:
                    if roi <= -0.9: bloq[o['s']] = ahora
                    n_c = cap * (1 + (roi/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"\n✅ CIERRE {o['s']} | ROI: {roi:.2f}% | B: ${cap:.2f}")

            # --- BUSCAR ENTRADA (SOLO SI NO HAY NINGUNA ABIERTA) ---
            if len(ops) == 0:
                monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'ETHUSDT', 'BTCUSDT', 'XRPUSDT']
                for m in monedas:
                    if m in bloq: continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl, op, hi, lo = [[float(x[i]) for x in k] for i in [4,1,2,3]]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v_c, v_o, v_h, v_l = cl[-2], op[-2], hi[-2], lo[-2]
                    
                    # Filtro de fuerza de vela
                    fuerza = abs(v_c - v_o) > ((v_h - v_l) * 0.5)

                    # Lógica de disparo
                    if v_c > v_o and v_c > e9 > e27 and fuerza:
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':5,'be':False})
                        print(f"\n🎯 DISPARO 5x LONG: {m}")
                        break # Salimos del bucle para asegurar 1 sola operación
                    
                    if v_c < v_o and v_c < e9 < e27 and fuerza:
                        ops.append({'s':m,'l':'SHORT','p':cl[-1],'x':5,'be':False})
                        print(f"\n🎯 DISPARO 5x SHORT: {m}")
                        break

            print(f"💰 ${cap:.2f} | Activa: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
