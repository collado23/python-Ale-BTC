import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer  
from binance.client import Client
from binance.enums import *

# --- SERVER DE SALUD ---
class H(BaseHTTPRequestHandler): 
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    p_inv = float(os.getenv("PORCENTAJE_INVERSION", 0.80))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    op = None
    bloqueada_hasta = 0
    u_p = 0
    
    print("🐊 MOTOR V146.2 | COMISIÓN CORREGIDA | 15X REAL")

    while True:
        try:
            ahora = time.time()

            # 1. RECUPERADOR
            if op is None:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        lev = int(p.get('leverage', 5))
                        op = {
                            's': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT", 
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': lev, 'be': False, 'piso': sl_val
                        }
                        print(f"✅ ENGANCHADO A {p['symbol']}")
                        break

            # 2. GESTIÓN (SIN EL DESCUENTO AGRESIVO DE 0.9)
            if op:
                p_act = float(c.futures_symbol_ticker(symbol=op['s'])['price'])
                diff = (p_act - op['p']) / op['p'] if op['l'] == "LONG" else (op['p'] - p_act) / op['p']
                
                # ROI real (solo descontamos un mínimo de 0.1 por el spread)
                roi = (diff * 100 * op['x']) - 0.10
                
                # SALTO REAL A 15X
                if roi >= 1.5 and not op['be']:
                    try:
                        c.futures_change_leverage(symbol=op['s'], leverage=15)
                        op['x'], op['be'], op['piso'] = 15, True, 0.5 # Piso inicial en 0.5%
                        print(f"🚀 SALTO 15X REALIZADO EN {op['s']}")
                    except: op['be'] = True

                # ESCALADOR LARGO (AJUSTADO)
                if op['be']:
                    n_p = op['piso']
                    if roi >= 30.0: n_p = 28.5
                    elif roi >= 20.0: n_p = 18.5
                    elif roi >= 10.0: n_p = 8.5
                    elif roi >= 5.0: n_p = 4.0
                    elif roi >= 2.0: n_p = 1.0
                    if n_p > op['piso']: op['piso'] = n_p

                # CIERRE
                check = op['piso'] if op['be'] else sl_val
                if roi < check:
                    side = SIDE_SELL if op['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=op['s'], side=side, type=ORDER_TYPE_MARKET, quantity=op['q'])
                    print(f"💰 CIERRE: {roi:.2f}%")
                    bloqueada_hasta = ahora + 60 # Descansa 1 minuto
                    op = None

            # 3. BUSCADOR
            elif ahora > bloqueada_hasta:
                for m in lista_m:
                    k = c.futures_klines(symbol=m, interval='1m', limit=5)
                    if float(k[-1][4]) > float(k[-1][1]): 
                        bal = c.futures_account_balance()
                        saldo = float(next(b for b in bal if b['asset'] == 'USDC')['balance'])
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((saldo * p_inv) * 5) / p_act, 1)
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"🎯 ENTRADA NUEVA: {m}")
                            break

            if ahora - u_p > 10:
                print("🔎..." if op is None else f"📊 {op['s']}: {roi:.2f}% (Piso: {op['piso']}%)")
                u_p = ahora

        except Exception as e:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot()
