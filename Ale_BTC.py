import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🚀 2. MOTOR V146 SIMULACIÓN (SALTO AL 0.9%) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    cap = 10.0 
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0

    print(f"🐊 SIM V146 ULTRA-AGRESIVA | SALTO 15X AL 0.9% | $10")

    while True:
        t_l = time.time()
        ganancia_vivo_usd = 0.0
        roi_vivo = 0.0
        ahora = time.time()
        
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI Neto (Precio - Comisión -0.90%)
                roi = (diff * 100 * o['x']) - 0.90
                roi_vivo = roi
                ganancia_vivo_usd = cap * (roi / 100)
                
                # 🔥 DISPARO AL 0.9% (Apenas salís del rojo de la comisión)
                if roi >= 0.9 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 0.4 # Piso inicial para asegurar el peaje
                    print(f"\n🚀 ¡SALTO A 15X! (ROI: {roi:.2f}%) en {o['s']}")

                # ESCALADOR (0.5% de margen siempre)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0: n_p = 24.5
                    elif roi >= 20.0: n_p = 19.5
                    elif roi >= 15.0: n_p = 14.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 8.0:  n_p = 7.5
                    elif roi >= 6.0:  n_p = 5.5
                    elif roi >= 4.0:  n_p = 3.5
                    elif roi >= 2.0:  n_p = 1.5
                    elif roi >= 1.0:  n_p = 0.5 
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ ESCALADOR: {o['s']} subió piso a {o['piso']}%")

                    # CIERRE POR PISO
                    if roi < o['piso']:
                        cap = cap + ganancia_vivo_usd
                        ultima_moneda = o['s']
                        tiempo_descanso = ahora
                        print(f"\n✅ COBRO SIM: {o['s']} | Netos: +${ganancia_vivo_usd:.2f}")
                        ops.remove(o)
                        continue

                # STOP LOSS (-2.5%)
                if not o['be'] and roi <= -2.5:
                    cap = cap + ganancia_vivo_usd
                    ultima_moneda = o['s']
                    tiempo_descanso = ahora
                    print(f"\n⚠️ STOP LOSS SIM: {o['s']} | -${abs(ganancia_vivo_usd):.2f}")
                    ops.remove(o)

            # --- 🎯 BUSCADOR ---
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
                        print(f"\n🎯 ENTRADA SIM: {m} ({tipo})")
                        break
            
            # MONITOR
            mon = f" | {ops[0]['s']}: ${ganancia_vivo_usd:.2f} ({roi_vivo:.2f}%)" if len(ops) > 0 else " | 🔎 Buscando..."
            print(f"💰 Sim: ${cap:.2f}{mon} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
