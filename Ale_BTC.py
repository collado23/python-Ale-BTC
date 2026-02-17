import os, time, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client() # MODO SIMULACIÓN (No necesita llaves reales)
    
    # --- VARIABLES DE SIMULACIÓN ---
    monedas = ['LINKUSDT', 'PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT']
    saldo_sim = 22.19  # Tu saldo actual para ver si recuperamos
    ops_sim = []
    
    print(f"🎮 SIMULADOR V163 + COMISIONES")
    print(f"📈 Estrategia: E9 > E27 | Salto 5x -> 15x")

    while True:
        try:
            # --- 1. SEGUIMIENTO DE OPERACIÓN SIMULADA ---
            if len(ops_sim) > 0:
                o = ops_sim[0]
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                
                # Diferencia de precio y ROI Bruto
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_bruto = diff * 100 * o['x']
                
                # Descontamos comisión (0.08% total * apalancamiento)
                comision_roi = 0.08 * o['x']
                roi_neto = roi_bruto - comision_roi
                
                # SALTO MÁGICO A 15X (Si el neto es bueno)
                if roi_neto > 0.3 and o['x'] == 5:
                    o['x'] = 15
                    print(f"🔥 SIM_OPORTUNIDAD: Subiendo a 15x en {o['s']}")

                # CIERRES (Netos)
                if roi_neto >= 2.5 or roi_neto <= -1.5:
                    saldo_sim += (o['monto'] * roi_neto / 100)
                    print(f"\n✅ SIM_CIERRE {o['s']} | NETO: {roi_neto:.2f}% | Saldo: ${saldo_sim:.2f}")
                    ops_sim.pop()
                    time.sleep(10)

            # --- 2. ENTRADA SIMULADA ---
            elif saldo_sim >= 10:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # Lógica de cruce de medias
                    if cl[-2] > e9 and e9 > e27:
                        precio = float(c.get_symbol_ticker(symbol=m)['price'])
                        ops_sim.append({
                            's': m, 'l': 'LONG', 'p': precio, 
                            'monto': saldo_sim, 'x': 5
                        })
                        print(f"\n🎯 SIM_ENTRADA 5X EN {m}")
                        break

            # STATUS
            if len(ops_sim) == 0:
                print(f"📊 SALDO SIM: ${saldo_sim:.2f} | Buscando cruce E9/E27...      ", end='\r')
            else:
                print(f"⏳ EN POSICIÓN: {ops_sim[0]['s']} | ROI NETO: {roi_neto:.2f}%      ", end='\r')

        except: time.sleep(5)
        time.sleep(2)

if __name__ == "__main__": bot()
