import os, time, redis, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- MEMORIA FIEL ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    if not r: return None
    try:
        if leer:
            v = r.get("mem_v163_final_6")
            return eval(v) if v else None
        else: r.set("mem_v163_final_6", str(d))
    except: return None

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    ak = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_APY_KEY")
    as_ = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_APY_SECRET")
    c = Client(ak, as_)
    
    datos = g_m(leer=True) or {"ops": []}
    ops = datos["ops"]
    # TUS 6 MONEDAS
    monedas = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT']

    print(f"🚀 V163 - TUS 6 MONEDAS - MODO 5X -> 15X")

    while True:
        try:
            bal = c.futures_account_balance()
            cap = next((float(b['balance']) for b in bal if b['asset'] == 'USDT'), 0.0)
            g_m(d={"ops": ops})

            # --- LÓGICA DE SEGUIMIENTO Y SALTO ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                # TU SALTO MÁGICO A 15X
                if roi > 0.2 and o['x'] == 5:
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'] = 15
                        print(f"🔥 OPORTUNIDAD: Subiendo a 15x en {o['s']}")
                    except: pass

                # CIERRES (Profit 2.5% o Stop -1.2%)
                if roi >= 2.5 or roi <= -1.2:
                    c.futures_create_order(symbol=o['s'], side=("SELL" if o['l']=="LONG" else "BUY"), type='MARKET', quantity=o['q'])
                    ops.remove(o)
                    print(f"✅ CIERRE EJECUTADO")
                    time.sleep(10); break

            # --- ENTRADA (Analiza las 6, entra en 1) ---
            if len(ops) < 1 and cap >= 12:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if cl[-2] > e9 and e9 > e27:
                        precio = float(c.get_symbol_ticker(symbol=m)['price'])
                        # Usamos el 90% para que la orden sea lo más grande posible y pase el filtro
                        qty = round((cap * 0.90 * 5) / precio, 3 if 'BTC' in m or 'ETH' in m else 1)
                        
                        if qty > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                            ops.append({'s':m,'l':'LONG','p':precio,'q':qty, 'x':5})
                            print(f"🎯 ENTRADA 5X EN {m}")
                            break

            print(f"💰 REAL: ${cap:.2f} | Activas: {len(ops)} | 5x/15x", end='\r')

        except Exception as e:
            print(f"⚠️ Log: {e}")
            time.sleep(10)
        time.sleep(10)

if __name__ == "__main__": bot()
