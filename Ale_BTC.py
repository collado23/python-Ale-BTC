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
    ak = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_APY_KEY")
    as_ = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_APY_SECRET")
    c = Client(ak, as_)
    
    # CONFIGURACIÓN DE PLATA REAL
    monedas = ['SHIBUSDT', 'PEPEUSDT']
    ops = [] # Control de operación activa
    leverage = 15
    comision_roi = 1.2 # Lo que se lleva Binance a 15x

    print(f"🐊 ESTRATEGIA FRANCOTIRADOR 4-2-1 ACTIVADA")

    while True:
        try:
            # 1. ACTUALIZAR SALDO
            bal = c.futures_account_balance()
            cap = next((float(b['balance']) for b in bal if b['asset'] == 'USDT'), 0.0)

            # 2. GESTIÓN DE VENTA (SALIR CON PLATA)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - comision_roi
                
                # Análisis de velas para salida (Distancia)
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                color_u = "VERDE" if float(k[-2][4]) > float(k[-2][1]) else "ROJA"

                cierre = False
                if roi_neto >= 1.5: # Queremos 1.5% limpio
                    if (o['l'] == "LONG" and color_u == "ROJA") or (o['l'] == "SHORT" and color_u == "VERDE"):
                        cierre, motivo = True, "✅ PROFIT LOGRADO"
                elif roi_neto <= -2.5:
                    cierre, motivo = True, "❌ STOP LOSS"

                if cierre:
                    c.futures_create_order(symbol=o['s'], side=("SELL" if o['l']=="LONG" else "BUY"), type='MARKET', quantity=o['q'])
                    ops.remove(o)
                    print(f"{motivo} | ROI NETO: {roi_neto:.2f}%")
                    time.sleep(5)

            # 3. GESTIÓN DE COMPRA (ENTRAR CON ESTRATEGIA)
            if len(ops) < 1 and cap >= 10:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=15)
                    
                    # LÓGICA 4 (Saturación) - 2 (Giro) - 1 (Distancia)
                    v_sat = k[-8:-4]
                    s_r = all(float(v[4]) < float(v[1]) for v in v_sat) # 4 Rojas
                    s_v = all(float(v[4]) > float(v[1]) for v in v_sat) # 4 Verdes
                    
                    v_giro = k[-4:-2]
                    g_v = all(float(v[4]) > float(v[1]) for v in v_giro) # 2 Verdes
                    g_r = all(float(v[4]) < float(v[1]) for v in v_giro) # 2 Rojas
                    
                    v_dist = k[-2]
                    c_dist = "VERDE" if float(v_dist[4]) > float(v_dist[1]) else "ROJA"

                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                    lado = ""
                    if s_r and g_v and c_dist == "VERDE": lado = "LONG"
                    if s_v and g_r and c_dist == "ROJA": lado = "SHORT"

                    if lado:
                        qty = round((cap * 0.95 * leverage) / p_act, 0)
                        c.futures_change_leverage(symbol=m, leverage=leverage)
                        c.futures_create_order(symbol=m, side=('BUY' if lado=="LONG" else 'SELL'), type='MARKET', quantity=qty)
                        ops.append({'s':m, 'l':lado, 'p':p_act, 'q':qty})
                        print(f"🚀 DISPARO EN {m} ({lado})")
                        break

            print(f"💰 SALDO: ${cap:.2f} | Acechando SHIB/PEPE...      ", end='\r')

        except Exception as e:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
