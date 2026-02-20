import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 EL SERVIDOR QUE MANTIENE VIVO A RAILWAY ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')  
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthServer)
    server.serve_forever()

def bot():
    # Lanzamos el servidor de salud en un hilo aparte para que Railway no nos mate
    threading.Thread(target=run_health_server, daemon=True).start()
    
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    p_inv = float(os.getenv("PORCENTAJE_INVERSION", 0.80))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    bloqueadas = {} 
    u_p = 0
    print("🐊 MOTOR V153 | ESTABILIDAD RECUPERADA")

    while True:
        try:
            ahora = time.time()
            
            # 🔄 1. RECUPERADOR (EL QUE TE ENGANCHÓ EL SOL RECIÉN)
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
                        print(f"✅ ENGANCHADO: {p['symbol']}")

            # 📊 2. GESTIÓN + SALTO REAL + ESCALADOR LARGO
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                
                if roi >= 1.5 and not o['be']: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 1.0
                        print(f"🚀 SALTO 15X REALIZADO")
                    except: o['be'] = True

                if o['be']:
                    n_p = o['piso']
                    if roi >= 30.0: n_p = 28.5
                    elif roi >= 20.0: n_p = 18.5
                    elif roi >= 10.0: n_p = 8.5
                    elif roi >= 5.0: n_p = 4.0
                    elif roi >= 2.0: n_p = 1.5
                    if n_p > o['piso']: o['piso'] = n_p

                if roi < (o['piso'] if o['be'] else sl_val):
                    side = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"💰 CIERRE EN CAJA: {roi:.2f}%")
                    bloqueadas[o['s']] = ahora + 120 # BLOQUEO 2 MINUTOS
                    ops.remove(o)

            # 🎯 3. BUSCADOR (EL QUE NO FALLA)
            if len(ops) == 0:
                for m in lista_m:
                    if m in bloqueadas and ahora < bloqueadas[m]: continue
                    
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    if (cl[-2] > float(k[-2][1])): # Lógica de vela simple
                        tipo = 'LONG'
                        bal = c.futures_account_balance()
                        saldo = float(next(b for b in bal if b['asset'] == 'USDC')['balance'])
                        inv = saldo * p_inv
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round((inv * 5) / p_act, 1)
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"🎯 ENTRADA NUEVA: {m}")
                            break

            # MONITOR DE LOGS (Mantiene activo el scroll)
            if ahora - u_p > 10:
                res = f"{ops[0]['s']}: {roi:.2f}%" if len(ops) > 0 else "🔎 BUSCANDO OPORTUNIDAD..."
                print(f"📊 {res}")
                u_p = ahora

        except Exception as e:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot()
