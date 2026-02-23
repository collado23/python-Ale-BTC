import os, time, threading, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- SERVER DE SALUD ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ALE-BTC-V155-OK") 

def run_server():
    try:
        port = int(os.getenv("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), HealthCheck)
        server.serve_forever()
    except Exception: pass

def bot():
    threading.Thread(target=run_server, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    ops = []
    
    def esta_en_horario():
        # FORZADO HORA ARGENTINA (UTC-3)
        tz_arg = datetime.timezone(datetime.timedelta(hours=-3))
        h = datetime.datetime.now(tz_arg).hour + datetime.datetime.now(tz_arg).minute/60
        return (11.0 <= h <= 18.0) or (h >= 22.5 or h <= 6.0)

    print("🐊 MOTOR V155 CARGADO | ESPERANDO HORA ARGENTINA...")

    while True:
        try:
            # 1. ACTUALIZAR SALDO
            cap = 0.0
            for b in c.futures_account_balance():
                if b['asset'] == 'USDC': cap = float(b['balance'])
            
            if cap >= 1000.0:
                print(f"🛑 FRENO DE $1000 ACTIVADO | CAP: ${cap:.2f}", end='\r')
                time.sleep(30); continue

            # 2. RECUPERADOR DE POSICIÓN
            if not ops:
                for p in c.futures_position_information():
                    amt = float(p.get('positionAmt', 0))
                    if amt != 0:
                        ops.append({'s':p['symbol'],'l':'LONG' if amt>0 else 'SHORT','p':float(p['entryPrice']),'q':abs(amt),'x':int(p['leverage']),'be':False,'piso':-4.0})
                        break

            # 3. GESTIÓN DE RIESGO (CON CONTROL DE 15X)
            for o in ops[:]:
                m_p = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                roi = ((m_p - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - m_p)/o['p']) * 100 * o['x']

                if roi >= 2.5 and not o['be']: o['be'] = True; o['piso'] = 2.0
                
                # SALTO A 15X SOLO SI HAY GANANCIA SEGURA
                if roi >= 2.9 and o['x'] < 15:
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'] = 15; o['piso'] = 2.4
                    except: pass

                if o['be']:
                    if (roi - 0.5) > o['piso']: o['piso'] = roi - 0.5

                piso_final = o['piso'] if o['be'] else -4.0
                if roi >= 15.0 or roi <= piso_final:
                    c.futures_create_order(symbol=o['s'], side=SIDE_SELL if o['l']=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"✅ CIERRE REALIZADO: {roi:.2f}%")
                    ops = []; time.sleep(5)
                else:
                    print(f"💰 ${cap:.2f} | {o['s']} | ROI: {roi:.2f}% | PISO: {piso_final:.2f}%", end='\r')

            # 4. ENTRADA CON "SÚPER-BLINDAJE"
            if not ops and esta_en_horario():
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl, ov = float(k[-2][4]), float(k[-2][1])
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27

                    if (cl > ov and cl > e9 and e9 > e27) or (cl < ov and cl < e9 and e9 < e27):
                        # --- PASO 1: CAMBIAR PALANCA ---
                        c.futures_change_leverage(symbol=m, leverage=5)
                        time.sleep(3) # Pausa larga para que Binance asiente el 5x
                        
                        # --- PASO 2: VERIFICAR PALANCA ANTES DE COMPRAR ---
                        info = c.futures_position_information(symbol=m)
                        if int(info[0]['leverage']) == 5:
                            tipo = 'LONG' if cl > ov else 'SHORT'
                            p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                            cant = round(((cap * 0.80) * 5) / p_act, 1 if 'XRP' not in m else 0)
                            c.futures_create_order(symbol=m, side=SIDE_BUY if tipo=='LONG' else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"🎯 ENTRADA PERFECTA A 5X EN {m}")
                            break
            
            if not ops and not esta_en_horario():
                print(f"💰 ${cap:.2f} | Fuera de horario (ARG) | {time.strftime('%H:%M:%S')}", end='\r')

        except Exception as e:
            time.sleep(10)
        time.sleep(10)

if __name__ == "__main__": bot()
