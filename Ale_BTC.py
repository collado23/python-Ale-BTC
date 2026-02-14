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
    c_i = 35.00  # Arrancamos con lo que ganaste en simulación
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v145_real")
            return float(h) if h else c_i
        else: r.set("cap_v145_real", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V145 (CON VARIABLES BINANCE_API) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # AQUÍ ESTÁ EL CAMBIO: El bot ahora busca tus nombres específicos
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    c = Client(api_key, api_secret)
    cap = g_m(leer=True)
    ops = []
    
    print(f"🦁 V145 REAL | Conectado con BINANCE_API | Cap: ${cap}")

    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                if roi > 0.2 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"🔥 SALTO 15X REAL: {o['s']}")
                    try: c.futures_change_leverage(symbol=o['s'], leverage=15)
                    except: pass

                if (o['be'] and roi <= 0.05) or roi >= 1.5 or roi <= -0.9:
                    lado_cierre = "SELL" if o['l'] == "LONG" else "BUY"
                    c.futures_create_order(symbol=o['s'], side=lado_cierre, type='MARKET', quantity=o['q'])
                    
                    n_c = cap * (1 + (roi/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"✅ CIERRE REAL | ROI: {roi:.2f}% | Saldo: ${n_c:.2f}")

            if len(ops) < 2:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'ETHUSDT', 'BTCUSDT']:
                    if any(x['s'] == m for x in ops): continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], op[-2]

                    if v > o_v and v > e9 and e9 > e27: # Señal LONG
                        precio = cl[-1]
                        qty = round((cap * 0.9 * 5) / precio, 0)
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                        ops.append({'s':m,'l':'LONG','p':precio,'x':5,'q':qty,'be':False})
                        print(f"🎯 COMPRA REAL: {m}")
                        break
                        
                    if v < o_v and v < e9 and e9 < e27: # Señal SHORT
                        precio = cl[-1]
                        qty = round((cap * 0.9 * 5) / precio, 0)
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side='SELL', type='MARKET', quantity=qty)
                        ops.append({'s':m,'l':'SHORT','p':precio,'x':5,'q':qty,'be':False})
                        print(f"🎯 VENTA REAL: {m}")
                        break

            print(f"💰 REAL: ${cap:.2f} | Activas: {len(ops)}", end='\r')

        except Exception as e:
            print(f"⚠️ Esperando conexión/llaves: {e}")
            time.sleep(10)
        
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
