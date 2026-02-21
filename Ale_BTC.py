import os, time, threading, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 SERVER PARA QUE RAILWAY NO SE FRENE ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200); self.end_headers()
        self.wfile.write(b"BOT-OK") 

def run_server():
    try:
        port = int(os.getenv("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), HealthCheck)
        server.serve_forever()
    except: pass

# --- 🚀 MOTOR V143 REFORZADO ---
def bot():
    threading.Thread(target=run_server, daemon=True).start()
    
    # Conexión Segura
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    
    def esta_en_horario():
        # Sincronizado para que ande en los horarios que pediste
        h = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)).hour
        return (11 <= h < 19) or (h >= 22 or h < 6)

    def get_saldo():
        try:
            for b in c.futures_account_balance():
                if b['asset'] == 'USDC': return float(b['balance'])
            return 0.0
        except: return 0.0

    print("🎯 MOTOR INICIADO - BUSCANDO POSICIONES...")

    while True:
        try:
            # 🔄 RECUPERADOR SEGURO (Evita el error 'leverage')
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
                            'piso': 1.5 if lev >= 15 else -2.5
                        })
                        print(f"🔗 ENGANCHADO A: {symbol}")
                        break

            # 1. GESTIÓN CON TRAILING STOP 2%
            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_n = (diff * 100 * o['x']) - 1.0 # -1% estimado por comisiones
                
                # 🔥 SALTO AL 2%
                if roi_n >= 2.0 and o['x'] < 15: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 1.5
                        print("🔥 SALTO 15X!")
                    except: o['be'] = True

                if o['be']:
                    if (roi_n - 0.5) > o['piso']: o['piso'] = roi_n - 0.5

                # CIERRE
                check_c = o['piso'] if o['be'] else -2.5
                if roi_n >= 3.5 or roi_n <= check_c:
                    c.futures_create_order(symbol=o['s'], side=SIDE_SELL if o['l']=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"✅ CIERRE EJECUTADO EN {roi_n:.2f}%")
                    time.sleep(5)
                    ops.remove(o)

            # 2. ENTRADA (95% DE CAPITAL PARA EVITAR ERROR DE MARGEN)
            if not ops and esta_en_horario():
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl, op_v = float(k[-2][4]), float(k[-2][1])
                    if (cl > op_v) or (cl < op_v): # Simplificado para entrar rápido
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cap = get_saldo()
                        # USAMOS 95% PARA QUE BINANCE NO REBOTE POR FALTA DE MARGEN
                        cant = round(((cap * 0.95) * 5) / p_act, 1 if 'XRP' not in m else 0)
                        if cant > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side=SIDE_BUY if cl > op_v else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                            ops.append({'s':m,'l':'LONG' if cl > op_v else 'SHORT','p':p_act,'q':cant,'x':5,'be':False,'piso':-2.5})
                            break

        except Exception as e:
            # ESTA PARTE EVITA QUE SE FRENE EL CONTENEDOR
            print(f"⚠️ Reintentando... ({e})")
            time.sleep(20)
        
        time.sleep(10)

if __name__ == "__main__": 
    bot()
