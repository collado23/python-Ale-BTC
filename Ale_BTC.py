import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 1. SERVER DE SALUD (PARA QUE RAILWAY NO LO FRENE) ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot V143 Online") 

def s_h():
    # Railway asigna un puerto dinámico, hay que leerlo sí o sí
    puerto = int(os.getenv("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", puerto), H)
        print(f"✅ Servidor de salud escuchando en el puerto {puerto}")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Error en server de salud: {e}")

# --- 🚀 2. MOTOR V143 ---
def bot():
    # Lanzamos el server de salud en segundo plano
    threading.Thread(target=s_h, daemon=True).start()
    
    # --- 🔑 VARIABLES DE ENTORNO ---
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    
    def obtener_saldo_real():
        try:
            res = c.futures_account_balance()
            for b in res:
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except: return 0.0

    cap = obtener_saldo_real()
    print(f"🎯 V143 ACTIVADO | SALDO: ${cap:.2f} | STOP -2.5 | SALTO 2.0")

    while True:
        t_l = time.time()
        try:
            # 🔄 RECUPERADOR DE POSICIONES REALES
            if not ops:
                posiciones = c.futures_position_information()
                for p in posiciones:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        simbolo = p['symbol']
                        lado = 'LONG' if amt > 0 else 'SHORT'
                        precio_entrada = float(p['entryPrice'])
                        palanca = int(p['leverage'])
                        ops.append({
                            's': simbolo, 'l': lado, 'p': precio_entrada, 
                            'q': abs(amt), 'x': palanca, 
                            'be': True if palanca >= 15 else False, 
                            'piso': 1.5 if palanca >= 15 else -2.5
                        })
                        print(f"\n🔗 REENGANCHADO EN: {simbolo}")
                        break

            # 1. GESTIÓN DE RIESGO Y ESCALADOR
            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_n = (diff * 100 * o['x']) - 0.9 
                
                # 🔥 SALTO A 15X (A los 2.0% NETO)
                if roi_n >= 2.0 and o['x'] < 15: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 1.5
                        print(f"\n🔥 SALTO 15X EN {o['s']}")
                    except: o['be'] = True

                # 🪜 ESCALADOR +0.5
                if o['be']:
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']: o['piso'] = nuevo_piso

                # 📉 CIERRE (Stop -2.5% o Piso)
                check_cierre = o['piso'] if o['be'] else -2.5
                if roi_n >= 3.5 or roi_n <= check_cierre:
                    side_cierre = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    try:
                        c.futures_create_order(symbol=o['s'], side=side_cierre, type=ORDER_TYPE_MARKET, quantity=o['q'])
                        print(f"\n✅ CIERRE EN {o['s']} | ROI: {roi_n:.2f}%")
                    except: pass
                    
                    time.sleep(2)
                    cap = obtener_saldo_real()
                    ops.remove(o)

            # 2. ENTRADA (SOL, XRP, BNB, )
            if not ops:
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC', ]:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, op_v = float(k[-2][4]), float(k[-2][1]) 
                    k_full = [float(x[4]) for x in k]
                    e9, e27 = sum(k_full[-9:])/9, sum(k_full[-27:])/27
                    
                    if (cl > op_v and cl > e9 and e9 > e27) or (cl < op_v and cl < e9 and e9 < e27):
                        tipo = 'LONG' if cl > op_v else 'SHORT'
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((cap * 0.90) * 5) / p_act, 1)
                        if cant > 0:
                            try:
                                c.futures_change_leverage(symbol=m, leverage=5)
                                c.futures_create_order(symbol=m, side=SIDE_BUY if tipo=='LONG' else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                                ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'x':5,'be':False, 'piso': -2.5})
                                break
                            except: pass

            status = f"ROI: {roi_n:.2f}%" if ops else "Acechando..."
            print(f"💰 ${cap:.2f} | {status} | {time.strftime('%H:%M:%S')}   ", end='\r')
            
        except Exception as e:
            print(f"⚠️ Error en bucle: {e}")
            time.sleep(10) # Espera un poco si hay error de red
        
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": 
    bot()
