import os, time, redis, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 2. MEMORIA REDIS ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    if not r: return 15.0
    try:
        if leer:
            h = r.get("cap_v148_real"); return float(h) if h else 15.0
        else: r.set("cap_v148_real", str(d))
    except: return 15.0

# --- 🚀 3. MOTOR V148 COMPLETO ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # Buscador inteligente de llaves
    ak = os.getenv("BINANCE_APY_KEY") or os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
    as_ = os.getenv("BINANCE_APY_SECRET") or os.getenv("BINANCE_API_SECRET") or os.getenv("API_SECRET")
    
    if not ak or not as_:
        print("❌ ERROR: No se encuentran las llaves APY/SECRET en el hosting.")
        return

    c = Client(ak, as_)
    ops = []
    cap = g_m(leer=True)
    
    print(f"🦁 COCODRILO V148 ACTIVADO | CAPITAL: ${cap}")

    while True:
        t_l = time.time()
        try:
            # ACTUALIZAR SALDO REAL (Billetera de Futuros USDT)
            try:
                bal = c.futures_account_balance()
                cap = next((float(b['balance']) for b in bal if b['asset'] == 'USDT'), cap)
                g_m(d=cap)
            except:
                pass

            # --- GESTIÓN DE CIERRES ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                # Salto de apalancamiento a 15x si va ganando
                if roi > 0.2 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    try: c.futures_change_leverage(symbol=o['s'], leverage=15)
                    except: pass

                # Cierres (Take Profit 1.5% o Stop Loss -0.9%)
                if (o['be'] and roi <= 0.05) or roi >= 1.5 or roi <= -0.9:
                    side = "SELL" if o['l'] == "LONG" else "BUY"
                    c.futures_create_order(symbol=o['s'], side=side, type='MARKET', quantity=o['q'])
                    ops.remove(o)
                    print(f"✅ CIERRE EXITOSO | ROI: {roi:.2f}% | Esperando 5s...")
                    time.sleep(5) 
                    break

            # --- BUSCADOR DE ENTRADAS ---
            # Solo monedas seguras para evitar el error 1121
            monedas = ['PEPEUSDT', 'DOGEUSDT', 'SOLUSDT', 'SHIBUSDT', 'BONKUSDT']
            
            if len(ops) < 2 and cap >= 10:
                for m in monedas:
                    if any(x['s'] == m for x in ops): continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op_p = [float(x[1]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], op_p[-2]

                    # Lógica Long
                    if v > o_v and v > e9 and e9 > e27:
                        precio = cl[-1]
                        # USAMOS EL 80% (0.8) PARA EVITAR ERROR DE MARGEN
                        qty = round((cap * 0.8 * 5) / precio, 0)
                        if qty > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                            ops.append({'s':m,'l':'LONG','p':precio,'x':5,'q':qty,'be':False})
                            print(f"🎯 COMPRA REAL: {m} | Qty: {qty}")
                            break
                        
                    # Lógica Short
                    if v < o_v and v < e9 and e9 < e27:
                        precio = cl[-1]
                        qty = round((cap * 0.8 * 5) / precio, 0)
                        if qty > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side='SELL', type='MARKET', quantity=qty)
                            ops.append({'s':m,'l':'SHORT','p':precio,'x':5,'q':qty,'be':False})
                            print(f"🎯 VENTA REAL: {m} | Qty: {qty}")
                            break

            print(f"💰 REAL: ${cap:.2f} | Activas: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')

        except Exception as e:
            # Si sale el 1121 aquí sabremos qué moneda fue
            print(f"⚠️ Log Error: {e}")
            time.sleep(10)
        
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__":
    bot()
