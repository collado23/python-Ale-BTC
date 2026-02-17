import os, time, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- SERVER DE SALUD (Para mantener el bot vivo) ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client() # Simulación
    
    # --- CONFIGURACIÓN DE ACCIÓN RÁPIDA ---
    monedas = ['SHIBUSDT', 'PEPEUSDT']
    saldo_sim = 27.58
    ops_sim = []
    leverage = 15
    comision_roi = 1.2 # Lo que descuenta Binance por entrar/salir a 15x

    print(f"🔥 SIMULADOR ACCIÓN RÁPIDA ACTIVADO")
    print(f"🎯 ESTRATEGIA 2-1-1 (2 Sat + 1 Giro + 1 Distancia)")
    print(f"💰 Saldo inicial: ${saldo_sim:.2f}")

    while True:
        try:
            # 1. SI HAY OPERACIÓN ABIERTA
            if len(ops_sim) > 0:
                o = ops_sim[0]
                ticker = c.get_symbol_ticker(symbol=o['s'])
                p_a = float(ticker['price'])
                
                # Cálculo de ROI Neto
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - comision_roi
                
                # Salida de Scalper (Corta rápido para sumar)
                if roi_neto >= 0.8 or roi_neto <= -1.2:
                    saldo_sim += (o['monto'] * roi_neto / 100)
                    print(f"\n✅ CIERRE EN {o['s']} | ROI NETO: {roi_neto:.2f}% | Saldo: ${saldo_sim:.2f}")
                    ops_sim.pop()

            # 2. SI NO HAY OPERACIÓN, BUSCAMOS DISPARO
            else:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=10)
                    
                    # LÓGICA 2-1-1 (Para que "muerda" rápido)
                    # A. 2 Velas de racha
                    v_sat = k[-5:-3]
                    s_r = all(float(v[4]) < float(v[1]) for v in v_sat) # 2 Rojas
                    s_v = all(float(v[4]) > float(v[1]) for v in v_sat) # 2 Verdes
                    
                    # B. 1 Vela de giro
                    v_giro = k[-3]
                    g_v = float(v_giro[4]) > float(v_giro[1]) # Giro a Verde
                    g_r = float(v_giro[4]) < float(v_giro[1]) # Giro a Roja
                    
                    # C. 1 Vela de distancia (Tu confirmación)
                    v_dist = k[-2]
                    c_dist = "VERDE" if float(v_dist[4]) > float(v_dist[1]) else "ROJA"

                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                    lado = ""
                    
                    if s_r and g_v and c_dist == "VERDE": lado = "LONG"
                    if s_v and g_r and c_dist == "ROJA": lado = "SHORT"

                    if lado:
                        ops_sim.append({'s':m, 'l':lado, 'p':p_act, 'monto': saldo_sim})
                        print(f"\n🚀 DISPARO RÁPIDO EN {m} ({lado}) | Patrón 2-1-1")
                        break

            # STATUS EN LÍNEA
            if len(ops_sim) == 0:
                print(f"📊 SALDO: ${saldo_sim:.2f} | Acechando SHIB/PEPE (Modo Rápido)...", end='\r')
            else:
                print(f"⏳ EN POSICIÓN: {ops_sim[0]['s']} | ROI NETO: {roi_neto:.2f}%      ", end='\r')

        except:
            time.sleep(2)
        time.sleep(1)

if __name__ == "__main__": bot()
