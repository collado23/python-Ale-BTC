import os, time, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 🌐 SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # --- CONFIGURACIÓN DEL SIMULADOR ---
    c = Client() 
    cap_sim = 15.77  # Capital inicial de prueba
    ops = []
    # Tus 6 monedas sin BTC ni ETH
    monedas = ['SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT', 'LINKUSDT', 'PEPEUSDT']

    print(f"🚀 SIMULADOR V174 - PANTALLA V170 - 6X -> 15X")

    while True:
        try:
            # --- SEGUIMIENTO DE OPERACIONES ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                
                # ROI según dirección
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # Salto a 15x
                if roi_neto > 0.25 and o['x'] == 6:
                    o['x'] = 15
                    print(f"🔥 SALTO A 15X EN {o['s']} ({o['l']})")

                # Cierre
                if roi_neto >= 2.5 or roi_neto <= -1.3:
                    ganancia = cap_sim * (roi_neto / 100)
                    cap_sim += ganancia
                    ops.remove(o)
                    print(f"✅ CIERRE {o['l']} | NETO: {roi_neto:.2f}% | CAP: ${cap_sim:.2f}")

            # --- ENTRADA BIDIRECCIONAL ---
            if len(ops) < 1:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    v, o_v = cl[-2], op[-2]
                    tipo = None
                    
                    if v > o_v and v > e9 and e9 > e27: tipo = "LONG"
                    elif v < o_v and v < e9 and e9 < e27: tipo = "SHORT"

                    if tipo:
                        precio = float(c.get_symbol_ticker(symbol=m)['price'])
                        ops.append({'s':m,'l':tipo,'p':precio,'x':6})
                        print(f"🎯 ENTRADA {tipo} 6X EN {m}")
                        break

            # PANTALLA ESTILO V170
            print(f"💰 Bi: ${cap_sim:.2f} | Ops: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')

        except Exception as e:
            # Si hay error de conexión, no se muere, solo espera
            time.sleep(10)
        
        time.sleep(10)

if __name__ == "__main__":
    bot()
