import os, time, redis, threading
import numpy as np
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 🌐 SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 MEMORIA REDIS (Blindada contra reinicios) ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    default = {"cap": 15.77, "ops": [], "bloq": {}}
    if not r: return default
    try:
        if leer:
            v = r.get("mem_v193_final")
            return eval(v) if v else default
        else: r.set("mem_v193_final", str(d))
    except: return default

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    
    # Cargar memoria completa
    m = g_m(leer=True)
    cap, ops, bloq = m["cap"], m["ops"], m["bloq"]
    
    monedas = ['SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT', 'LINKUSDT', 'PEPEUSDT']
    print(f"🚀 V193 CARGADA: TODO INCLUIDO. SIN RECORTES.")

    while True:
        try:
            # Guardar estado actual
            g_m(d={"cap": cap, "ops": ops, "bloq": bloq})
            
            # Filtro de corrección: Perdona errores tras 5 min
            ahora = time.time()
            bloq = {mon: t for mon, t in bloq.items() if ahora - t < 300}

            # --- 1. SEGUIMIENTO CON COMISIONES Y BREAKEVEN ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI NETO (Descontando comisión de entrada y salida)
                roi_n = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # Salto de 6x a 15x
                if o['x'] == 6 and roi_n > 0.3:
                    o['x'] = 15; print(f"\n🔥 TURBO 15X: {o['s']}")

                # Activación de Breakeven
                if roi_n >= 0.7: o['be'] = True

                # Lógica de Cierres
                if o.get('be') and roi_n <= 0.1: # Cierre Protección
                    cap += cap * (roi_n / 100)
                    ops.remove(o); print(f"\n🛡️ BE PROTECT: {o['s']}"); break
                
                if roi_n <= -2.5: # Cierre Error (Bloquea para aprender)
                    cap += cap * (roi_n / 100)
                    bloq[o['s']] = ahora
                    ops.remove(o); print(f"\n❌ STOP/BLOQUEO: {o['s']}"); break

                if roi_n >= 2.0: # Cierre Profit
                    cap += cap * (roi_n / 100)
                    ops.remove(o); print(f"\n✅ PROFIT: {o['s']} | ${cap:.2f}"); break

            # --- 2. ENTRADA CON LIBRERÍA DE VELAS COMPLETA ---
            if len(ops) < 1:
                for s in monedas:
                    if s in bloq: continue # No entrar donde falló hace poco
                    
                    k = c.get_klines(symbol=s, interval='1m', limit=30)
                    op, hi, lo, cl = [np.array([float(x[i]) for x in k]) for i in [1,2,3,4]]
                    
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # Anatomía de Vela (Fuerza y Patrón)
                    cuerpo = abs(cl[-2] - op[-2])
                    rango = hi[-2] - lo[-2]
                    sombra_inf = min(op[-2], cl[-2]) - lo[-2]
                    sombra_sup = hi[-2] - max(op[-2], cl[-2])
                    
                    # Filtros de calidad de entrada
                    fuerza = cuerpo > (rango * 0.55) # Vela sólida
                    no_mecha_loca = sombra_sup < (cuerpo * 0.8) if cl[-2]>op[-2] else sombra_inf < (cuerpo * 0.8)

                    tipo = None
                    if cl[-2] > e9 > e27 and fuerza and no_mecha_loca:
                        tipo = "LONG"
                    elif cl[-2] < e9 < e27 and fuerza and no_mecha_loca:
                        tipo = "SHORT"

                    if tipo:
                        p = float(c.get_symbol_ticker(symbol=s)['price'])
                        ops.append({'s':s, 'l':tipo, 'p':p, 'x':6, 'be':False})
                        print(f"\n🎯 {tipo} 6X: {s} (Vela Confirmada)")
                        break

            print(f"B: ${cap:.2f} | O: {len(ops)} | BLOQ: {len(bloq)} | T: {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(2)
        time.sleep(2)

if __name__ == "__main__": bot()
