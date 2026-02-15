import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client

# --- 🌐 SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 MEMORIA CON LÓGICA DE RACHA ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None

def g_m(leer=False, d=None):
    c_i = 12.36 # Tu saldo actual según el último log
    if not r: return c_i
    try:
        if leer:
            h = r.get("saldo_eterno_ale")
            return float(h) if h else c_i
        else:
            # Guardamos el saldo previo para saber si venimos perdiendo
            actual = r.get("saldo_eterno_ale")
            if actual: r.set("saldo_previo", actual)
            r.set("saldo_eterno_ale", str(d))
    except: return c_i

# --- 🚀 MOTOR V243 (Cruce de Recuperación) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(); cap = g_m(leer=True); ops = []
    
    # Verificamos si venimos de pérdida
    saldo_p = float(r.get("saldo_previo") or cap) if r else cap
    en_perdida = cap < saldo_p
    
    print(f"🦁 V243 MATEMÁTICA | SALDO: ${cap:.2f} | MODO: {'RECUPERACIÓN' if en_perdida else 'ESTÁNDAR'}")

    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = (diff * 100 * o['x']) - (0.12 * o['x'])
                
                # --- 📉 LÓGICA PARA SUBIR EL 15X (Solo si la matemática da) ---
                if o['x'] == 5 and roi > 0.45:
                    k = c.get_klines(symbol=o['s'], interval='1m', limit=10)
                    cuerpos = [abs(float(x[4]) - float(x[1])) for x in k]
                    avg_cuerpo = sum(cuerpos) / len(cuerpos)
                    cuerpo_actual = abs(float(k[-1][4]) - float(k[-1][1]))
                    
                    # Solo sube si la vela actual es un 50% más fuerte que el promedio
                    if cuerpo_actual > (avg_cuerpo * 1.5):
                        o['x'] = 15; o['be'] = True
                        print(f"🔥 MATEMÁTICA CONFIRMADA: Subiendo a 15x en {o['s']}")

                # Cierre con protección (Si venimos perdiendo, el stop es más corto)
                stop_loss = -0.9 if en_perdida else -1.2
                if (o['be'] and roi <= 0.1) or roi >= 10.0 or roi <= stop_loss:
                    n_c = cap * (1 + (roi/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"✅ CIERRE LÓGICO | SALDO ACTUALIZADO: ${cap:.2f}")

            if len(ops) < 2:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if any(x['s'] == m for x in ops): continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # Libro de Velas: Acción de precio
                    v = k[-2]; op_v, cl_v = float(v[1]), float(v[4])
                    
                    # Si venimos perdiendo, exigimos que el cruce de EMAs sea más amplio
                    separacion = abs(e9 - e27) / e27
                    exigencia = 0.0008 if en_perdida else 0.0005

                    if e9 > e27 and cl_v > op_v and separacion > exigencia:
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':5,'be':False})
                        print(f"🎯 DISPARO ESTRATÉGICO 5x: {m}")
                        break
                    if e9 < e27 and cl_v < op_v and separacion > exigencia:
                        ops.append({'s':m,'l':'SHORT','p':cl[-1],'x':5,'be':False})
                        print(f"🎯 DISPARO ESTRATÉGICO 5x: {m}")
                        break

            print(f"💰 ${cap:.2f} | Memoria: {'PERDIDA' if en_perdida else 'OK'} | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(5)
        time.sleep(max(1, 8 - (time.time() - t_l)))

if __name__ == "__main__": bot()
