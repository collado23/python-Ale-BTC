import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer  
from binance.client import Client
from binance.enums import *

# --- 🌐 SERVIDOR PARA QUE RAILWAY NO LO FRENE ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200); self.end_headers()
        self.wfile.write(b"BOT-OK") 

def start_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheck)
    server.serve_forever()

# --- 🚀 MOTOR V143 REFORZADO ---
def bot():
    threading.Thread(target=start_health_server, daemon=True).start()
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    
    def get_saldo():
        try:
            for b in c.futures_account_balance():
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except: return 0.0

    cap = get_saldo()
    print(f"🎯 V143 CONECTADO | SALDO: ${cap:.2f}")

    while True:
        try:
            # 🔄 RECUPERADOR (Sin errores de 'leverage')
            if not ops:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p.get('positionAmt', 0))
                    if amt != 0:
                        symbol = p['symbol']
                        lev = int(p.get('leverage', 5))
                        ops.append({
                            's': symbol, 'l': 'LONG' if amt > 0 else 'SHORT',
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': lev, 'be': True if lev >= 15 else False, 
                            'piso': 2.0 if lev >= 15 else -2.5
                        })
                        print(f"🔗 RECUPERADO: {symbol}")
                        break

            # 1. GESTIÓN
            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_n = (diff * 100 * o['x']) - 0.9 
                
                # Salto a 15x en 2.5%
                if roi_n >= 2.5 and o['x'] < 15: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 2.0
                        print(f"🔥 SALTO 15X")
                    except: o['be'] = True

                if o['be']:
                    if (roi_n - 0.5) > o['piso']: o['piso'] = roi_n - 0.5

                check_cierre = o['piso'] if o['be'] else -2.5
                if roi_n >= 3.5 or roi_n <= check_cierre:
                    c.futures_create_order(symbol=o['s'], side=SIDE_SELL if o['l'] == "LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"✅ CIERRE: {roi_n:.2f}%")
                    time.sleep(5)
                    cap = get_saldo()
                    ops.remove(o)

            # 2. ENTRADA
            if not ops:
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, op_v = float(k[-2][4]), float(k[-2][1]) 
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27
                    
                    if (cl > op_v and cl > e9 and e9 > e27) or (cl < op_v and cl < e9 and e9 < e27):
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        # Usamos el 100% para que no falle por monto mínimo
                        cant = round((cap * 5) / p_act, 1 if 'XRP' not in m else 0)
                        if cant > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side=SIDE_BUY if cl > op_v else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                            ops.append({'s':m,'l':'LONG' if cl > op_v else 'SHORT','p':p_act,'q':cant,'x':5,'be':False, 'piso': -2.5})
                            break

        except Exception as e:
            print(f"Aviso: {e}")
            time.sleep(10)
        
        time.sleep(10)

if __name__ == "__main__": 
    bot()
