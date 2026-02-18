import os, time, redis, json, threading
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
    c_i = 17.66  
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v146_sim")
            return float(h) if h else c_i
        else: r.set("cap_v146_sim", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V146 SIMULACIÓN (BUCLE INFINITO) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client() # Para simulación no necesita API Key si solo lee precios
    cap = g_m(leer=True)
    ops = []
    print(f"🐊 V146 SIMULACIÓN | BUSCADOR ACTIVO | ${cap}")

    while True:
        t_l = time.time()
        roi_vivo = 0.0
        ganancia_vivo_usd = 0.0
        
        try:
            # 1. GESTIÓN DE OPERACIONES ABIERTAS
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI Neto con comisión de entrada -0.90%
                roi = (diff * 100 * o['x']) - 0.90
                roi_vivo = roi
                ganancia_vivo_usd = cap * (roi / 100)
                
                # SALTO A 15X (Al 2.0%)
                if roi >= 2.0 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.5 
                    print(f"\n🔥 SALTO A 15X: {o['s']} | Entró a: {o['p']}")

                # ESCALADOR INTERCALADO (A 0.5% DE DISTANCIA)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0: n_p = 24.5
                    elif roi >= 20.0: n_p = 19.5
                    elif roi >= 15.0: n_p = 14.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 8.0:  n_p = 7.5
                    elif roi >= 6.0:  n_p = 5.5
                    elif roi >= 4.0:  n_p = 3.5
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ ESCALADOR: {o['s']} | Piso: {o['piso']}% | Actual: ${ganancia_vivo_usd:.2f}")

                    # CIERRE POR PISO
                    if roi < o['piso']:
                        cap = cap + ganancia_vivo_usd
                        g_m(d=cap)
                        print(f"\n✅ VENDIDO (Take Profit): {o['s']}")
                        print(f"   💰 GANANCIA: +${ganancia_vivo_usd:.2f} | ROI: {roi:.2f}%")
                        print(f"   📍 Entró: {o['p']} | Salió: {p_a}")
                        ops.remove(o) # <--- AQUÍ LIBERA EL ESPACIO PARA BUSCAR OTRA
                        continue

                # STOP LOSS (-2.5%)
                if not o['be'] and roi <= -2.5:
                    cap = cap + ganancia_vivo_usd
                    g_m(d=cap)
                    print(f"\n⚠️ VENDIDO (Stop Loss): {o['s']}")
                    print(f"   📉 PÉRDIDA: ${ganancia_vivo_usd:.2f} | Salió a: {p_a}")
                    ops.remove(o) # <--- AQUÍ LIBERA EL ESPACIO PARA BUSCAR OTRA

            # 2. BUSCADOR DE NUEVAS OPORTUNIDADES (Solo si no hay nada abierto)
            if len(ops) < 1:
                # Prioridad Ale: SOL, XRP, BNB
                for m in ['SOLUSDT', 'XRPUSDT', 'BNBUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], float(k[-2][1])

                    # Estrategia: Cruce y Acción de Precio
                    if v > o_v and v > e9 and e9 > e27:
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':5,'be':False, 'piso': -2.5})
                        print(f"\n🎯 NUEVA ENTRADA LONG: {m} a {cl[-1]}")
                        break
                    if v < o_v and v < e9 and e9 < e27:
                        ops.append({'s':m,'l':'SHORT','p':cl[-1],'x':5,'be':False, 'piso': -2.5})
                        print(f"\n🎯 NUEVA ENTRADA SHORT: {m} a {cl[-1]}")
                        break

            # MONITOR
            mon = f" | {ops[0]['s']}: ${ganancia_vivo_usd:.2f} ({roi_vivo:.2f}%)" if len(ops) > 0 else " | 🔎 Buscando SOL, XRP o BNB..."
            print(f"💰 Saldo: ${cap:.2f}{mon} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except Exception as e:
            time.sleep(5)
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
