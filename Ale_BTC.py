import os, time, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- SERVER DE SALUD (Para que el bot no se muera) ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    # Usamos Client sin llaves o con llaves solo para lectura
    c = Client() 
    
    # --- VARIABLES DE SIMULACIÓN ---
    monedas = ['SHIBUSDT', 'PEPEUSDT']
    saldo_sim = 27.58  # Tu saldo inicial para ver cómo crece
    ops_sim = []       # Lista de operaciones simuladas
    leverage = 15
    comision_roi = 1.2 # Lo que restamos de ROI por entrar y salir a 15x

    print(f"🎮 MODO SIMULACIÓN ACTIVADO")
    print(f"🎯 ESTRATEGIA: 4 Saturación + 2 Giro + 1 Distancia")
    print(f"💰 Saldo inicial: ${saldo_sim:.2f}")

    while True:
        try:
            # 1. MONITOREO DE LA OPERACIÓN ABIERTA
            if len(ops_sim) > 0:
                o = ops_sim[0]
                ticker = c.get_symbol_ticker(symbol=o['s'])
                p_a = float(ticker['price'])
                
                # Cálculo de ROI NETO simulado
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - comision_roi
                
                # Análisis de velas para salida (Confirmación de giro)
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                color_u = "VERDE" if float(k[-2][4]) > float(k[-2][1]) else "ROJA"

                cierre = False
                if roi_neto >= 1.5: # Objetivo de 1.5% neto
                    if (o['l'] == "LONG" and color_u == "ROJA") or (o['l'] == "SHORT" and color_u == "VERDE"):
                        cierre, motivo = True, "✅ SIM_PROFIT"
                elif roi_neto <= -2.5:
                    cierre, motivo = True, "❌ SIM_STOP_LOSS"

                if cierre:
                    saldo_sim += (o['monto'] * roi_neto / 100)
                    print(f"\n{motivo} en {o['s']} | Neto: {roi_neto:.2f}% | Nuevo Saldo: ${saldo_sim:.2f}")
                    ops_sim.pop()

            # 2. BÚSQUEDA DE ENTRADA (Lógica 4-2-1)
            else:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=15)
                    
                    # A. SATURACIÓN (4 velas)
                    v_sat = k[-8:-4]
                    s_r = all(float(v[4]) < float(v[1]) for v in v_sat) # 4 Rojas
                    s_v = all(float(v[4]) > float(v[1]) for v in v_sat) # 4 Verdes
                    
                    # B. GIRO (2 velas)
                    v_giro = k[-4:-2]
                    g_v = all(float(v[4]) > float(v[1]) for v in v_giro) # 2 Verdes
                    g_r = all(float(v[4]) < float(v[1]) for v in v_giro) # 2 Rojas
                    
                    # C. DISTANCIA (Tu vela de confirmación)
                    v_dist = k[-2]
                    c_dist = "VERDE" if float(v_dist[4]) > float(v_dist[1]) else "ROJA"

                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                    lado = ""
                    if s_r and g_v and c_dist == "VERDE": lado = "LONG"
                    if s_v and g_r and c_dist == "ROJA": lado = "SHORT"

                    if lado:
                        ops_sim.append({'s':m, 'l':lado, 'p':p_act, 'monto': saldo_sim})
                        print(f"\n🚀 SIM_ENTRADA EN {m} ({lado}) | Patrón 4-2-1 detectado")
                        break

            # 3. STATUS EN CONSOLA
            if len(ops_sim) == 0:
                print(f"📊 SIMULANDO: ${saldo_sim:.2f} | Buscando 4-2-1 en SHIB/PEPE...      ", end='\r')
            else:
                print(f"⏳ EN POSICIÓN: {ops_sim[0]['s']} | ROI NETO: {roi_neto:.2f}%      ", end='\r')

        except Exception as e:
            time.sleep(2)
        time.sleep(1)

if __name__ == "__main__": bot()
