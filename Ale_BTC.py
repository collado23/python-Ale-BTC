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
    
    # 🔗 CONEXIÓN
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    
    # ⚙️ VARIABLES (Directo de tus variables de Railway)
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    p_inv = float(os.getenv("PORCENTAJE_INVERSION", 0.80))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    u_p = 0
    print("🐊 MOTOR V151 | ARRANCANDO LABURO")

    while True:
        try:
            ahora = time.time()

            # 🔄 1. RECUPERADOR (PESCA LO QUE ESTÉ ABIERTO)
            if len(ops) == 0:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        ops.append({
                            's': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT", 
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': 5, 'be': False, 'piso': sl_val
                        })
                        print(f"✅ ENGANCHADO: {p['symbol']}")

            # 📊 2. GESTIÓN CON EL ESCALADOR LARGO
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.9
                
                # SALTO A 15X
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 1.0; print("🚀 POTENCIA 15X")

                # ESCALADOR LARGO
                if o['be']:
                    n_p = o['piso']
                    if roi >= 30.0: n_p = 28.5
                    elif roi >= 20.0: n_p = 18.5
                    elif roi >= 10.0: n_p = 8.5
                    elif roi >= 5.0: n_p = 4.0
                    elif roi >= 2.0: n_p = 1.5
                    if n_p > o['piso']: o['piso'] = n_p

                # CIERRE
                check = o['piso'] if o['be'] else sl_val
                if roi < check:
                    side = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    ops.remove(o); print(f"💰 CIERRE: {roi:.2f}%")

            # 🎯 3. BUSCADOR (Si no hay nada enganchado)
            if len(ops) == 0:
                for m in lista_m:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    if (cl[-2] > float(k[-2][1])): # Lógica simple para que arranque
                        tipo = 'LONG'
                        bal = c.futures_account_balance()
                        inv = float(next(b for b in bal if b['asset'] == 'USDC')['balance']) * p_inv
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round((inv * 5) / p_act, 1)
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"🎯 NUEVA: {m}")
                            break

            # MONITOR
            if ahora - u_p > 10:
                bal = c.futures_account_balance()
                saldo = float(next(b for b in bal if b['asset'] == 'USDC')['balance'])
                res = f"{ops[0]['s']}: {roi:.2f}%" if len(ops) > 0 else "🔎 BUSCANDO..."
                print(f"💰 Cap: ${saldo:.2f} | {res}")
                u_p = ahora

        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
