import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0

    # --- 💰 ESCÁNER DE BILLETERA USDC ---
    def obtener_saldo_total():
        try:
            # Busca USDC en Spot
            s = c.get_asset_balance(asset='USDC')
            saldo_spot = float(s['free']) if s else 0.0
            # Busca USDC en Futuros
            f = c.futures_account_balance()
            saldo_fut = next((float(i['balance']) for i in f if i['asset'] == 'USDC'), 0.0)
            return saldo_spot + saldo_fut
        except: return 0.0

    print(f"🐊 MOTOR V146 REAL | MONEDA: USDC | SALTO 15X AL 1.5%")

    while True:
        ahora = time.time()
        roi_vis, gan_vis, piso_vis = 0.0, 0.0, -2.5
        
        try:
            # Actualiza el capital con lo que hay en USDC
            cap = obtener_saldo_total()
            if cap == 0: cap = 10.0 # Valor de seguridad por si falla la API

            for o in ops[:]:
                # Usamos pares con USDC
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                roi = (diff * 100 * o['x']) - 0.90
                ganancia_usdc = cap * (roi / 100)
                roi_vis, gan_vis, piso_vis = roi, ganancia_usdc, o['piso']
                
                # 🔥 SALTO 15X AL 1.5%
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.0 
                    print(f"\n🚀 ¡SALTO 15X! {o['s']} | Entré a: {o['p']} | ROI: {roi:.2f}%")

                # 🛡️ ESCALADOR AGRESIVO (Con el 6% incluido)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0:   n_p = 24.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 8.0:  n_p = 7.5
                    elif roi >= 6.0:  n_p = 5.5
                    elif roi >= 4.0:  n_p = 3.5
                    elif roi >= 2.5:  n_p = 2.0
                    elif roi >= 2.0:  n_p = 1.5
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ ESCALADOR: {o['s']} subió piso a {o['piso']}% | ROI: {roi:.2f}%")

                    if roi < o['piso']:
                        ultima_moneda = o['s']
                        tiempo_descanso = ahora
                        print(f"\n✅ VENTA: {o['s']} | Compra: {o['p']} | Venta: {p_a} | Ganancia: +{ganancia_usdc:.2f} USDC | ROI: {roi:.2f}%")
                        ops.remove(o)
                        continue

                # ⚠️ STOP LOSS
                if not o['be'] and roi <= -2.5:
                    ultima_moneda = o['s']
                    tiempo_descanso = ahora
                    print(f"\n⚠️ STOP LOSS: {o['s']} | Perdida: {ganancia_usdc:.2f} USDC | ROI: {roi:.2f}%")
                    ops.remove(o)

            # --- 🎯 BUSCADOR (PARES USDC) ---
            if len(ops) < 1 and (ahora - tiempo_descanso) > 10:
                # Cambiamos a pares con USDC
                monedas = ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']
                for m in monedas:
                    if m == ultima_moneda: continue 
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    v, o_v = cl[-2], float(k[-2][1])
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27

                    if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                        tipo = 'LONG' if v > o_v else 'SHORT'
                        ops.append({'s':m,'l':tipo,'p':cl[-1],'x':5,'be':False, 'piso': -2.5})
                        print(f"\n🎯 ENTRADA REAL: {m} | Precio: {cl[-1]} | Tipo: {tipo} | Cap: {cap:.2f} USDC")
                        break
            
            # --- 🕒 MONITOR DETALLADO ---
            if len(ops) > 0:
                mon = f" | {ops[0]['s']}: {roi_vis:.2f}% ({gan_vis:.2f} USDC) | Piso: {piso_vis}%"
            elif (ahora - tiempo_descanso) <= 10:
                mon = f" | ⏳ Pausa: {int(10-(ahora-tiempo_descanso))}s"
            else:
                mon = " | 🔎 Buscando oportunidad..."

            print(f"💰 Billetera: {cap:.2f} USDC{mon} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except Exception as e:
            time.sleep(5)
            
        time.sleep(1)

if __name__ == "__main__": bot()
