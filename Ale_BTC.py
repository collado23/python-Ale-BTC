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
    
    # ⚙️ VARIABLES DESDE RAILWAY
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    p_inv = float(os.getenv("PORCENTAJE_INVERSION", 0.80))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    u_p = 0
    print("🐊 MOTOR V150.2 | FULL EQUIPO | RECUPERADOR + ESCALADOR")

    while True:
        try:
            ahora = time.time()
            
            # 🔄 RECUPERADOR (PESCA A TU SOL ABIERTO)
            if len(ops) == 0:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p['positionAmt'])
                    if amt != 0 and p['symbol'] in lista_m:
                        ops.append({
                            's': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT", 
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': int(p['leverage']), 'be': False, 'piso': sl_val, 'inv': 8.0
                        })
                        print(f"✅ RECONECTADO: {p['symbol']} a {int(p['leverage'])}x")

            # 📊 GESTIÓN TOTAL
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                
                # 🔥 EL SALTO A 15X
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 1.0 
                    print(f"🚀 SALTO 15X EN {o['s']} | ROI: {roi:.2f}%")

                # 🛡️ ESCALADOR DE PISO (TRAILING STOP)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0:   n_p = 24.0
                    elif roi >= 15.0: n_p = 14.0
                    elif roi >= 10.0: n_p = 9.0
                    elif roi >= 5.0:  n_p = 4.0
                    elif roi >= 3.0:  n_p = 2.5
                    elif roi >= 2.0:  n_p = 1.5
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ PISO SUBIÓ A {o['piso']}% en {o['s']}")

                # ⚠️ CIERRE POR PISO O STOP LOSS
                piso_check = o['piso'] if o['be'] else sl_val
                if roi < piso_check:
                    side_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    ops.remove(o)
                    print(f"✅ CIERRE PROTECTOR: {o['s']} | ROI FINAL: {roi:.2f}%")
                    continue

            # 🎯 BUSCADOR (SI NO HAY NADA ABIERTO)
            if len(ops) == 0:
                for m in lista_m:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    v, o_v = cl[-2], float(k[-2][1])
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                        tipo = 'LONG' if v > o_v else 'SHORT'
                        inv = (float(c.futures_account_balance()[0]['balance'])) * p_inv
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round((inv * 5) / p_act, 1)
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=(SIDE_BUY if tipo=='LONG' else SIDE_SELL), type=ORDER_TYPE_MARKET, quantity=cant)
                            ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'inv':inv,'x':5,'be':False,'piso':sl_val})
                            print(f"🎯 ENTRADA NUEVA: {m} ({tipo})")
                            break

            # MONITOR
            if ahora - u_p > 15:
                res = f"{ops[0]['s']}: {roi:.2f}% | Piso: {ops[0]['piso']}%" if len(ops) > 0 else "🔎 BUSCANDO..."
                print(f"💰 Cap: ${float(c.futures_account_balance()[0]['balance']):.2f} | {res}")
                u_p = ahora
                
        except Exception as e:
            time.sleep(2)
        time.sleep(1)

if __name__ == "__main__": bot()
