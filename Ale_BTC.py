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

# --- 🚀 3. MOTOR V143 FRANCOTIRADOR (Ajustado) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(); cap = g_m(leer=True); ops = []
    print(f"🎯 V143 FRANCOTIRADOR | ${cap} | COMISIÓN 0.9")

    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # --- NUEVA COMISIÓN A 0.9 ---
                roi_bruto = diff * 100 * o['x']
                comision_roi = 0.9  # Ajustado según tu pedido
                roi_n = roi_bruto - comision_roi 
                
                # 1. SALTO A 15X (Pide 2.0% NETO)
                if roi_n >= 2.0 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"🔥 SALTO A 15X: {o['s']} (Ganancia consolidada)")

                # 2. CIERRES (Profit 3.5% o Stop Loss 2.5%)
                if (o['be'] and roi_n <= 0.1) or roi_n >= 3.5 or roi_n <= -2.5:
                    n_c = cap * (1 + (roi_n/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"\n✅ CIERRE EN {o['s']} | NETO: {roi_n:.2f}% | SALDO: ${cap:.2f}")

            # 3. ENTRADA (Solo 1 bala, filtro 0.6%)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'SHIBUSDT', 'BTCUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=10)
                    cl, op = float(k[-2][4]), float(k[-2][1]) # Vela cerrada anterior
                    
                    # Filtro de fuerza de 0.6%
                    mov = abs((cl - op) / op) * 100
                    
                    if mov >= 0.6:
                        # Lógica de medias móviles para dirección
                        k_full = [float(x[4]) for x in k]
                        e9, e27 = sum(k_full[-9:])/9, sum(k_full[-27:])/27
                        
                        p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                        
                        if cl > op and cl > e9 and e9 > e27: # Tendencia alcista fuerte
                            ops.append({'s':m,'l':'LONG','p':p_act,'x':5,'be':False})
                            print(f"\n🎯 DISPARO LONG: {m} (Fuerza: {mov:.2f}%)")
                            break
                        if cl < op and cl < e9 and e9 < e27: # Tendencia bajista fuerte
                            ops.append({'s':m,'l':'SHORT','p':p_act,'x':5,'be':False})
                            print(f"\n🎯 DISPARO SHORT: {m} (Fuerza: {mov:.2f}%)")
                            break

            status = f"ROI: {roi_n:.2f}%" if len(ops) > 0 else "Acechando 0.6%..."
            print(f"💰 ${cap:.2f} | {status} | {time.strftime('%H:%M:%S')}   ", end='\r')
            
        except: time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
