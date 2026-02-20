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
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    u_p = 0
    print("🐊 MOTOR V150.8 | FORZANDO RECONOCIMIENTO...")

    while True:
        try:
            ahora = time.time()
            
            # 🔄 RECUPERADOR AGRESIVO (SIN FILTROS DE NOMBRE)
            if len(ops) == 0:
                posiciones = c.futures_position_information()
                for p in posiciones:
                    amt = float(p['positionAmt'])
                    if amt != 0: # Si hay CUALQUIER MONEDA abierta
                        # Metemos la operación a la fuerza en el sistema
                        ops.append({
                            's': p['symbol'], 
                            'l': "LONG" if amt > 0 else "SHORT", 
                            'p': float(p['entryPrice']), 
                            'q': abs(amt), 
                            'x': int(p['leverage']), 
                            'be': False, 
                            'piso': sl_val
                        })
                        print(f"✅ POSICIÓN DETECTADA A LA FUERZA: {p['symbol']}")

            # 📊 GESTIÓN CON EL ESCALADOR LARGO QUE PEDISTE
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.90 # Ajuste de comisión
                
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 1.0; print(f"🚀 SALTO 15X EN {o['s']}")

                if o['be']:
                    n_p = o['piso']
                    if roi >= 30.0: n_p = 29.0
                    elif roi >= 20.0: n_p = 18.5
                    elif roi >= 10.0: n_p = 8.5
                    elif roi >= 5.0: n_p = 4.0
                    elif roi >= 2.0: n_p = 1.2
                    if n_p > o['piso']: o['piso'] = n_p

                if roi < (o['piso'] if o['be'] else sl_val):
                    side = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    ops.remove(o); print(f"💰 CIERRE EJECUTADO: {roi:.2f}%")

            if ahora - u_p > 10:
                try:
                    bal = c.futures_account_balance()
                    # Buscamos saldo en USDC o USDT, el que tenga guita
                    saldo = sum(float(b['balance']) for b in bal if b['asset'] in ['USDC', 'USDT'])
                    msg = f"{ops[0]['s']}: {roi:.2f}%" if len(ops) > 0 else "🔎 BUSCANDO EN BINANCE..."
                    print(f"💰 Saldo Total: ${saldo:.2f} | {msg}")
                except: pass
                u_p = ahora

        except Exception as e:
            # Si hay error de conexión, no lo matamos, que espere
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
