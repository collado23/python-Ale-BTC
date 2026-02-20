import os, time, threading 
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 1. SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🚀 2. MOTOR V143 ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # --- CONECTANDO CON TUS VARIABLES DE RAILWAY ---
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    
    def obtener_saldo_real():
        try:
            res = c.futures_account_balance()
            for b in res:
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except: return 0.0

    cap = obtener_saldo_real()
    print(f"🎯 V143 FRANCOTIRADOR | VARIABLES CONECTADAS | SALDO: ${cap:.2f}")

    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN CON ESCALADOR DINÁMICO
            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_n = (diff * 100 * o['x']) - 0.9 
                
                # 🔥 SALTO A 15X (ROI 2.5% NETO)
                if roi_n >= 2.5 and o['x'] == 5: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 2.0
                        print(f"\n🔥 SALTO 15X REALIZADO EN {o['s']}")
                    except: o['be'] = True

                # 🪜 ESCALADOR +0.5 (SIEMPRE SUBE)
                if o['be']:
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']:
                        o['piso'] = nuevo_piso

                # 📉 CIERRES REALES (Stop -1.6 o Piso dinámico)
                check_cierre = o['piso'] if o['be'] else -1.6
                if roi_n >= 10.0 or roi_n <= check_cierre:
                    side_cierre = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    try:
                        c.futures_create_order(symbol=o['s'], side=side_cierre, type=ORDER_TYPE_MARKET, quantity=o['q'])
                        print(f"\n✅ CIERRE EJECUTADO | ROI: {roi_n:.2f}% | PISO: {check_cierre:.2f}%")
                    except Exception as e:
                        print(f"\n❌ ERROR CIERRE: {e}")
                    
                    time.sleep(2)
                    cap = obtener_saldo_real()
                    ops.remove(o)

            # 2. ENTRADA (E9/E27 - SIN BTC)
            if len(ops) < 1:
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC',]:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, op_v = float(k[-2][4]), float(k[-2][1]) 
                    k_full = [float(x[4]) for x in k]
                    e9, e27 = sum(k_full[-9:])/9, sum(k_full[-27:])/27
                    
                    p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                    
                    if cl > op_v and cl > e9 and e9 > e27: # LONG
                        tipo = 'LONG'
                    elif cl < op_v and cl < e9 and e9 < e27: # SHORT
                        tipo = 'SHORT'
                    else: tipo = None
                    
                    if tipo:
                        cant = round(((cap * 0.80) * 5) / p_act, 1)
                        if cant > 0:
                            try:
                                c.futures_change_leverage(symbol=m, leverage=5)
                                side_orden = SIDE_BUY if tipo == 'LONG' else SIDE_SELL
                                c.futures_create_order(symbol=m, side=side_orden, type=ORDER_TYPE_MARKET, quantity=cant)
                                ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'x':5,'be':False, 'piso': -1.6})
                                print(f"\n🎯 DISPARO {tipo}: {m} | CANT: {cant}")
                                break
                            except Exception as e:
                                print(f"\n❌ ERROR ENTRADA: {e}")

            if len(ops) > 0:
                print(f"💰 ${cap:.2f} | ROI: {roi_n:.2f}% | PISO: {o['piso']:.2f}% | {time.strftime('%H:%M:%S')}   ", end='\r')
            else:
                if int(time.time()) % 60 == 0: cap = obtener_saldo_real()
                print(f"💰 ${cap:.2f} | Acechando... | {time.strftime('%H:%M:%S')}   ", end='\r')
            
        except Exception as e:
            time.sleep(5)
        
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": 
    bot()
