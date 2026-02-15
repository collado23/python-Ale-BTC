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
    default = {"cap": 15.77, "ops": [], "u_m": ""}
    if not r: return default
    try:
        if leer:
            v = r.get("mem_sim_v180")
            return eval(v) if v else default
        else: r.set("mem_sim_v180", str(d))
    except: return default

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    
    # Cargar datos guardados
    datos = g_m(leer=True)
    cap_sim = datos["cap"]
    ops = datos["ops"]
    u_m = datos.get("u_m", "")
    
    monedas = ['SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT', 'LINKUSDT', 'PEPEUSDT']

    print(f"🚀 SIM V180 - INTELIGENCIA + PROTECCIÓN BE")

    while True:
        try:
            # Guardar estado en Redis
            g_m(d={"cap": cap_sim, "ops": ops, "u_m": u_m})

            # --- 1. SEGUIMIENTO ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI Neto con comisión
                roi_n = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # --- LÓGICA DE BREAKEVEN (Protección) ---
                if roi_n >= 0.8: o['be'] = True 
                
                # Si activó BE y cae al 0.1% (cubre comisión), cerramos
                if o.get('be') and roi_n <= 0.1:
                    print(f"\n🛡️ [SIM] BE ACTIVADO EN {o['s']}")
                    roi_n = 0.1 # Salida en neutro
                
                # Salto a 15x
                if roi_n > 0.25 and o['x'] == 6:
                    o['x'] = 15
                    print(f"\n🔥 [SIM] 15X: {o['s']}")

                # Cierres (Profit 2.5% / Stop -2.5% / Breakeven)
                if roi_n >= 2.5 or roi_n <= -2.5 or (o.get('be') and roi_n <= 0.1):
                    ganancia = cap_sim * (roi_n / 100)
                    cap_sim += ganancia
                    
                    # Filtro: Si ganó (>0.5%), guardamos moneda para no repetirla
                    u_m = o['s'] if roi_n > 0.5 else ""
                    
                    ops.remove(o)
                    print(f"\n✅ [SIM] FIN {o['l']} {o['s']} | {roi_n:.2f}% | B: ${cap_sim:.2f}")

            # --- 2. ENTRADA (Análisis de Velas y EMAs) ---
            if len(ops) < 1:
                for m in monedas:
                    if m == u_m: continue # No repetir la que acaba de ganar
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    dist = abs(e9 - e27) / e27 * 100
                    
                    # Fuerza de vela (Cuerpo actual vs Previo)
                    v_act = abs(cl[-2] - op[-2])
                    v_prev = abs(cl[-3] - op[-3])
                    
                    tipo = None
                    if cl[-2] > e9 > e27 and dist > 0.05 and v_act > v_prev:
                        tipo = "LONG"
                    elif cl[-2] < e9 < e27 and dist > 0.05 and v_act > v_prev:
                        tipo = "SHORT"

                    if tipo:
                        precio = float(c.get_symbol_ticker(symbol=m)['price'])
                        ops.append({'s':m,'l':tipo,'p':precio,'x':6, 'be': False})
                        print(f"\n🎯 [SIM] {tipo} 6X {m} (Dist: {dist:.3f}%)")
                        break

            # Pantalla ultra resumida
            print(f"B: ${cap_sim:.2f} | O: {len(ops)} | T: {time.strftime('%H:%M:%S')}", end='\r')

        except: time.sleep(10)
        time.sleep(10)

if __name__ == "__main__": bot()
