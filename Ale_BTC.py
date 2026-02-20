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

# --- 🚀 2. MOTOR V143 REFORZADO ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # Variables de Railway
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
    print(f"🎯 V143 | STOP -2.5 | SALTO 2.0 | SALDO: ${cap:.2f}")

    while True:
        t_l = time.time()
        try:
            # 🔄 RECUPERADOR DINÁMICO
            if not ops:
                posiciones = c.futures_position_information()
                for p in posiciones:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        simbolo = p['symbol']
                        lado = 'LONG' if amt > 0 else 'SHORT'
                        precio_entrada = float(p['entryPrice'])
                        palanca = int(p['leverage'])
                        # Reengancha con el nuevo stop loss de -2.5
                        ops.append({
                            's': simbolo, 'l': lado, 'p': precio_entrada, 
                            'q': abs(amt), 'x': palanca, 
                            'be': True if palanca >= 15 else False, 
                            'piso': 1.5 if palanca >= 15 else -2.5
                        })
                        print(f"\n🔗 POSICIÓN RECUPERADA: {simbolo}")
                        break

            # 1. GESTIÓN DE OPERACIÓN
            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI NETO (0.9 de comisión)
                roi_bruto = diff * 100 * o['x']
                roi_n = roi_bruto - 0.9
                
                # 🔥 SALTO A 15X (Ajustado a 2.0% NETO)
                if roi_n >= 2.0 and o['x'] < 15: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 1.5 # Piso inicial tras salto
                        print(f"\n🔥 SALTO 15X REALIZADO EN {o['s']}")
                    except: o['be'] = True

                # 🪜 ESCALADOR +0.5
                if o['be']:
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']: o['piso'] = nuevo_piso

                # 📉 CIERRE (Profit 3.5%, Stop -2.5% o Piso)
                check_cierre = o['piso'] if o['be'] else -2.5
                if roi_n >= 3.5 or roi_n <= check_cierre:
                    side_cierre = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    try:
                        c.futures_create_order(symbol=o['s'], side=side_cierre, type=ORDER_TYPE_MARKET, quantity=o['q'])
                        print(f"\n✅ CIERRE EN {o['s']} | NETO: {roi_n:.2f}%")
                    except: pass
                    
                    time.sleep(2)
                    cap = obtener_saldo_real()
                    ops.remove(o)

            # 2. ENTRADA (E9/E27 SIN BTC)
            if not ops:
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC', 'PEPEUSDC', 'DOGEUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, op_v = float(k[-2][4]), float(k[-2][1]) 
                    k_full = [float(x[4]) for x in k]
                    e9, e27 = sum(k_full[-9:])/9, sum(k_full[-27:])/27
                    
                    if (cl > op_v and cl > e9 and e9 > e27) or (cl < op_v and cl < e9 and e9 < e27):
                        tipo = 'LONG' if cl > op_v else 'SHORT'
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((cap * 0.80) * 5) / p_act, 1)
                        
                        if cant > 0:
                            try:
                                c.futures_change_leverage(symbol=m, leverage=5)
                                side_orden = SIDE_BUY if tipo == 'LONG' else SIDE_SELL
                                c.futures_create_order(symbol=m, side=side_orden, type=ORDER_TYPE_MARKET, quantity=cant)
                                ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'x':5,'be':False, 'piso': -2.5})
                                print(f"\n🎯 DISPARO {tipo}: {m}")
                                break
                            except: pass

            # MONITOR
            if ops:
                print(f"💰 ${cap:.2f} | ROI: {roi_n:.2f}% | PISO: {o['piso']:.2f}% | {time.strftime('%H:%M:%S')}   ", end='\r')
            else:
                if int(time.time()) % 60 == 0: cap = obtener_saldo_real()
                print(f"💰 ${cap:.2f} | Buscando... | {time.strftime('%H:%M:%S')}   ", end='\r')
            
        except Exception as e:
            time.sleep(5)
        
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": 
    bot()
