import os, time, redis, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 🌐 SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 MEMORIA REDIS ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    default = {"cap": 15.77, "ops": []}
    if not r: return default
    try:
        if leer:
            v = r.get("mem_sim_v177_final")
            return eval(v) if v else default
        else:
            r.set("mem_sim_v177_final", str(d))
    except: return default

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    
    datos = g_m(leer=True)
    cap_sim = datos["cap"]
    ops = datos["ops"]
    
    monedas = ['SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT', 'LINKUSDT', 'PEPEUSDT']

    print(f"🚀 SIMULADOR V177 - STOP -2.5% + COMISIÓN REAL")

    while True:
        try:
            g_m(d={"cap": cap_sim, "ops": ops})

            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI CON COMISIÓN (0.1% * palanca)
                roi_n = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # Salto a 15x
                if roi_n > 0.25 and o['x'] == 6:
                    o['x'] = 15
                    print(f"\n🔥 [SIM] 15X: {o['s']} ({o['l']})")

                # Cierre: Profit 2.5% | Stop -2.5% (El margen que te funcionaba ayer)
                if roi_n >= 2.5 or roi_n <= -2.5:
                    ganancia = cap_sim * (roi_n / 100)
                    cap_sim += ganancia
                    ops.remove(o)
                    print(f"\n✅ [SIM] FIN {o['l']} | {roi_n:.2f}% | B: ${cap_sim:.2f}")

            # --- ENTRADA ---
            if len(ops) < 1:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl, op = [float(x[4]) for x in k], [float(x[1]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], op[-2]
                    
                    tipo = "LONG" if (v > o_v and v > e9 and e9 > e27) else "SHORT" if (v < o_v and v < e9 and e9 < e27) else None

                    if tipo:
                        precio = float(c.get_symbol_ticker(symbol=m)['price'])
                        ops.append({'s':m,'l':tipo,'p':precio,'x':6})
                        print(f"\n🎯 [SIM] {tipo} 6X: {m}")
                        break

            print(f"B: ${cap_sim:.2f} | O: {len(ops)} | T: {time.strftime('%H:%M:%S')}", end='\r')

        except:
            time.sleep(10)
        
        time.sleep(10)

if __name__ == "__main__": bot()
