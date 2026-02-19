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
    
    # --- ⚙️ CARGA DE VARIABLES DESDE RAILWAY ---
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    # Lista de monedas (ej: SOLUSDC,XRPUSDC,BNBUSDC)
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    # Porcentaje de capital a usar (85% = 0.85)
    p_inv = float(os.getenv("PORCENTAJE_INVERSION", 0.85))
    # Tiempo de espera entre trades
    t_espera = int(os.getenv("TIEMPO_ESPERA", 15))
    # Stop Loss (ej: -2.5)
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    c = Client(api_key, api_secret)
    ops = []
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

    print(f"🐊 MOTOR V146.5 | CONTROL POR VARIABLES ACTIVO")

    while True:
        ahora = time.time()
        roi_vis = 0.0
        
        try:
            if bloqueo_activo and (ahora - tiempo_descanso) > t_espera:
                bloqueo_activo = False
                print(f"\n🔓 CERROJO LIBERADO: Buscando en {lista_m}...")

            saldo_api = obtener_saldo_futuros()
            saldo_actual = saldo_api if saldo_api > 0 else 10.0

            # --- GESTIÓN DE OPERACIÓN ---
            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_a) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                roi_vis = roi
                
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 1.0 
                    print(f"\n🚀 ¡SALTO 15X! {o['s']} | ROI: {roi:.2f}%")

                if o['be']:
                    # ESCALADOR
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
                        tiempo_descanso = ahora; ops.remove(o); bloqueo_activo = True
                        print(f"\n✅ CIERRE EN PISO: {o['s']} | ROI: {roi:.2f}%")
                        continue

                if not o['be'] and roi <= sl_val:
                    side_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    tiempo_descanso = ahora; ops.remove(o); bloqueo_activo = True
                    print(f"\n⚠️ STOP LOSS: {o['s']} | ROI: {roi:.2f}%")

            # --- 🎯 BUSCADOR ---
            if not bloqueo_activo and len(ops) == 0:
                if not tiene_posicion_abierta():
                    for m in lista_m:
                        k = c.futures_klines(symbol=m, interval='1m', limit=30)
                        cl = [float(x[4]) for x in k]; v, o_v = cl[-2], float(k[-2][1])
                        e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27

                        if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                            tipo = 'LONG' if v > o_v else 'SHORT'
                            try:
                                inversion = obtener_saldo_futuros() * p_inv 
                                c.futures_change_leverage(symbol=m, leverage=5)
                                time.sleep(1.5)
                                p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                                cant = round((inversion * 5) / p_act, 1) 
                                if cant > 0:
                                    c.futures_create_order(symbol=m, side=(SIDE_BUY if tipo == 'LONG' else SIDE_SELL), type=ORDER_TYPE_MARKET, quantity=cant)
                                    ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'inv':inversion,'x':5,'be':False, 'piso': sl_val})
                                    print(f"\n🎯 ENTRADA: {tipo} en {m}")
                                    break
                            except: break
            
            # MONITOR
            if len(ops) > 0: mon = f" | {ops[0]['s']}: {roi_vis:.2f}%"
            else: mon = f" | 🔒 ESPERA: {max(0, int(t_espera-(ahora-tiempo_descanso)))}s" if bloqueo_activo else " | 🔎 BUSCANDO..."
            print(f"💰 Cap: ${saldo_actual:.2f}{mon}", end='\r')
        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__": bot()
