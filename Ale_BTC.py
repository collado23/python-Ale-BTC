import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # 🔗 VINCULACIÓN CON TUS VARIABLES
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    u_p = 0
    print("🐊 MOTOR V150.9 | MODO RADAR ACTIVADO")

    while True:
        try:
            ahora = time.time()
            
            # 🔄 RADAR DE POSICIONES (ESCANEO TOTAL)
            if len(ops) == 0:
                # Forzamos la actualización de cuenta
                acc = c.futures_account()
                posiciones = acc['positions']
                for p in posiciones:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        symbol = p['symbol']
                        ops.append({
                            's': symbol, 
                            'l': "LONG" if amt > 0 else "SHORT", 
                            'p': float(p['entryPrice']), 
                            'q': abs(amt), 
                            'x': int(p['leverage']), 
                            'be': False, 
                            'piso': sl_val
                        })
                        print(f"🎯 RADAR: Posición enganchada en {symbol}")

            # 📊 GESTIÓN CON EL ESCALADOR QUE QUERÉS
            for o in ops[:]:
                ticker = c.futures_symbol_ticker(symbol=o['s'])
                p_act = float(ticker['price'])
                
                # ROI real con apalancamiento
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.8 # Descuento de comisión
                
                # Lógica 15x
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 0.8
                    print(f"🚀 SALTO 15X EN {o['s']}")

                # 🛡️ TU ESCALADOR LARGO (CORREGIDO)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 30.0: n_p = 28.5
                    elif roi >= 20.0: n_p = 18.5
                    elif roi >= 10.0: n_p = 8.5
                    elif roi >= 5.0: n_p = 4.0
                    elif roi >= 2.5: n_p = 1.8
                    if n_p > o['piso']: o['piso'] = n_p

                # Cierre por Stop o Piso
                umbral = o['piso'] if o['be'] else sl_val
                if roi < umbral:
                    side = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    ops.remove(o)
                    print(f"💰 CIERRE: {o['s']} | ROI: {roi:.2f}%")

            # 💰 MONITOR DE SALDO (USDC / USDT)
            if ahora - u_p > 10:
                bal = c.futures_account_balance()
                saldo = sum(float(b['balance']) for b in bal if b['asset'] in ['USDC', 'USDT'])
                msg = f"{ops[0]['s']}: {roi:.2f}%" if len(ops) > 0 else "🔎 ESCANEANDO..."
                print(f"💰 Saldo: ${saldo:.2f} | {msg}")
                u_p = ahora

        except Exception as e:
            time.sleep(4)
        time.sleep(1)

if __name__ == "__main__":
    bot()
