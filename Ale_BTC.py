import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🚀 2. MOTOR V143 FRANCOTIRADOR ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    cap = 15.77 
    ops = []
    
    print(f"🎯 V143 AGRESIVA | STOP -1.6 | SALTO 2.5 | CON ESCALADOR")

    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                roi_bruto = diff * 100 * o['x']
                roi_n = roi_bruto - 0.9 
                
                # 🔥 1. SALTO A 15X (Cuando toca 2.5% NETO)
                if roi_n >= 2.5 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 2.0 # Primer piso asegurado
                    try: c.futures_change_leverage(symbol=o['s'], leverage=15)
                    except: pass
                    print(f"\n🔥 SALTO A 15X Y PISO 2.0%: {o['s']}")

                # 🪜 2. ESCALADOR (Sube el piso de 0.5 en 0.5 para arriba)
                if o['be']:
                    # Si el ROI sube, el piso sube manteniendo 0.5% de distancia
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']:
                        o['piso'] = nuevo_piso

                # 📉 3. CIERRES
                # Si saltó (be), cierra si cae del piso. Si no saltó, cierra en -1.6
                check_cierre = o['piso'] if o['be'] else -1.6
                
                if (roi_n >= 3.5 and not o['be']) or roi_n <= check_cierre:
                    n_c = cap * (1 + (roi_n/100))
                    cap = n_c
                    ops.remove(o)
                    print(f"\n✅ CIERRE EN {o['s']} | NETO: {roi_n:.2f}% | PISO FINAL: {check_cierre:.2f}% | SALDO: ${cap:.2f}")

            # 🎯 4. ENTRADA (Lógica E9/E27 original)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'SHIBUSDT', 'BTCUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=50)
                    cl, op_v = float(k[-2][4]), float(k[-2][1]) 
                    
                    k_full = [float(x[4]) for x in k]
                    e9, e27 = sum(k_full[-9:])/9, sum(k_full[-27:])/27
                    
                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                    
                    if cl > op_v and cl > e9 and e9 > e27: # LONG
                        ops.append({'s':m,'l':'LONG','p':p_act,'x':5,'be':False, 'piso': -1.6})
                        print(f"\n🎯 DISPARO LONG: {m}")
                        break
                    if cl < op_v and cl < e9 and e9 < e27: # SHORT
                        ops.append({'s':m,'l':'SHORT','p':p_act,'x':5,'be':False, 'piso': -1.6})
                        print(f"\n🎯 DISPARO SHORT: {m}")
                        break

            status = f"ROI: {roi_n:.2f}%" if len(ops) > 0 else "Acechando entrada..."
            print(f"💰 ${cap:.2f} | {status} | {time.strftime('%H:%M:%S')}   ", end='\r')
            
        except: 
            time.sleep(5)
        
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": 
    bot()
