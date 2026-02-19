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
    
    # Usa tus variables de entorno BINANCE_API_KEY y BINANCE_API_SECRET
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0

    def obtener_saldo_futuros():
        try:
            f = c.futures_account_balance()
            return next((float(i['balance']) for i in f if i['asset'] == 'USDC'), 0.0)
        except: return 0.0

    print(f"🐊 !!! FUTUROS REAL V146 !!! | ESCALADOR ORIGINAL | USDC")

    while True:
        ahora = time.time()
        roi_vis, gan_vis, piso_vis = 0.0, 0.0, -2.5
        
        try:
            saldo_usdc = obtener_saldo_futuros()

            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_a) / o['p']
                
                roi = (diff * 100 * o['x']) - 0.90
                ganancia_usdc = o['inv'] * (roi / 100)
                roi_vis, gan_vis, piso_vis = roi, ganancia_usdc, o['piso']
                
                # 🔥 EL SALTO AL 1.5%
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.0 
                    print(f"\n🚀 ¡SALTO 15X! {o['s']} | ROI: {roi:.2f}%")

                # 🛡️ TU ESCALADOR ORIGINAL (SIN CAMBIOS)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0:   n_p = 24.5
                    elif roi >= 20.0: n_p = 19.5
                    elif roi >= 15.0: n_p = 14.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 8.0:  n_p = 7.5
                    elif roi >= 6.0:  n_p = 5.5
                    elif roi >= 4.0:  n_p = 3.5
                    elif roi >= 2.5:  n_p = 2.0
                    elif roi >= 2.0:  n_p = 1.5
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ ESCALADOR: {o['s']} subió piso a {o['piso']}%")

                    # CIERRE POR PISO
                    if roi < o['piso']:
                        side_cierre = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                        c.futures_create_order(symbol=o['s'], side=side_cierre, type=ORDER_TYPE_MARKET, quantity=o['q'])
                        ultima_moneda = o['s']
                        tiempo_descanso = ahora
                        print(f"\n✅ VENTA: {o['s']} | Compra: {o['p']} | Venta: {p_a} | Ganancia: +{ganancia_usdc:.2f} USDC | ROI: {roi:.2f}%")
                        ops.remove(o)
                        continue

                # ⚠️ STOP LOSS
                if not o['be'] and roi <= -2.5:
                    side_cierre = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side_cierre, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    ultima_moneda = o['s']
                    tiempo_descanso = ahora
                    print(f"\n⚠️ STOP LOSS: {o['s']} | Perdida: {ganancia_usdc:.2f} USDC")
                    ops.remove(o)

            # --- 🎯 BUSCADOR ---
            if len(ops) < 1 and (ahora - tiempo_descanso) > 10 and saldo_usdc >= 10:
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    if m == ultima_moneda: continue 
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    v, o_v = cl[-2], float(k[-2][1])
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27

                    if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                        tipo = 'LONG' if v > o_v else 'SHORT'
                        side_entrada = SIDE_BUY if tipo == 'LONG' else SIDE_SELL
                        print(f"\n🎯 ABRIENDO {tipo} EN {m}...")
                        
                        c.futures_change_leverage(symbol=m, leverage=5)
                        precio_actual = float(c.futures_symbol_ticker(symbol=m)['price'])
                        # Ajustamos la cantidad para que sean $10
                        cantidad = round((10.0 * 5) / precio_actual, 1) 
                        
                        c.futures_create_order(symbol=m, side=side_entrada, type=ORDER_TYPE_MARKET, quantity=cantidad)
                        ops.append({'s':m,'l':tipo,'p':precio_actual,'q':cantidad,'inv':10.0,'x':5,'be':False, 'piso': -2.5})
                        print(f"✔️ OK: {cantidad} {m} a {precio_actual}")
                        break
            
            if len(ops) > 0:
                mon = f" | {ops[0]['s']}: {roi_vis:.2f}% (${gan_vis:.2f}) | Piso: {piso_vis}%"
            else:
                mon = f" | 🔎 Buscando... (Saldo: {saldo_usdc:.2f} USDC)"
            print(f"💰 Billetera: {saldo_usdc:.2f} USDC{mon}", end='\r')
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            time.sleep(10)
        time.sleep(1)

if __name__ == "__main__": bot()
