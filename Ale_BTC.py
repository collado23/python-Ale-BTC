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
    
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    ops = []
    u_p = 0
    print("🐊 MOTOR V152 | SALTO REAL 15X ACTIVADO")

    while True:
        try:
            ahora = time.time()
            
            # 🔄 1. RECUPERADOR (BUSCA TU OPERACIÓN)
            if len(ops) == 0:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        ops.append({
                            's': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT", 
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': int(p['leverage']), 'be': False, 'piso': sl_val
                        })
                        print(f"✅ ENGANCHADO: {p['symbol']} a {p['leverage']}x")

            # 📊 2. GESTIÓN + SALTO REAL EN BINANCE
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.8
                
                # 🔥 EL SALTO REAL (CAMBIA EL CARTELITO EN BINANCE)
                if roi >= 1.5 and not o['be']: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15) # <-- ESTO LO CAMBIA EN BINANCE
                        o['x'] = 15
                        o['be'] = True
                        o['piso'] = 1.0
                        print(f"🚀 SALTO 15X REALIZADO EN BINANCE PARA {o['s']}")
                    except Exception as e:
                        print(f"⚠️ Error al cambiar palanca: {e}")
                        o['be'] = True # Lo marcamos igual para proteger

                # 🛡️ ESCALADOR LARGO (TU PREFERIDO)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 30.0:   n_p = 28.5
                    elif roi >= 20.0: n_p = 18.5
                    elif roi >= 10.0: n_p = 8.5
                    elif roi >= 5.0:  n_p = 4.0
                    elif roi >= 2.0:  n_p = 1.5
                    if n_p > o['piso']: o['piso'] = n_p

                # ⚠️ CIERRE POR PISO O STOP
                check = o['piso'] if o['be'] else sl_val
                if roi < check:
                    side = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    ops.remove(o)
                    print(f"💰 CIERRE: ROI {roi:.2f}%")

            # 🎯 3. MONITOR
            if ahora - u_p > 10:
                bal = c.futures_account_balance()
                saldo = float(next(b for b in bal if b['asset'] == 'USDC')['balance'])
                msg = f"{ops[0]['s']}: {roi:.2f}% (Piso: {ops[0]['piso']}%)" if len(ops) > 0 else "🔎 BUSCANDO..."
                print(f"💰 Cap: ${saldo:.2f} | {msg}")
                u_p = ahora

        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
