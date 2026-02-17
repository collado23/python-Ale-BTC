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
    c_i = 15.77 
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v143")
            return float(h) if h else c_i
        else: r.set("cap_v143", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V143 FRANCOTIRADOR (Cruce Real Time) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(); cap = g_m(leer=True); ops = []
    
    monedas_target = ['SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    idx = 0 
    
    print(f"🎯 FRANCOTIRADOR ALE | Cruz EMA 1/32 | ${cap:.2f}")

    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                roi_n = (diff * 100 * o['x']) - 0.9 
                
                # 1. SALTO A 15X (al tocar 2.0% neto)
                if roi_n >= 2.0 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"\n🔥 SALTO A 15X EN {o['s']} | PROTECCIÓN 0.5% ACTIVADA")

                # 2. CIERRES (Ajustado a 0.5% en Protección)
                if (o['be'] and roi_n <= 0.5) or roi_n >= 3.5 or roi_n <= -2.5:
                    n_c = cap * (1 + (roi_n/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"\n✅ CIERRE EN {o['s']} | NETO: {roi_n:.2f}% | SALDO: ${cap:.2f}")
                    # Rotar a la siguiente moneda
                    idx = (idx + 1) % len(monedas_target)

            # 3. ENTRADA (Lógica de la Cruz en la imagen)
            if len(ops) < 1:
                m = monedas_target[idx]
                k = c.get_klines(symbol=m, interval='1m', limit=50)
                cl = [float(x[4]) for x in k]
                
                e32 = sum(cl[-32:])/32 
                precio_anterior = cl[-1]
                p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                
                if precio_anterior <= e32 and p_act > e32: # CRUZ ARRIBA
                    ops.append({'s': m, 'l': 'LONG', 'p': p_act, 'x': 5, 'be': False})
                    print(f"\n❌ CRUZ ARRIBA EN {m} | DISPARO LONG")
                elif precio_anterior >= e32 and p_act < e32: # CRUZ ABAJO
                    ops.append({'s': m, 'l': 'SHORT', 'p': p_act, 'x': 5, 'be': False})
                    print(f"\n❌ CRUZ ABAJO EN {m} | DISPARO SHORT")

            status = f"ROI: {roi_n:.2f}%" if len(ops) > 0 else f"Buscando cruz en {monedas_target[idx]}..."
            print(f"💰 ${cap:.2f} | {status} | {time.strftime('%H:%M:%S')}   ", end='\r')
            
        except: time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
