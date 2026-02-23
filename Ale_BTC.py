import os, time, threading, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- SERVER DE SALUD (Para que Railway no lo mate) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ALE-BTC-V156-VIVO") 

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
        ahora = datetime.datetime.now(tz_arg)
        h = ahora.hour + ahora.minute/60
        return (11.0 <= h <= 18.0) or (h >= 22.5 or h <= 6.0)

    print("🚀 MOTOR V156 ARRANCANDO...")

    while True:
        try:
            # 1. ACTUALIZAR SALDO Y HORA
            tz_arg = datetime.timezone(datetime.timedelta(hours=-3))
            ahora_arg = datetime.datetime.now(tz_arg)
            hora_str = ahora_arg.strftime('%H:%M:%S')
            
            cap = 0.0
            try:
                for b in c.futures_account_balance():
                    if b['asset'] == 'USDC': cap = float(b['balance'])
            except: pass

            # 2. RECUPERADOR: BUSCAR SI HAY ALGO ABIERTO EN BINANCE
            if not ops:
                posiciones = c.futures_position_information()
                for p in posiciones:
                    amt = float(p.get('positionAmt', 0))
                    if amt != 0:
                        symbol = p['symbol']
                        entry_price = float(p['entryPrice'])
                        lev = int(p.get('leverage', 5))
                        ops.append({
                            's': symbol, 
                            'l': 'LONG' if amt > 0 else 'SHORT',
                            'p': entry_price, 
                            'q': abs(amt), 
                            'x': lev, 
                            'be': False, 
                            'piso': -4.0 
                        })
                        print(f"\n🔗 REENGANCHADO A: {symbol} | APALANCAMIENTO: {lev}x")
                        break

            # 3. GESTIÓN DE RIESGO (Si hay operación)
            if ops:
                o = ops[0]
                m_p = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                diff = (m_p - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - m_p)/o['p']
                roi = diff * 100 * o['x']

                if roi >= 2.5 and not o['be']: o['be'] = True; o['piso'] = 2.0
                
                # Salto a 15x
                if roi >= 2.9 and o['x'] < 15:
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'] = 15; o['piso'] = 2.4
                        print(f"\n🔥 SALTO A 15X EXITOSO")
                    except: pass

                if o['be']:
                    if (roi - 0.5) > o['piso']: o['piso'] = roi - 0.5

                piso_f = o['piso'] if o['be'] else -4.0
                
                if roi >= 15.0 or roi <= piso_f:
                    side_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"\n✅ CIERRE EN ROI: {roi:.2f}%")
                    ops = []; time.sleep(5)
                else:
                    print(f"💰 ${cap:.2f} | {o['s']} | ROI: {roi:.2f}% | PISO: {piso_f:.2f}% | {hora_str}", end='\r')

            # 4. ENTRADA (Solo si no hay nada abierto y es horario)
            elif esta_en_horario():
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl, ov = float(k[-2][4]), float(k[-2][1])
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27

                    if (cl > ov and cl > e9 and e9 > e27) or (cl < ov and cl < e9 and e9 < e27):
                        # BLINDAJE 5X
                        c.futures_change_leverage(symbol=m, leverage=5)
                        time.sleep(2)
                        
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((cap * 0.80) * 5) / p_act, 1 if 'XRP' not in m else 0)
                        
                        tipo = 'LONG' if cl > ov else 'SHORT'
                        c.futures_create_order(symbol=m, side=SIDE_BUY if tipo=='LONG' else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"\n🎯 DISPARO {tipo} EN {m} A 5X")
                        break
                print(f"💰 ${cap:.2f} | Acechando... | {hora_str}", end='\r')

            else:
                # FUERA DE HORARIO
                print(f"💰 ${cap:.2f} | Esperando hora (22:30) | {hora_str}", end='\r')

        except Exception as e:
            # Si hay error, lo mostramos para que no se tilde sin saber por qué
            print(f"\n⚠️ Error: {e}")
            time.sleep(10)
        
        time.sleep(10)

if __name__ == "__main__": bot()
