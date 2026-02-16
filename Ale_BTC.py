import os, time, redis, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    ak = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_APY_KEY")
    as_ = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_APY_SECRET")
    c = Client(ak, as_)
    
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT']
    ops = []

    # --- SALDO FORZADO A $30 PARA ARRANCAR ---
    cap = 30.0 
    print(f"💰 V2700 - SALDO INICIAL: ${cap:.2f} - MODO 15X")

    while True:
        try:
            # 1. ACTUALIZAR SALDO REAL DE LA BILLETERA
            bal = c.futures_account_balance()
            actual_balance = next((float(b['balance']) for b in bal if b['asset'] == 'USDT'), 0.0)
            
            # Si el balance real es mayor a nuestro cap inicial, usamos el real
            if actual_balance > cap: cap = actual_balance

            # 2. GESTIÓN DE CIERRES
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * 15) - 2.4
                
                # Cierre por profit del Libro (7.5%) o Stop (1.8%)
                if roi >= 7.5 or roi <= -1.8:
                    side_c = "SELL" if o['l']=="LONG" else "BUY"
                    c.futures_create_order(symbol=o['s'], side=side_c, type='MARKET', quantity=o['q'])
                    ops.remove(o)
                    print(f"✅ CIERRE LIBRO EJECUTADO. ROI: {roi:.2f}%")

            # 3. ENTRADAS CON MEDIDAS DEL LIBRO
            if len(ops) < 1:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=20)
                    v = k[-2] # Vela anterior cerrada
                    
                    ap, hi, lo, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl - ap) or 0.00000001
                    m_sup, m_inf = hi - max(cl, ap), min(cl, ap) - lo
                    
                    # Distancia del Pico (Agotamiento)
                    precios = [float(x[4]) for x in k[:-2]]
                    distancia = (max(precios) - min(precios)) / min(precios) * 100

                    # Medidas del Martillo (2.2x el cuerpo)
                    es_m = (m_inf > cuerpo * 2.2) and (m_sup < cuerpo * 0.7)
                    es_i = (m_sup > cuerpo * 2.2) and (m_inf < cuerpo * 0.7)

                    # Solo si la vela tiene "carne" y viene de un pico largo
                    if distancia > 0.38 and ((hi-lo)/lo*100) > 0.12:
                        p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                        
                        # LONG: Martillo en piso + Confirmación
                        if es_m and cl < max(precios) and p_act > hi:
                            qty = round((cap * 0.92 * 15) / p_act, 0 if 'PEPE' in m or 'DOGE' in m else 2)
                            c.futures_change_leverage(symbol=m, leverage=15)
                            c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                            ops.append({'s':m, 'l':'LONG', 'p':p_act, 'q':qty})
                            print(f"🔨 MARTILLO: {m} (Distancia: {distancia:.2f}%) Entrando con balance ${cap}")
                            break

                        # SHORT: Martillo Invertido en techo + Confirmación
                        if es_i and cl > min(precios) and p_act < lo:
                            qty = round((cap * 0.92 * 15) / p_act, 0 if 'PEPE' in m or 'DOGE' in m else 2)
                            c.futures_change_leverage(symbol=m, leverage=15)
                            c.futures_create_order(symbol=m, side='SELL', type='MARKET', quantity=qty)
                            ops.append({'s':m, 'l':'SHORT', 'p':p_act, 'q':qty})
                            print(f"🛸 ESTRELLA: {m} (Distancia: {distancia:.2f}%) Entrando con balance ${cap}")
                            break

            print(f"💰 FONDO: ${cap:.2f} | Buscando picos largos (>0.38%)... ", end='\r')

        except Exception as e:
            print(f"⚠️ Log: {e}")
            time.sleep(5)
        time.sleep(3)

if __name__ == "__main__": bot()
