import os, time, threading, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- SERVER DE SALUD ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200); self.end_headers()
        self.wfile.write(b"BOT-ALE-OK") 

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

    def esta_en_horario():
        ahora_utc = datetime.datetime.now(datetime.timezone.utc)
        arg = ahora_utc - datetime.timedelta(hours=3)
        h = arg.hour + arg.minute/60
        return (11.0 <= h <= 18.0) or (h >= 22.5 or h <= 6.0)

    def get_saldo():
        try:
            for b in c.futures_account_balance():
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except Exception: return 0.0

    print(f"🎯 ALE_BTC V150 | COMPLETO Y BLINDADO")

    while True:
        try:
            cap = get_saldo()
            limite_alcanzado = cap >= 1000.0

            # 1. RASTREADOR DE POSICIÓN ABIERTA (Recuperador)
            if not ops:
                posiciones = c.futures_position_information()
                for p in posiciones:
                    amt = float(p.get('positionAmt', 0))
                    if amt != 0:
                        symbol = p['symbol']
                        lev_actual = int(p.get('leverage', 5))
                        
                        # Si está en 15x y no hay ganancia, el bot lo sabe
                        ops.append({
                            's': symbol, 'l': 'LONG' if amt > 0 else 'SHORT',
                            'p': float(p['entryPrice']), 'q': abs(amt), 
                            'x': lev_actual, 'be': False, 'piso': -4.0 
                        })
                        print(f"🔗 REENGANCHADO A {symbol} ({lev_actual}x)")
                        break

            # 2. GESTIÓN DE RIESGO
            for o in ops[:]:
                p_m = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                diff = (p_m - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_m)/o['p']
                roi_n = (diff * 100 * o['x'])

                if roi_n >= 2.5 and not o['be']:
                    o['be'] = True; o['piso'] = 2.0
                    print(f"✅ TRAILING ACTIVO")

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
                    time.sleep(5); ops.remove(o)

            # 3. ENTRADA (CON FILTROS COMPLETOS)
            if not ops and esta_en_horario() and not limite_alcanzado:
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl, o_v = float(k[-2][4]), float(k[-2][1])
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27

                    # Estrategia: Vela confirma + Medias confirman
                    if (cl > o_v and cl > e9 and e9 > e27) or (cl < o_v and cl < e9 and e9 < e27):
                        tipo = 'LONG' if cl > o_v else 'SHORT'
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        
                        # --- BLINDAJE DE ENTRADA ---
                        try:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            time.sleep(2)
                        except: pass
                        
                        cant = round(((cap * 0.80) * 5) / p_act, 1 if 'XRP' not in m else 0)
                        
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY if tipo=='LONG' else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                            ops.append({'s':m,'l':tipo,'p':p_act,'q':cant,'x':5,'be':False,'piso':-4.0})
                            print(f"🎯 DISPARO {tipo} EN {m} A 5X")
                            break

            # Consola de estado
            if ops:
                print(f"💰 ${cap:.2f} | {ops[0]['s']} | ROI: {roi_n:.2f}% | PISO: {check_cierre:.2f}%", end='\r')
            elif limite_alcanzado:
                print(f"🛑 SALDO > $1000 | CAPITAL: ${cap:.2f}", end='\r')
            else:
                txt = "Acechando..." if esta_en_horario() else "Fuera de horario..."
                print(f"💰 ${cap:.2f} | {txt} | {time.strftime('%H:%M:%S')}", end='\r')

        except Exception as e:
            time.sleep(10)
        
        time.sleep(10)

if __name__ == "__main__": bot()
