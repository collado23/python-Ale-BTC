import os, time, redis, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 2. MEMORIA REDIS BLINDADA ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    c_i = 15.77
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v194")
            return float(h) if h else c_i
        else: r.set("cap_v194", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V194 (Acción de Precio + Velas Japonesas) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    cap = g_m(leer=True)
    ops = []
    bloq = {} # Memoria de errores para no repetir malas entradas
    
    print(f"🦁 V194 ACTIVADA | EL RETORNO | ${cap}")

    while True:
        t_l = time.time()
        try:
            # Limpiar bloqueos de errores (5 minutos)
            ahora = time.time()
            bloq = {m: t for m, t in bloq.items() if ahora - t < 300}

            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                # ROI Neto (descontando 0.1% de comisión total)
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # Escalada Ultra Rápida (5x a 15x)
                if roi > 0.2 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"\n🔥 TURBO 15X: {o['s']}")

                # Cierre dinámico: Breakeven, Profit rápido o Stop cortito
                if (o['be'] and roi <= 0.05) or roi >= 1.5 or roi <= -0.9:
                    # Si perdió, bloqueamos la moneda para aprender del error
                    if roi <= -0.9: bloq[o['s']] = ahora
                    
                    n_c = cap * (1 + (roi/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"\n✅ FIN {o['s']} | NETO: {roi:.2f}% | B: ${cap:.2f}")

            if len(ops) < 2:
                monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'ETHUSDT', 'BTCUSDT', 'XRPUSDT']
                for m in monedas:
                    if any(x['s'] == m for x in ops) or m in bloq: continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k] # Close
                    op = [float(x[1]) for x in k] # Open
                    hi = [float(x[2]) for x in k] # High
                    lo = [float(x[3]) for x in k] # Low
                    
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v_c, v_o, v_h, v_l = cl[-2], op[-2], hi[-2], lo[-2] # Vela anterior cerrada
                    
                    # Inteligencia de Velas Japonesas:
                    cuerpo = abs(v_c - v_o)
                    rango = v_h - v_l
                    # Solo entramos si la vela tiene cuerpo (fuerza) y no es pura mecha
                    fuerza_vela = cuerpo > (rango * 0.5)

                    # Gatillo: Tu lógica original + Anatomía de vela
                    if v_c > v_o and v_c > e9 and e9 > e27 and fuerza_vela:
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':5,'be':False})
                        print(f"\n🎯 DISPARO 5x LONG: {m}")
                        break
                    
                    if v_c < v_o and v_c < e9 and e9 < e27 and fuerza_vela:
                        ops.append({'s':m,'l':'SHORT','p':cl[-1],'x':5,'be':False})
                        print(f"\n🎯 DISPARO 5x SHORT: {m}")
                        break

            print(f"💰 ${cap:.2f} | Ops: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
