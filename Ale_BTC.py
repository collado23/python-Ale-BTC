import os, time, redis, json, threading
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
    c_i = 14.87 
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v211_08")
            return float(h) if h else c_i
        else: r.set("cap_v211_08", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V211 (Salto 0.8%) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(); cap = g_m(leer=True); ops = []
    print(f"🦁 V211 | SALTO 15X A 0.8% | ${cap}")

    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI Neto real (Comisión 0.1% * Palanca)
                roi = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # --- 1. ESCALADA MÁS SEGURA (A 0.8%) ---
                if roi > 0.8 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"🔥 POTENCIA 15X CONFIRMADA (0.8%): {o['s']}")

                # --- 2. MODO "SI SUBE MÁS" ---
                if roi >= 6.0:
                    o['max_roi'] = max(o.get('max_roi', 0), roi)
                    o['modo_trail'] = True

                # --- 3. CONDICIONES DE CIERRE ---
                cierre = False
                if o.get('modo_trail'):
                    if roi < (o['max_roi'] - 0.5): # Cierre si cae 0.5% desde el pico
                        cierre = True
                elif (o['be'] and roi <= 0.1) or roi <= -0.9:
                    cierre = True
                
                if roi >= 15.0: cierre = True # Techo de seguridad extrema

                if cierre:
                    n_c = cap * (1 + (roi/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"✅ CIERRE {o['s']} | NETO: {roi:.2f}% | BAL: ${cap:.2f}")

            # --- ENTRADA: TU GATILLO DE AYER ---
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, v_a, o_v, o_a = cl[-2], cl[-3], op[-2], op[-3]

                    if v > o_v and v > o_a and v > e9 and e9 > e27:
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':5,'be':False})
                        print(f"🎯 DISPARO LONG: {m}")
                        break 
                    if v < o_v and v < o_a and v < e9 and e9 < e27:
                        ops.append({'s':m,'l':'SHORT','p':cl[-1],'x':5,'be':False})
                        print(f"🎯 DISPARO SHORT: {m}")
                        break 

            print(f"💰 ${cap:.2f} | Activa: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
