import os, time, redis, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    if not r: return None
    try:
        if leer:
            v = r.get("mem_v170_salto_fijo")
            return eval(v) if v else None
        else: r.set("mem_v170_salto_fijo", str(d))
    except: return None

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    ak = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_APY_KEY")
    as_ = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_APY_SECRET")
    c = Client(ak, as_)
    
    datos = g_m(leer=True) or {"ops": []}
    ops = datos["ops"]
    monedas = ['SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT', 'LINKUSDT', 'PEPEUSDT']

    print(f"🚀 V170 - SALTO 15X GARANTIZADO - 6 MONEDAS")

    while True:
        try:
            bal = c.futures_account_balance()
            cap = next((float(b['balance']) for b in bal if b['asset'] == 'USDT'), 0.0)
            g_m(d={"ops": ops})

            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                # --- INTENTO DE SALTO REFORZADO ---
                if roi > 0.20 and o['x'] == 6:
                    try:
                        # Forzamos el cambio de leverage en la API
                        res = c.futures_change_leverage(symbol=o['s'], leverage=15)
                        if int(res['leverage']) == 15:
                            o['x'] = 15
                            print(f"🔥 SALTO EXITOSO: Ahora operando a 15x en {o['s']}")
                    except Exception as e:
                        print(f"❌ Binance rechazó el salto: {e}")

                if roi >= 2.5 or roi <= -1.2:
                    c.futures_create_order(symbol=o['s'], side=("SELL" if o['l']=="LONG" else "BUY"), type='MARKET', quantity=o['q'])
                    ops.remove(o)
                    print(f"✅ CIERRE EJECUTADO")
                    time.sleep(10); break

            if len(ops) < 1 and cap >= 10:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if cl[-2] > e9 and e9 > e27:
                        precio = float(c.get_symbol_ticker(symbol=m)['price'])
                        
                        # REDONDEOS PARA EVITAR ERROR 1111
                        if 'PEPE' in m: prec = 0
                        elif 'DOGE' in m: prec = 0
                        elif 'SOL' in m: prec = 2
                        else: prec = 1
                        
                        # USAMOS 75% PARA DEJAR MARGEN LIBRE Y QUE BINANCE DEJE SUBIR A 15X
                        qty = round((cap * 0.75 * 6) / precio, prec)
                        
                        if qty > 0:
                            c.futures_change_leverage(symbol=m, leverage=6)
                            c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                            ops.append({'s':m,'l':'LONG','p':precio,'q':qty, 'x':6})
                            print(f"🎯 ENTRADA 6X EN {m}")
                            break

            print(f"💰 Billetera: ${cap:.2f} | Ops: {len(ops)}", end='\r')

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)
        time.sleep(10)

if __name__ == "__main__": bot()
