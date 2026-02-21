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
    except: pass

# --- 🚀 MOTOR V143 PROFESIONAL ---
def bot():
    threading.Thread(target=run_server, daemon=True).start()
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    
    def esta_en_horario():
        # Calculamos la hora actual en Argentina (UTC-3)
        ahora_utc = datetime.datetime.now(datetime.timezone.utc)
        arg = ahora_utc - datetime.timedelta(hours=3)
        h = arg.hour + arg.minute/60

        # --- BLOQUES DE CORTE ---
        # Bloque Wall Street: 11:00 a 18:00
        # Bloque Asia: 22:30 a 06:00
        es_usa = (11.0 <= h <= 18.0)
        es_asia = (h >= 22.5 or h <= 6.0)
        
        return es_usa or es_asia

    def get_saldo():
        try:
            res = c.futures_account_balance()
            for b in res:
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except: return 0.0

    cap = get_saldo()
    print(f"🎯 ALE_BTC | HORARIO WALL STREET Y ASIA | SALTO 2.9% | SL -4%")

    while True:
        try:
            # 🔄 RECUPERADOR
            if not ops:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p.get('positionAmt', 0))
                    if amt != 0:
                        symbol = p['symbol']
                        lev = int(p.get('leverage', 5))
                        ops.append({
                            's': symbol, 'l': 'LONG' if amt > 0 else 'SHORT',
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': lev, 'be': True if lev >= 15 else False, 
                            'piso': 2.0 if lev >= 15 else -4.0 
                        })
                        print(f"🔗 REENGANCHADO A: {symbol}")
                        break

            # 1. GESTIÓN DE POSICIÓN
            for o in ops[:]:
                p_m = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                diff = (p_m - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_m)/o['p']
                roi_n = (diff * 100 * o['x'])
                
                # 🪜 TRAILING STOP 2.5%
                if roi_n >= 2.5 and not o['be']:
                    o['be'] = True
                    o['piso'] = 2.0
                    print(f"✅ TRAILING ACTIVADO (PISO 2.0%)")

                # 🔥 SALTO 15X A 2.9%
                if roi_n >= 2.9 and o['x'] < 15: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'] = 15
                        if o['piso'] < 2.4: o['piso'] = 2.4
                        print(f"🔥 SALTO 15X EN {o['s']}")
                    except: pass

                if o['be']:
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']: o['piso'] = nuevo_piso

                # CIERRES
                check_cierre = o['piso'] if o['be'] else -4.0
                
                if roi_n >= 6.0 or roi_n <= check_cierre:
                    lado_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=lado_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"✅ CIERRE EN {roi_n:.2f}% | PISO: {check_cierre:.2f}%")
                    time.sleep(5)
                    ops.remove(o)

            # 2. ENTRADA (SÓLO SI ESTÁ EN HORARIO WALL STREET / ASIA)
            if not ops:
                if esta_en_horario():
                    for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                        k = c.futures_klines(symbol=m, interval='1m', limit=30)
                        cl = [float(x[4]) for x in k]
                        op = [float(x[1]) for x in k]
                        e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                        v, v_a, o_v, o_a = cl[-2], cl[-3], op[-2], op[-3]

                        if (v > o_v and v > o_a and v > e9 and e9 > e27) or (v < o_v and v < o_a and v < e9 and e9 < e27):
                            tipo = 'LONG' if v > o_v else 'SHORT'
                            p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                            cap = get_saldo()
                            cant = round(((cap * 0.90) * 5) / p_act, 1 if 'XRP' not in m else 0)
                            
                            if cant > 0:
                                c.futures_change_leverage(symbol=m, leverage=5)
                                c.futures_create_order(symbol=m, side=SIDE_BUY if tipo=='LONG' else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                                ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'x':5,'be':False,'piso':-4.0})
                                print(f"🎯 DISPARO {tipo} EN {m}")
                                break
                else:
                    # Mensaje discreto para saber que está esperando el horario
                    if int(time.time()) % 60 == 0:
                        print("💤 Fuera de horario (Wall Street/Asia). Bot en espera...")

        except Exception as e:
            time.sleep(20)
        
        time.sleep(10)

if __name__ == "__main__": bot()
