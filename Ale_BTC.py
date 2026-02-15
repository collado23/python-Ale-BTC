import os, time, redis, threading
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 2. MEMORIA REDIS (Sincronizada) ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    c_i = 15.18 # Saldo real tras los logs
    if not r: return c_i
    try:
        if leer:
            h = r.get("mem_alt_v197")
            return float(h) if h else c_i
        else:
            if d > 0: r.set("mem_alt_v197", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V197 (SOLO UNA OP / ALTCOINS) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    cap = g_m(leer=True)
    ops = []
    bloq = {} # Memoria de errores corregida
    
    print(f"🦁 V197 - SOLO ALTCOINS - ${cap}")

    while True:
        t_l = time.time()
        try:
            # Sincronizar capital con Redis
            cap_r = g_m(leer=True)
            if cap_r < cap: cap = cap_r

            ahora = time.time()
            bloq = {m: t for m, t in bloq.items() if ahora - t < 300}

            # --- SEGUIMIENTO ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                # ROI Neto con comisiones (0.1% * palanca)
                roi = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # Salto a 15x
                if roi > 0.2 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"\n🔥 15X ACTIVADO: {o['s']}")

                # Cierres (BE 0.05% / TP 1.5% / SL -0.9%)
                if (o['be'] and roi <= 0.05) or roi >= 1.5 or roi <= -0.9:
                    if roi <= -0.9: bloq[o['s']] = ahora
                    cap = cap * (1 + (roi/100))
                    g_m(d=cap) # Guardar en Redis inmediatamente
                    ops.remove(o)
                    print(f"\n✅ CIERRE {o['s']} | NETO: {roi:.2f}% | B: ${cap:.2f}")

            # --- BUSCAR ENTRADA (SOLO ALTCOINS) ---
            if len(ops) == 0:
                # Quitamos BTC y ETH por tu pedido
                monedas = ['SOLUSDT', 'PEPEUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT']
                for m in monedas:
                    if m in bloq: continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=50)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    hi = [float(x[2]) for x in k]
                    lo = [float(x[3]) for x in k]
                    
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v_c, v_o = cl[-2], op[-2]
                    
                    # Filtro de fuerza de vela (Anatomía Japonesa)
                    fuerza = abs(v_c - v_o) > ((hi[-2] - lo[-2]) * 0.6)

                    # Lógica de disparo limpia
                    if v_c > v_o and v_c > e9 > e27 and fuerza:
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':5,'be':False})
                        print(f"\n🎯 LONG 5X: {m}")
                        break
                    
                    if v_c < v_o and v_c < e9 < e27 and fuerza:
                        ops.append({'s':m,'l':'SHORT','p':cl[-1],'x':5,'be':False})
                        print(f"\n🎯 SHORT 5X: {m}")
                        break

            print(f"💰 ${cap:.2f} | Op: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
