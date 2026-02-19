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
    
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0
    bloqueo_activo = False 

    def tiene_posicion_abierta():
        try:
            pos = c.futures_position_information()
            for p in pos:
                if float(p['positionAmt']) != 0: return True
            return False
        except: return True

    def obtener_saldo_futuros():
        try:
            balances = c.futures_account_balance()
            for b in balances:
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except: return -1.0

    print(f"🐊 MOTOR V146.3 | INSTALACIÓN LIMPIA | MARGEN 85%")

    while True:
        ahora = time.time()
        roi_vis, gan_vis, piso_vis = 0.0, 0.0, -2.5
        
        try:
            if bloqueo_activo and (ahora - tiempo_descanso) > 15:
                bloqueo_activo = False
                print("\n🔓 CERROJO LIBERADO: Buscador listo.")

            saldo_api = obtener_saldo_futuros()
            saldo_actual = saldo_api if saldo_api > 0 else 10.0

            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_a) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                roi_vis, gan_vis, piso_vis = roi, o['inv'] * (roi / 100), o['piso']
                
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 1.0 
                    print(f"\n🚀 ¡SALTO 15X! {o['s']} | ROI: {roi:.2f}%")

                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0: n_p = 24.5
                    elif roi >= 20.0: n_p = 19.5
                    elif roi >= 15.0: n_p = 14.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 8.0:  n_p = 7.5
                    elif roi >= 6.0:  n_p = 5.5
                    elif roi >= 4.0:  n_p = 3.5
                    elif roi >= 2.5:  n_p = 2.0
                    elif roi >= 2.0:  n_p = 1.5
                    if n_p > o['piso']: o['piso'] = n_p

                    if roi < o['piso']:
                        side_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                        c.futures_create_order(symbol=o['s'], side=side_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                        ultima_moneda = o['s']; tiempo_descanso = ahora; ops.remove(o); bloqueo_activo = True
                        continue

                if not o['be'] and roi <= -2.5:
                    side_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    ultima_moneda = o['s']; tiempo_descanso = ahora; ops.remove(o); bloqueo_activo = True

            if not bloqueo_activo and len(ops) == 0:
                if not tiene_posicion_abierta():
                    for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                        if m == ultima_moneda: continue 
                        k = c.futures_klines(symbol=m, interval='1m', limit=30)
                        cl = [float(x[4]) for x in k]; v, o_v = cl[-2], float(k[-2][1])
                        e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27

                        if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                            tipo = 'LONG' if v > o_v else 'SHORT'
                            try:
                                inversion = obtener_saldo_futuros() * 0.85 
                                c.futures_change_leverage(symbol=m, leverage=5)
                                time.sleep(1.5)
                                p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                                cant = round((inversion * 5) / p_act, 1) 
                                if cant > 0:
                                    c.futures_create_order(symbol=m, side=(SIDE_BUY if tipo == 'LONG' else SIDE_SELL), type=ORDER_TYPE_MARKET, quantity=cant)
                                    ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'inv':inversion,'x':5,'be':False, 'piso': -2.5})
                                    break
                            except: break
            
            # MONITOR
            if len(ops) > 0: mon = f" | {ops[0]['s']}: {roi_vis:.2f}%"
            else: mon = f" | 🔒 CERROJO: {max(0, int(15-(ahora-tiempo_descanso)))}s" if bloqueo_activo else " | 🔎 BUSCANDO..."
            print(f"💰 Cap: ${saldo_actual:.2f}{mon}", end='\r')
        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__": bot()
