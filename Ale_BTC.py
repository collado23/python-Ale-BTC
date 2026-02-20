import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 SERVIDOR DE SALUD ULTRARRÁPIDO ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_health_server():
    try:
        port = int(os.getenv("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), HealthCheck)
        server.serve_forever()
    except: pass

def bot():
    # 1. Arrancamos el servidor de salud ANTES que cualquier cosa
    threading.Thread(target=start_health_server, daemon=True).start()
    
    # 2. Conexión con Binance
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    # 3. Parámetros
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    bloqueadas = {} 
    u_p = 0
    print("🐊 MOTOR V154 | BLINDADO Y ESCANEANDO")

    while True:
        try:
            ahora = time.time()
            
            # 🔄 RECUPERADOR (BUSCA TU OPERACIÓN ABIERTA)
            if len(ops) == 0:
                posiciones = c.futures_position_information()
                for p in posiciones:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        ops.append({
                            's': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT", 
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': int(p['leverage']), 'be': False, 'piso': sl_val
                        })
                        print(f"✅ ENGANCHADO: {p['symbol']}")

            # 📊 GESTIÓN DE RIESGO + SALTO 15X REAL + ESCALADOR
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                
                # Salto de palanca en Binance
                if roi >= 1.5 and not o['be']: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 1.0
                        print(f"🚀 SALTO 15X REAL EN BINANCE")
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

                # Cierre Protector
                check = o['piso'] if o['be'] else sl_val
                if roi < check:
                    side = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"💰 CIERRE: {roi:.2f}%")
                    bloqueadas[o['s']] = ahora + 120 # Enfriamiento 2 min
                    ops.remove(o)

            # MONITOR DE LOGS
            if ahora - u_p > 15:
                status = f"{ops[0]['s']}: {roi:.2f}%" if len(ops) > 0 else "🔎 BUSCANDO..."
                print(f"📊 {status}")
                u_p = ahora

        except Exception as e:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot()
