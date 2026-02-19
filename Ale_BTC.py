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
    
    # 🔗 VARIABLES DESDE RAILWAY
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    u_p = 0
    print("🐊 MOTOR V150.5 | ESCALADOR COMPLETO ACTIVO")

    while True:
        try:
            ahora = time.time()
            
            # 🔄 RECUPERADOR (BUSCA TU SOL)
            if len(ops) == 0:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p['positionAmt'])
                    if amt != 0 and p['symbol'] in lista_m:
                        ops.append({
                            's': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT", 
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': int(p['leverage']), 'be': False, 'piso': sl_val
                        })
                        print(f"✅ RECUPERADO: {p['symbol']} a {p['leverage']}x")

            # 📊 GESTIÓN CON ESCALADOR LARGO
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                
                # 🔥 EL SALTO A 15X (MÁXIMA POTENCIA)
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 1.0 
                    print(f"🚀 SALTO 15X: {o['s']} | ROI: {roi:.2f}%")

                # 🛡️ ESCALADOR LARGO (ESTE ES EL QUE QUERÍAS)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 30.0:   n_p = 29.2  # Protege casi todo en saltos grandes
                    elif roi >= 25.0: n_p = 24.1
                    elif roi >= 20.0: n_p = 19.1
                    elif roi >= 15.0: n_p = 14.2
                    elif roi >= 10.0: n_p = 9.3
                    elif roi >= 8.0:  n_p = 7.4
                    elif roi >= 6.0:  n_p = 5.5
                    elif roi >= 4.0:  n_p = 3.6
                    elif roi >= 2.5:  n_p = 2.1
                    elif roi >= 2.0:  n_p = 1.6
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"📈 PISO ACTUALIZADO: {o['piso']}%")

                # ⚠️ CIERRE POR PISO O STOP LOSS
                piso_check = o['piso'] if o['be'] else sl_val
                if roi < piso_check:
                    side = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    ops.remove(o)
                    print(f"💰 CIERRE EN CAJA: {o['s']} | ROI FINAL: {roi:.2f}%")

            # 💰 MONITOR DE SALDO Y ESTADO
            if ahora - u_p > 15:
                try:
                    bal = c.futures_account_balance()
                    saldo = float(next(b for b in bal if b['asset'] == 'USDC')['balance'])
                    msg = f"{ops[0]['s']}: {roi:.2f}% (Piso: {ops[0]['piso']}%)" if len(ops) > 0 else "🔎 BUSCANDO..."
                    print(f"💰 Cap: ${saldo:.2f} | {msg}")
                except: pass
                u_p = ahora

        except Exception as e:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot()
