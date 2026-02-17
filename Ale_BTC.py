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

# --- 🚀 3. MOTOR V143 FRANCOTIRADOR ROTATIVO ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(); cap = g_m(leer=True); ops = []
    
    monedas_target = ['SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    indice_moneda = 0 
    
    print(f"🎯 V143 FRANCOTIRADOR | ${cap:.2f} | PROTECCIÓN 0.15%")

    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                roi_bruto = diff * 100 * o['x']
                comision_roi = 0.9  
                roi_n = roi_bruto - comision_roi 
                
                # 1. SALTO A 15X (Pide 2.0% NETO)
                if roi_n >= 2.0 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"\n🔥 SALTO A 15X EN {o['s']} (Activando protección 0.15%)")

                # 2. CIERRES (Ajustado a 0.15% en BE)
                if (o['be'] and roi_n <= 0.15) or roi_n >= 3.5 or roi_n <= -2.5:
                    n_c = cap * (1 + (roi_n/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"\n✅ CIERRE EN {o['s']} | NETO: {roi_n:.2f}% | SALDO: ${cap:.2f}")
                    
                    # Rotación de moneda al cerrar
                    indice_moneda = (indice_moneda + 1) % len(monedas_target)
                    print(f"🔄 PRÓXIMO OBJETIVO: {monedas_target[indice_moneda]}")

            # 3. ENTRADA (Bidireccional EMA 1/32)
            if len(ops) < 1:
                m = monedas_target[indice_moneda]
                k = c.get_klines(symbol=m, interval='1m', limit=50)
                cl = [float(x[4]) for x in k]
                
                e1, e32 = cl[-1], sum(cl[-32:])/32 
                v_act, v_apert = cl[-1], float(k[-1][1])
                p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                
                if v_act > v_apert and e1 > e32: # LONG
                    ops.append({'s':m,'l':'LONG','p':p_act,'x':5,'be':False})
                    print(f"\n🎯 DISPARO LONG: {m}")
                elif v_act < v_apert and e1 < e32: # SHORT
                    ops.append({'s':m,'l':'SHORT','p':p_act,'x':5,'be':False})
                    print(f"\n🎯 DISPARO SHORT: {m}")

            status = f"ROI: {roi_n:.2f}%" if len(ops) > 0 else f"Acechando {monedas_target[indice_moneda]}..."
            print(f"💰 ${cap:.2f} | {status} | {time.strftime('%H:%M:%S')}   ", end='\r')
            
        except: time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
