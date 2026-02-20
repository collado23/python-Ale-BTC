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
    p_inv = float(os.getenv("PORCENTAJE_INVERSION", 0.80))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    bloqueadas = {} 
    u_p = 0
    print("🐊 MOTOR V152.3 | FLUIDEZ TOTAL ACTIVADA")

    while True:
        try:
            ahora = time.time()
            
            # 🔄 1. RECUPERADOR (Siempre activo)
            if len(ops) == 0:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        ops.append({'s': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT", 'p': float(p['entryPrice']), 'q': abs(amt), 'x': int(p['leverage']), 'be': False, 'piso': sl_val})
                        print(f"✅ ENGANCHADO: {p['symbol']}")

            # 📊 2. GESTIÓN + SALTO 15X + ESCALADOR
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.8
                
                if roi >= 1.5 and not o['be']: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 1.0
                        print(f"🚀 SALTO 15X REALIZADO EN {o['s']}")
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
                    c.futures_create_order(symbol=o['s'], side=(SIDE_SELL if o['l']=="LONG" else SIDE_BUY), type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"💰 CIERRE: {o['s']} | ROI {roi:.2f}%")
                    bloqueadas[o['s']] = ahora + 120
                    ops.remove(o)

            # 🎯 3. BUSCADOR (SIN TRABAS)
            if len(ops) == 0:
                for m in lista_m:
                    if m in bloqueadas and ahora < bloqueadas[m]: continue
                    
                    try:
                        k = c.futures_klines(symbol=m, interval='1m', limit=30)
                        cl = [float(x[4]) for x in k]
                        v, o_v = cl[-2], float(k[-2][1])
                        e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                        
                        if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                            tipo = 'LONG' if v > o_v else 'SHORT'
                            bal = c.futures_account_balance()
                            saldo_f = float(next(b for b in bal if b['asset'] == 'USDC')['balance'])
                            inv = saldo_f * p_inv
                            c.futures_change_leverage(symbol=m, leverage=5)
                            p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                            cant = round((inv * 5) / p_act, 1)
                            if cant > 0:
                                c.futures_create_order(symbol=m, side=(SIDE_BUY if tipo=='LONG' else SIDE_SELL), type=ORDER_TYPE_MARKET, quantity=cant)
                                print(f"🎯 ENTRADA NUEVA: {m}")
                                break
                    except: continue # Si una moneda falla, que siga con la otra

            # MONITOR (A PRUEBA DE ERRORES)
            if ahora - u_p > 15:
                try:
                    res = f"{ops[0]['s']}: {roi:.2f}%" if len(ops) > 0 else "🔎 BUSCANDO..."
                    print(f"📊 Estado: {res}")
                except: pass
                u_p = ahora

        except Exception as e:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
