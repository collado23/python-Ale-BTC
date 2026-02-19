import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🚀 2. MOTOR V146 SIMULACIÓN - ALE (VERSIÓN DETALLADA) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # Cliente de Binance (público para simulación)
    c = Client()
    
    cap = 10.44  # Tu capital de simulación
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0

    print(f"🐊 SIMULACIÓN V146 | SALTO 15X AL 1.5% | DETALLE COMPLETO")

    while True:
        ahora = time.time()
        roi_vis = 0.0
        gan_vis = 0.0
        piso_vis = -2.5
        
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI Neto y Ganancia Simulación
                roi = (diff * 100 * o['x']) - 0.90
                ganancia_usd = cap * (roi / 100)
                
                # Actualizamos visualización para el monitor
                roi_vis, gan_vis, piso_vis = roi, ganancia_usd, o['piso']
                
                # 🔥 EL SALTO AL 1.5% (A 15X)
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.0 
                    print(f"\n🚀 SIM: ¡SALTO 15X! {o['s']} | Precio Ent: {o['p']} | ROI: {roi:.2f}%")

                # 🛡️ ESCALADOR AGRESIVO (Con escalón del 6%)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0:   n_p = 24.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 8.0:  n_p = 7.5
                    elif roi >= 6.0:  n_p = 5.5 # <--- Nuevo escalón que pediste
                    elif roi >= 4.0:  n_p = 3.5
                    elif roi >= 2.5:  n_p = 2.0
                    elif roi >= 2.0:  n_p = 1.5
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ SIM ESCALADOR: {o['s']} subió piso a {o['piso']}% | ROI: {roi:.2f}%")

                    if roi < o['piso']:
                        cap += ganancia_usd
                        ultima_moneda = o['s']
                        tiempo_descanso = ahora
                        print(f"\n✅ SIM VENTA: {o['s']} | Compra: {o['p']} | Venta: {p_a} | Ganancia: +${ganancia_usd:.2f} | ROI: {roi:.2f}%")
                        ops.remove(o)
                        continue

                # ⚠️ STOP LOSS
                if not o['be'] and roi <= -2.5:
                    cap += ganancia_usd
                    ultima_moneda = o['s']
                    tiempo_descanso = ahora
                    print(f"\n⚠️ SIM STOP LOSS: {o['s']} | Perdida: -${abs(ganancia_usd):.2f} | ROI: {roi:.2f}%")
                    ops.remove(o)

            # --- 🎯 BUSCADOR (CON DESCANSO Y ROTACIÓN) ---
            if len(ops) < 1 and (ahora - tiempo_descanso) > 10:
                for m in ['SOLUSDT', 'XRPUSDT', 'BNBUSDT']:
                    if m == ultima_moneda: continue 
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    v, o_v = cl[-2], float(k[-2][1])
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27

                    if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                        tipo = 'LONG' if v > o_v else 'SHORT'
                        ops.append({'s':m,'l':tipo,'p':cl[-1],'x':5,'be':False, 'piso': -2.5})
                        print(f"\n🎯 SIM ENTRADA: {m} | Precio: {cl[-1]} | Tipo: {tipo} | Cap: ${cap:.2f}")
                        break
            
            # --- 🕒 MONITOR DETALLADO ---
            if len(ops) > 0:
                mon = f" | {ops[0]['s']}: {roi_vis:.2f}% (${gan_vis:.2f}) | Piso: {piso_vis}%"
            elif (ahora - tiempo_descanso) <= 10:
                mon = f" | ⏳ Pausa: {int(10-(ahora-tiempo_descanso))}s"
            else:
                mon = " | 🔎 Buscando..."

            print(f"💰 Sim Cap: ${cap:.2f}{mon}", end='\r')
            
        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
