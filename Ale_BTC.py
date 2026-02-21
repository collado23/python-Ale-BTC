import os, time, threading, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 1. SERVER DE SALUD (Mantiene el bot vivo en Railway) ---
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

# --- 🚀 2. MOTOR V143 PROFESIONAL ---
def bot():
    # El servidor de salud arranca antes que nada
    threading.Thread(target=run_server, daemon=True).start()
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    
    def esta_en_horario():
        # Hora Argentina (UTC-3)
        ahora_utc = datetime.datetime.now(datetime.timezone.utc)
        arg = ahora_utc - datetime.timedelta(hours=3)
        h = arg.hour + arg.minute/60
        # USA: 11 a 18 | ASIA: 22:30 a 06
        return (11.0 <= h <= 18.0) or (h >= 22.5 or h <= 6.0)

    def get_saldo():
        try:
            for b in c.futures_account_balance():
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except Exception: return 0.0

    cap = get_saldo()
    print(f"🎯 BOT INICIADO | SALDO: ${cap:.2f} | SL: -4% | SALTO: 2.9%")

    while True:
        try:
            # 🔄 RECUPERADOR (Evita abrir doble)
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

            # 1. GESTIÓN DE RIESGO Y TRAILING
            for o in ops[:]:
                p_m = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                diff = (p_m - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_m)/o['p']
                roi_n = (diff * 100 * o['x']) # ROI REAL (Empieza en 0)

                # Trailing al 2.5%
                if roi_n >= 2.5 and not o['be']:
                    o['be'] = True; o['piso'] = 2.0
                    print(f"✅ TRAILING ACTIVO")

                # Salto a 15x al 2.9%
                if roi_n >= 2.9 and o['x'] < 15: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'] = 15
                        if o['piso'] < 2.4: o['piso'] = 2.4
                        print(f"🔥 SALTO 15X")
                    except Exception: pass

                if o['be']:
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']: o['piso'] = nuevo_piso

                # Cierre por SL o Trailing
                check_cierre = o['piso'] if o['be'] else -4.0
                if roi_n >= 6.0 or roi_n <= check_cierre:
                    lado_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=lado_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"✅ CIERRE EN {roi_n:.2f}%")
                    time.sleep(5)
                    ops.remove(o)

            # 2. ENTRADA (SOLO EN HORARIO)
            if not ops and esta_en_horario():
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], op[-2]

                    if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
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
            
            # Status cada 10 seg
            if not ops and not esta_en_horario():
                print(f"💰 ${cap:.2f} | Esperando Wall Street/Asia... | {time.strftime('%H:%M:%S')}   ", end='\r')
            elif ops:
                print(f"💰 ${cap:.2f} | ROI: {roi_n:.2f}% | PISO: {check_cierre:.2f}% | {time.strftime('%H:%M:%S')}   ", end='\r')

        except Exception as e:
            time.sleep(15)
        
        time.sleep(10)

if __name__ == "__main__": 
    bot()
