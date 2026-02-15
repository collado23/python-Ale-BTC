import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from binance.client import Client

# --- 🌐 SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # Buscador de llaves
    ak = os.getenv("BINANCE_APY_KEY") or os.getenv("BINANCE_API_KEY")
    as_ = os.getenv("BINANCE_APY_SECRET") or os.getenv("BINANCE_API_SECRET")
    
    if not ak or not as_:
        print("❌ ERROR: Faltan las llaves en el hosting.")
        return

    c = Client(ak, as_)
    ops = []
    
    # LISTA BLINDADA (Solo estas, escritas perfecto)
    monedas_validas = ['PEPEUSDT', 'DOGEUSDT', 'SOLUSDT', 'SHIBUSDT']

    print(f"🚀 INICIANDO V148.1 - LIMPIEZA DE ERRORES")

    while True:
        try:
            # ACTUALIZAR SALDO REAL
            bal = c.futures_account_balance()
            cap = next((float(b['balance']) for b in bal if b['asset'] == 'USDT'), 0.0)

            # --- GESTIÓN DE CIERRES ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                if roi >= 1.5 or roi <= -0.9:
                    side = "SELL" if o['l'] == "LONG" else "BUY"
                    c.futures_create_order(symbol=o['s'], side=side, type='MARKET', quantity=o['q'])
                    ops.remove(o)
                    print(f"✅ CIERRE EXITOSO. Esperando 5s...")
                    time.sleep(5)
                    break

            # --- ENTRADAS (USANDO EL 80% PARA EL MARGEN) ---
            if len(ops) < 2 and cap >= 10:
                for m in monedas_validas:
                    if any(x['s'] == m for x in ops): continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if cl[-2] > e9 and e9 > e27: # Señal Long
                        precio = cl[-1]
                        qty = round((cap * 0.8 * 5) / precio, 0)
                        if qty > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                            ops.append({'s':m,'l':'LONG','p':precio,'x':5,'q':qty})
                            print(f"🎯 ENTRADA REAL EN {m}")
                            break

            print(f"💰 REAL: ${cap:.2f} | Activas: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')

        except Exception as e:
            # Esto atrapará el error 1121 y nos dirá qué está pasando
            print(f"⚠️ Aviso: {e}")
            time.sleep(10)
        
        time.sleep(10)

if __name__ == "__main__":
    bot()
