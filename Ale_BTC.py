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
    t_espera = int(os.getenv("TIEMPO_ESPERA", 15))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    tiempo_descanso = 0
    bloqueo_activo = False 
    ultimo_print = 0

    def obtener_saldo_futuros():
        try:
            balances = c.futures_account_balance()
            for b in balances:
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except: return -1.0

    def tiene_posicion_abierta():
        try:
            pos = c.futures_position_information()
            for p in pos:
                if float(p['positionAmt']) != 0: return True
            return False
        except: return True

    def sincronizar_huerfanos():
        try:
            posiciones = c.futures_position_information()
            for p in posiciones:
                amt = float(p['positionAmt'])
                if amt != 0 and p['symbol'] in lista_m:
                    if any(o['s'] == p['symbol'] for o in ops): continue
                    tipo = "LONG" if amt > 0 else "SHORT"
                    ops.append({
                        's': p['symbol'], 'l': tipo, 'p': float(p['entryPrice']), 
                        'q': abs(amt), 'inv': 8.0, 'x': int(p['leverage']), 
                        'be': False, 'piso': sl_val
                    })
                    print(f"\n🔄 RECUPERADA: {p['symbol']} detectada.")
        except: pass

    print(f"🐊 MOTOR V146.8 | SIN ERRORES | RECUPERADOR ACTIVO")

    while True:
        ahora = time.time()
        try:
            if len(ops) == 0: sincronizar_huerfanos()
            if bloqueo_activo and (ahora - tiempo_descanso) > t_espera: bloqueo_activo = False

            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_a) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 1.0 
                    print(f"\n🚀 SALTO 15X: {o['s']}")

                if o['be']:
                    n_p = o['piso']
                    if roi >= 5.0: n_p = roi - 0.5
                    elif roi >= 2.0: n_p = 1.5
                    if n_p > o['piso']: o['piso'] = n_p
                    if roi < o['piso']:
                        c.futures_create_order(symbol=o['s'], side=(SIDE_SELL if o['l']=="LONG" else SIDE_BUY), type=ORDER_TYPE_MARKET, quantity=o['q'])
                        tiempo_descanso = ahora; ops.remove(o); bloqueo_activo = True; continue

                if not o['be'] and roi <= sl_val:
                    c.futures_create_order(symbol=o['s'], side=(SIDE_SELL if o['l']=="LONG" else SIDE_BUY), type=ORDER_TYPE_MARKET, quantity=o['q'])
                    tiempo_descanso = ahora; ops.remove(o); bloqueo_activo = True

            if not bloqueo_activo and len(ops) == 0 and not tiene_posicion_abierta():
                for m in lista_m:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]; v, o_v = cl[-2], float(k[-2][1])
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                        tipo = 'LONG' if v > o_v else 'SHORT'
                        inv = obtener_saldo_futuros() * p_inv
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round((inv * 5) / p_act, 1)
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=(SIDE_BUY if tipo=='LONG' else SIDE_SELL), type=ORDER_TYPE_MARKET, quantity=cant)
                            ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'inv':inv,'x':5,'be':False,'piso':sl_val})
                            break
            
            if ahora - ultimo_print > 10:
                print(f"💰 Cap: ${obtener_saldo_futuros():.2f} | {'🔎 BUSCANDO...' if len(ops)==0 else f'{ops[0][s]}: Recuperada'}")
                ultimo_print = ahora
        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__": bot()
