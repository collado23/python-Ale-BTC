import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD (Tu original) ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 2. CRUCE DE MEMORIA (Persistencia Real) ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None

def get_cap():
    # El bot busca el saldo guardado por el programa anterior. 
    # Si no hay nada (primera vez), usa 12.85 que es tu saldo actual.
    default = 12.85
    if not r: return default
    try:
        val = r.get("saldo_eterno_ale")
        return float(val) if val else default
    except: return default

def save_cap(valor):
    if r: r.set("saldo_eterno_ale", str(valor))

# --- 🚀 3. MOTOR CRUZADO (Tu V143 + Lógica de Velas) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client()
    cap = get_cap() # Carga la memoria
    ops = []
    
    print(f"🦁 V241 CRUCE FINAL | MEMORIA ACTIVA | SALDO: ${cap}")

    while True:
        t_l = time.time()
        try:
            # --- LÓGICA DE GESTIÓN (Tu código con esteroides) ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI Neto: Descontamos la comisión de Binance (0.12% aprox en 15x)
                roi = (diff * 100 * o['x']) - (0.12 * o['x'])
                
                # LÓGICA DE ESCALADA (CUÁNDO LA SUBE):
                # Solo pasa a 15x si hay ROI positivo y el Libro confirma fuerza de vela
                if roi > 0.3 and o['x'] == 5:
                    k = c.get_klines(symbol=o['s'], interval='1m', limit=2)
                    v = k[-1]; op_v, cl_v = float(v[1]), float(v[4])
                    # Confirmación por color de vela
                    if (o['l'] == 'LONG' and cl_v > op_v) or (o['l'] == 'SHORT' and cl_v < op_v):
                        o['x'] = 15; o['be'] = True
                        print(f"🔥 LA SUBE A 15X: {o['s']} confirmada por Libro")

                # LÓGICA DE CIERRE (Tu stop y profit + Seguridad)
                if (o['be'] and roi <= 0.08) or roi >= 12.0 or roi <= -1.2:
                    cap *= (1 + (roi/100))
                    save_cap(cap) # GUARDA LA INFO EN REDIS AL INSTANTE
                    ops.remove(o)
                    print(f"✅ VENTA FINALIZADA | SALDO EN MEMORIA: ${cap:.2f}")

            # --- LÓGICA DE ENTRADA (CRUCE DE TU ESTRATEGIA + LIBRO) ---
            if len(ops) < 2:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'BTCUSDT']:
                    if any(x['s'] == m for x in ops): continue
                    
                    # 1. Tu lógica de EMAs
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # 2. Lógica del Libro (Vela Japonesa de Poder)
                    v_u = k[-2] # Última cerrada
                    op_u, hi_u, lo_u, cl_u = float(v_u[1]), float(v_u[2]), float(v_u[3]), float(v_u[4])
                    cuerpo = abs(cl_u - op_u)
                    rango = hi_u - lo_u
                    
                    # El libro dice: Solo entrar si el cuerpo es > 70% de la vela (sin mechas largas)
                    es_fuerte = cuerpo > (rango * 0.7) and (cuerpo/op_u) > 0.0006

                    if es_fuerte:
                        if e9 > e27 and cl_u > op_u: # LONG
                            ops.append({'s':m,'l':'LONG','p':float(c.get_symbol_ticker(symbol=m)['price']),'x':5,'be':False})
                            print(f"🎯 DISPARO LONG (Libro + EMAs): {m}")
                            break
                        if e9 < e27 and cl_u < op_u: # SHORT
                            ops.append({'s':m,'l':'SHORT','p':float(c.get_symbol_ticker(symbol=m)['price']),'x':5,'be':False})
                            print(f"🎯 DISPARO SHORT (Libro + EMAs): {m}")
                            break

            print(f"💰 ${cap:.2f} | Memoria: Guardando... | {time.strftime('%H:%M:%S')}", end='\r')
        except: 
            time.sleep(5)
        
        time.sleep(max(1, 8 - (time.time() - t_l)))

if __name__ == "__main__": bot()
