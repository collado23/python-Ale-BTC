import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 1. EL "SEGURO" PARA QUE RAILWAY NO SE FRENE ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200); self.end_headers()
        self.wfile.write(b"V143-ALIVE") 

def run_health_server():
    # Railway usa la variable PORT para monitorear el bot
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- 🚀 2. MOTOR V143 REFORZADO ---
def bot():
    # Iniciamos el servidor de salud en un hilo aparte
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # Conexión a Binance mediante Variables de Railway
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
    print(f"🎯 V143 CONECTADO | SALDO: ${cap:.2f}")

    while True:
        t_l = time.time()
        try:
            # 🔄 RECUPERADOR (Evita el error de margen detectando tu XRP)
            if not ops:
                posiciones = c.futures_position_information()
                for p in posiciones:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        simbolo = p['symbol']
                        ops.append({
                            's': simbolo, 'l': 'LONG' if amt > 0 else 'SHORT',
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': int(p['leverage']), 'be': True if int(p['leverage']) >= 15 else False, 
                            'piso': 2.0 if int(p['leverage']) >= 15 else -2.5
                        })
                        print(f"\n🔗 OPERACIÓN RECUPERADA: {simbolo}")
                        break

            # 1. GESTIÓN DE RIESGO
            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_n = (diff * 100 * o['x']) - 0.9 
                
                # Salto a 15x en 2.5%
                if roi_n >= 2.5 and o['x'] < 15: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 2.0
                        print(f"\n🔥 SALTO A 15X")
                    except: o['be'] = True

                if o['be']:
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']: o['piso'] = nuevo_piso

                check_cierre = o['piso'] if o['be'] else -2.5
                if roi_n >= 3.5 or roi_n <= check_cierre:
                    side_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"\n✅ CIERRE EN {roi_n:.2f}%")
                    time.sleep(2)
                    cap = obtener_saldo_real()
                    ops.remove(o)

            # 2. ENTRADA (SOLO SI NO HAY NADA ABIERTO)
            if not ops:
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, op_v = float(k[-2][4]), float(k[-2][1]) 
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27
                    
                    if (cl > op_v and cl > e9 and e9 > e27) or (cl < op_v and cl < e9 and e9 < e27):
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((cap * 0.95) * 5) / p_act, 1 if 'XRP' not in m else 0)
                        if cant > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side=SIDE_BUY if cl > op_v else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                            ops.append({'s':m,'l':'LONG' if cl > op_v else 'SHORT','p':p_act,'q':cant,'x':5,'be':False, 'piso': -2.5})
                            break

            print(f"💰 ${cap:.2f} | {time.strftime('%H:%M:%S')}   ", end='\r')
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)
        
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": 
    bot()
