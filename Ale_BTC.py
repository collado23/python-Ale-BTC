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
    c_i = 15.00  
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v146_ale")
            return float(h) if h else c_i
        else: r.set("cap_v146_ale", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V146 (SALTO 2.0% | MARGEN 0.5%) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(); cap = g_m(leer=True); ops = []
    print(f"🐊 V146 ALE | SALTO 2.0% | MARGEN 0.5% | ${cap}")

    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                # 1. SALTO A 15X (Vuelve a 2.0% como pediste)
                if roi >= 2.0 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.5 # Al saltar en 2.0%, ya asegura 1.5%
                    print(f"\n🔥 SALTO A 15X: {o['s']} | Piso inicial 1.5%")

                # 2. LÓGICA DE ESCALADOR INTERCALADO (A 0.5% DE DISTANCIA)
                if o['be']:
                    nuevo_piso = o['piso']
                    # Escalones pegaditos (Margen de 0.5%)
                    if roi >= 25.0: nuevo_piso = 24.5
                    elif roi >= 20.0: nuevo_piso = 19.5
                    elif roi >= 15.0: nuevo_piso = 14.5
                    elif roi >= 10.0: nuevo_piso = 9.5
                    elif roi >= 8.0:  nuevo_piso = 7.5
                    elif roi >= 6.0:  nuevo_piso = 5.5
                    elif roi >= 4.0:  nuevo_piso = 3.5
                    # El nivel de 2.0 ya está cubierto por el salto inicial
                    
                    if nuevo_piso > o['piso']:
                        o['piso'] = nuevo_piso
                        print(f"\n🛡️ ESCALADOR: Nuevo piso en {o['piso']}% (ROI actual: {roi:.2f}%)")

                    # CIERRE POR RETROCESO
                    if roi < o['piso']:
                        n_c = cap * (1 + (roi/100))
                        g_m(d=n_c); ops.remove(o); cap = n_c
                        print(f"\n✅ COBRO REALIZADO {o['s']} | ROI: {roi:.2f}% | Piso: {o['piso']}%")
                        continue

                # 3. STOP LOSS DE SEGURIDAD (-2.5%)
                if not o['be'] and roi <= -2.5:
                    n_c = cap * (1 + (roi/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"\n⚠️ STOP LOSS {o['s']} | ROI: {roi:.2f}%")

            # --- BUSCADOR DE ENTRADAS ---
            if len(ops) < 2:
                for m in ['BNBUSDT', 'XRPUSDT', 'SOLUSDT', 'BTCUSDT']:
                    if any(x['s'] == m for x in ops): continue
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], float(k[-2][1])

                    if v > o_v and v > e9 and e9 > e27:
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':5,'be':False, 'piso': -2.5})
                        print(f"\n🎯 DISPARO LONG: {m}")
                        break
                    if v < o_v and v < e9 and e9 < e27:
                        ops.append({'s':m,'l':'SHORT','p':cl[-1],'x':5,'be':False, 'piso': -2.5})
                        print(f"\n🎯 DISPARO SHORT: {m}")
                        break

            print(f"💰 ${cap:.2f} | Activas: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')
        except Exception as e: 
            time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
