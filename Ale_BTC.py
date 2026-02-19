import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    
    # --- 💰 CONFIGURACIÓN ---
    cap = 10.0  # <--- Poné acá la plata que quieras que use el bot
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0

    print(f"🐊 V146 REAL | CAP FIJO: ${cap} | SALTO 15X AL 1.5%")

    while True:
        ahora = time.time()
        roi_vis, gan_vis, piso_vis = 0.0, 0.0, -2.5
        
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                roi = (diff * 100 * o['x']) - 0.90
                ganancia_usd = cap * (roi / 100)
                roi_vis, gan_vis, piso_vis = roi, ganancia_usd, o['piso']
                
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.0 
                    print(f"\n🚀 SALTO 15X! {o['s']} | Entré a: {o['p']} | ROI: {roi:.2f}%")

                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0:   n_p = 24.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 8.0:  n_p = 7.5
                    elif roi >= 6.0:  n_p = 5.5
                    elif roi >= 4.0:  n_p = 3.5
                    elif roi >= 2.5:  n_p = 2.0
                    elif roi >= 2.0:  n_p = 1.5
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ ESCALADOR: {o['s']} subió piso a {o['piso']}%")

                    if roi < o['piso']:
                        cap += ganancia_usd
                        ultima_moneda = o['s']
                        tiempo_descanso = ahora
                        print(f"\n✅ VENTA: {o['s']} | Compra: {o['p']} | Venta: {p_a} | Ganancia: +${ganancia_usd:.2f} | Final: ${cap:.2f}")
                        ops.remove(o)
                        continue

                if not o['be'] and roi <= -2.5:
                    cap += ganancia_usd
                    ultima_moneda = o['s']
                    tiempo_descanso = ahora
                    print(f"\n⚠️ STOP LOSS: {o['s']} | Perdida: ${ganancia_usd:.2f}")
                    ops.remove(o)

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
                        print(f"\n🎯 ENTRADA: {m} | Precio: {cl[-1]} | Cap: ${cap:.2f}")
                        break
            
            if len(ops) > 0:
                mon = f" | {ops[0]['s']}: {roi_vis:.2f}% (${gan_vis:.2f}) | Piso: {piso_vis}%"
            elif (ahora - tiempo_descanso) <= 10:
                mon = f" | ⏳ Pausa: {int(10-(ahora-tiempo_descanso))}s"
            else: mon = " | 🔎 Buscando..."
            print(f"💰 Cap: ${cap:.2f}{mon}", end='\r')
            
        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
