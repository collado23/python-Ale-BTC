import os, time, redis, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 MEMORIA REDIS ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    c_i = 13.66 
    if not r: return c_i
    try:
        if leer:
            h = r.get("mem_final_v200")
            return float(h) if h else c_i
        else: r.set("mem_final_v200", str(d))
    except: return c_i

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    cap = g_m(leer=True)
    ops = []
    
    print(f"🦁 V200 - LÓGICA ORIGINAL + COMISIONES | BAL: ${cap}")

    while True:
        t_l = time.time()
        try:
            # --- SEGUIMIENTO CON COMISIÓN ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI NETO: Diferencia * Palanca - (Comisión de entrada y salida 0.1% * Palanca)
                roi = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # Escalada 5x a 15x
                if roi > 0.2 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"🔥 SALTO A 15X: {o['s']}")

                # Cierres (Tu lógica: BE 0.05, TP 1.5, SL -0.9)
                # Al ser ROI NETO, el 0.05 de BE ya es ganancia limpia.
                if (o['be'] and roi <= 0.05) or roi >= 1.5 or roi <= -0.9:
                    n_c = cap * (1 + (roi/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"✅ CIERRE {o['s']} | NETO: {roi:.2f}% | BAL: ${cap:.2f}")

            # --- ENTRADA: TU ACCIÓN DE PRECIO FIEL ---
            if len(ops) < 1: 
                # Solo las Alts que pediste
                for m in ['SOLUSDT', 'PEPEUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, v_a, o_v, o_a = cl[-2], cl[-3], op[-2], op[-3]

                    # GATILLO ORIGINAL: v > o_v y v > o_a
                    if v > o_v and v > o_a and v > e9 and e9 > e27:
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':5,'be':False})
                        print(f"🎯 DISPARO 5x LONG: {m}")
                        break
                    
                    if v < o_v and v < o_a and v < e9 and e9 < e27:
                        ops.append({'s':m,'l':'SHORT','p':cl[-1],'x':5,'be':False})
                        print(f"🎯 DISPARO 5x SHORT: {m}")
                        break

            print(f"💰 ${cap:.2f} | Activa: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
