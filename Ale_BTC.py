import os, time, threading, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 SERVER DE SALUD ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200); self.end_headers()
        self.wfile.write(b"BOT-ALE-BTC-OK") 

def run_server():
    try:
        port = int(os.getenv("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), HealthCheck)
        server.serve_forever()
    except Exception: pass

def bot():
    threading.Thread(target=run_server, daemon=True).start()
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    
    def get_saldo():
        try:
            for b in c.futures_account_balance():
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except Exception: return 0.0

    print(f"🎯 ALE_BTC | FORZADO 5X ACTIVADO | BLINDAJE V148")

    while True:
        try:
            cap = get_saldo()
            limite_alcanzado = cap >= 1000.0

            # 1. RECUPERADOR Y FORZADO DE 5X
            if not ops:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p.get('positionAmt', 0))
                    if amt != 0:
                        symbol = p['symbol']
                        lev_actual = int(p.get('leverage', 5))
                        
                        # Si detecta que está en 15x y no debería, intenta bajarlo
                        if lev_actual != 5:
                            try:
                                c.futures_change_leverage(symbol=symbol, leverage=5)
                                lev_actual = 5
                                print(f"📉 AJUSTANDO POSICIÓN A 5X...")
                            except: pass

                        ops.append({
                            's': symbol, 'l': 'LONG' if amt > 0 else 'SHORT',
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': lev_actual, 'be': False, 'piso': -4.0 
                        })
                        break

            # 2. GESTIÓN DE RIESGO
            for o in ops[:]:
                p_m = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                diff = (p_m - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_m)/o['p']
                roi_n = (diff * 100 * o['x'])

                if roi_n >= 2.5 and not o['be']:
                    o['be'] = True; o['piso'] = 2.0

                if roi_n >= 2.9 and o['x'] < 15: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'] = 15; o['be'] = True
                        if o['piso'] < 2.4: o['piso'] = 2.4
                        print(f"🔥 SALTO EXITOSO A 15X")
                    except: pass

                if o['be']:
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']: o['piso'] = nuevo_piso

                check_cierre = o['piso'] if o['be'] else -4.0
                
                if roi_n >= 15.0 or roi_n <= check_cierre:
                    lado_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=lado_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"✅ CIERRE EN {roi_n:.2f}%")
                    time.sleep(2); ops.remove(o)

            # 3. ENTRADA CON PAUSA DE SEGURIDAD (EL BLINDAJE)
            if not ops and not limite_alcanzado:
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl, o_v = float(k[-2][4]), float(k[-2][1])
                    e9, e27 = sum([float(x[4]) for x in k[-9:]])/9, sum([float(x[4]) for x in k[-27:]])/27

                    if (cl > o_v and cl > e9 and e9 > e27) or (cl < o_v and cl < e9 and e9 < e27):
                        tipo = 'LONG' if cl > o_v else 'SHORT'
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        
                        # --- PASOS DE BLINDAJE ---
                        print(f"🛠️ PREPARANDO ENTRADA EN {m}...")
                        try:
                            # 1. Forzamos el cambio a 5x ANTES de comprar
                            c.futures_change_leverage(symbol=m, leverage=5)
                            time.sleep(2) # Esperamos 2 segundos para que Binance procese
                        except: pass
                        
                        cant = round(((cap * 0.80) * 5) / p_act, 1 if 'XRP' not in m else 0)
                        
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY if tipo=='LONG' else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                            ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'x':5,'be':False,'piso':-4.0})
                            print(f"🎯 DISPARO OK A 5X")
                            break

            time.sleep(10)

        except Exception as e:
            time.sleep(10)

if __name__ == "__main__": bot()
