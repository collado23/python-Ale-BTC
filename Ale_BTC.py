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
        # Horarios USA (11-19) y ASIA (22:30-06) - Hora Argentina
        ahora_utc = datetime.datetime.now(datetime.timezone.utc)
        arg = ahora_utc - datetime.timedelta(hours=3)
        h = arg.hour + arg.minute/60
        return (11.0 <= h <= 19.0) or (h >= 22.5 or h <= 6.0)

    def get_saldo():
        try:
            res = c.futures_account_balance()
            for b in res:
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except: return 0.0

    cap = get_saldo()
    print(f"🎯 REINICIADO | SALDO: ${cap:.2f} | ROI INICIAL: 0% | SL: -4%")

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
                            'piso': 2.4 if lev >= 15 else -4.0 
                        })
                        print(f"🔗 REENGANCHADO A: {symbol}")
                        break

            # 1. GESTIÓN DE POSICIÓN
            for o in ops[:]:
                # Usamos Mark Price para máxima precisión con la App
                p_m = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                diff = (p_m - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_m)/o['p']
                
                # ROI DESDE CERO (Sin descuentos previos)
                roi_n = (diff * 100 * o['x'])
                
                # 🔥 SALTO A 15X AL 2.9%
                if roi_n >= 2.9 and o['x'] < 15: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 2.4
                        print(f"🔥 SALTO 2.9% EN {o['s']} | TRAILING ON")
                    except: o['be'] = True

                # 🪜 TRAILING STOP (Sube el piso si el precio sube)
                if o['be']:
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']: o['piso'] = nuevo_piso

                # CIERRE (Profit o Stop -4.0%)
                check_cierre = o['piso'] if o['be'] else -4.0
                
                if roi_n >= 5.0 or roi_n <= check_cierre:
                    lado_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=lado_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"✅ CIERRE EN {roi_n:.2f}% | SALDO: ${get_saldo():.2f}")
                    time.sleep(5)
                    ops.remove(o)

            # 2. ENTRADA (Misma lógica, 90% del Capital)
            if not ops and esta_en_horario():
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, v_a, o_v, o_a = cl[-2], cl[-3], op[-2], op[-3]

                    if v > o_v and v > o_a and v > e9 and e9 > e27:
                        tipo = 'LONG'
                    elif v < o_v and v < o_a and v < e9 and e9 < e27:
                        tipo = 'SHORT'
                    else: continue

                    p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                    cap = get_saldo()
                    # Usamos el 90% para que Binance no rebote por centavos
                    cant = round(((cap * 0.90) * 5) / p_act, 1 if 'XRP' not in m else 0)
                    
                    if cant > 0:
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side=SIDE_BUY if tipo=='LONG' else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                        ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'x':5,'be':False,'piso':-4.0})
                        print(f"🎯 DISPARO {tipo} EN {m}")
                        break

            # Consola limpia
            if ops:
                print(f"💰 ${cap:.2f} | ROI: {roi_n:.2f}% | SL: {check_cierre:.2f}% | {time.strftime('%H:%M:%S')}   ", end='\r')
            else:
                print(f"💰 ${cap:.2f} | Acechando... | {time.strftime('%H:%M:%S')}   ", end='\r')

        except Exception as e:
            print(f"⚠️ Reintentando... ({e})")
            time.sleep(20)
        
        time.sleep(10)

if __name__ == "__main__": bot()
