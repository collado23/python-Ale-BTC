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
    
    # ⚙️ VARIABLES
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    ops = []
    ultimo_print = 0

    print("🐊 MOTOR V146.9 | BUSCANDO OPERACIONES HUÉRFANAS...")

    while True:
        ahora = time.time()
        try:
            # --- 🔄 SINCRONIZADOR DE EMERGENCIA ---
            if len(ops) == 0:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p['positionAmt'])
                    if amt != 0 and p['symbol'] in lista_m:
                        ops.append({
                            's': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT",
                            'p': float(p['entryPrice']), 'q': abs(amt), 'x': int(p['leverage']), 
                            'be': False, 'piso': sl_val
                        })
                        print(f"\n✅ RECONECTADO CON: {p['symbol']}")

            # --- 📊 GESTIÓN DE SOL ---
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                
                # Salto a 15x si va bien
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 1.0; print(f"\n🚀 SALTO 15x en {o['s']}")

                # Stop Loss o Cierre en Piso
                piso_actual = o['piso'] if o['be'] else sl_val
                if roi < piso_actual:
                    side_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    ops.remove(o); print(f"\n⚠️ CIERRE PROTECTOR EN {o['s']}")

            if ahora - ultimo_print > 15:
                status = f"{ops[0]['s']}: {roi:.2f}%" if len(ops) > 0 else "Buscando..."
                print(f"💰 Cap: ${float(c.futures_account_balance()[0]['balance']):.2f} | {status}")
                ultimo_print = ahora

        except Exception as e:
            time.sleep(2)
        time.sleep(1)

if __name__ == "__main__": bot()
