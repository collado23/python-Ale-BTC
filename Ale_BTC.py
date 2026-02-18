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
    c_i = 10.0 
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v146_sim_agresivo")
            return float(h) if h else c_i
        else: r.set("cap_v146_sim_agresivo", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V146 SIMULACIÓN (SALTO 1.5%) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    cap = g_m(leer=True)
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0

    print(f"🐊 SIM V146 AGRESIVA | SALTO 15X AL 1.5% | $10")

    while True:
        t_l = time.time()
        ganancia_vivo_usd = 0.0
        roi_vivo = 0.0
        ahora = time.time()
        
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI Neto (-0.90% comisión)
                roi = (diff * 100 * o['x']) - 0.90
                roi_vivo = roi
                ganancia_vivo_usd = cap * (roi / 100)
                
                # 🔥 NUEVO DISPARO: SALTO A 15X AL 1.5%
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.0 # Asegura el 1% si retrocede
                    print(f"\n🚀 SALTO 15X (1.5% alcanzado): {o['s']}")

                # ESCALADOR 0.5% (Manteniendo la lógica de protección)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0: n_p = 24.5
                    elif roi >= 20.0: n_p = 19.5
                    elif roi >= 15.0: n_p = 14.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 8.0:  n_p = 7.5
                    elif roi >= 6.0:  n_p = 5.5
                    elif roi >= 4.0:  n_p = 3.5
                    elif roi >= 2.0:  n_p = 1.5 # Paso intermedio
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ ESCALADOR: {o['s']} subió piso a {o['piso']}%")

                    if roi < o['piso']:
                        cap = cap + ganancia_vivo_usd
                        g_m(d=cap)
                        ultima_moneda = o['s']
                        tiempo_descanso = ahora
                        print(f"\n✅ SIM COBRO: {o['s']} | Ganancia: +${ganancia_vivo_usd:.2f}")
                        ops.remove(o)
                        continue

                # STOP LOSS
                if not o['be'] and roi <= -2.5:
                    cap = cap + ganancia_vivo_usd
                    g_m(d=cap)
                    ultima_moneda = o['s']
                    tiempo_descanso = ahora
                    print(f"\n⚠️ SIM STOP LOSS: {o['s']} | Pérdida: ${ganancia_vivo_usd:.2f}")
                    ops.remove(o)

            # --- 🎯 BUSCADOR CON DESCANSO ---
            if len(ops) < 1 and (ahora - tiempo_descanso) > 10:
                for m in ['SOLUSDT', 'XRPUSDT', 'BNBUSDT']:
                    if m == ultima_moneda: continue 
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], float(k[-2][1])

                    if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                        tipo = 'LONG' if v > o_v else 'SHORT'
                        ops.append({'s':m,'l':tipo,'p':cl[-1],'x':5,'be':False, 'piso': -2.5})
                        print(f"\n🎯 SIM ENTRADA: {m} ({tipo})")
                        break
            elif len(ops) < 1 and (ahora - tiempo_descanso) <= 10:
                print(f"⏳ Pausa 10s... {int(10-(ahora-tiempo_descanso))}s", end='\r')

            # MONITOR
            mon = f" | {ops[0]['s']}: ${ganancia_vivo_usd:.2f} ({roi_vivo:.2f}%)" if len(ops) > 0 else " | 🔎 Buscando..."
            print(f"💰 Sim: ${cap:.2f}{mon} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except: time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
