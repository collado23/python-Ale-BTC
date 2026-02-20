import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer  
from binance.client import Client
from binance.enums import *

# --- 🌐 SERVIDOR MÍNIMO PARA RAILWAY ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s, daemon=True).start()
    
    # 🔗 CONEXIÓN
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    bloqueadas = {}
    u_p = 0
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    print("🐊 MOTOR V155 | RECONECTANDO CON TU OPERACIÓN...")

    while True:
        try:
            ahora = time.time()
            
            # 🔄 RECUPERADOR FORZADO (SI NO VE LA POSICIÓN, REINTENTA)
            if not ops:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        ops.append({
                            's': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT", 
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': int(p['leverage']), 'be': False, 'piso': sl_val
                        })
                        print(f"✅ ¡LA ENCONTRÉ! Operación activa en {p['symbol']}")

            # 📊 GESTIÓN Y ESCALADOR
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                
                # Salto Real en Binance
                if roi >= 1.5 and not o['be']: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 1.0
                        print(f"🚀 SALTO 15X OK")
                    except: o['be'] = True

                # Tu Escalador Largo
                if o['be']:
                    n_p = o['piso']
                    if roi >= 30.0: n_p = 28.5
                    elif roi >= 20.0: n_p = 18.5
                    elif roi >= 10.0: n_p = 8.5
                    elif roi >= 5.0: n_p = 4.0
                    elif roi >= 2.0: n_p = 1.5
                    if n_p > o['piso']: o['piso'] = n_p

                # Cierre
                if roi < (o['piso'] if o['be'] else sl_val):
                    c.futures_create_order(symbol=o['s'], side=(SIDE_SELL if o['l']=="LONG" else SIDE_BUY), type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"💰 CIERRE: {roi:.2f}%")
                    bloqueadas[o['s']] = ahora + 120
                    ops.remove(o)

            # MONITOR (PARA QUE NO SE QUEDE MUDO)
            if ahora - u_p > 10:
                if ops:
                    print(f"📊 {ops[0]['s']}: {roi:.2f}% | Piso: {ops[0]['piso']}%")
                else:
                    print("🔎 ESCANEANDO BINANCE...")
                u_p = ahora

        except Exception as e:
            # Si hay error de conexión de Binance, el bot no se muere, espera 2 segundos y sigue
            time.sleep(2)
            continue
        
        time.sleep(1)

if __name__ == "__main__":
    bot()
