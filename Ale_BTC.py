import os, time, redis, threading
from binance.client import Client

# --- 🧠 MEMORIA REDIS ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    c_i = 14.03 
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v213_seguro")
            return float(h) if h else c_i
        else: r.set("cap_v213_seguro", str(d))
    except: return c_i

def bot():
    c = Client()
    cap = g_m(leer=True)
    ops = []
    print(f"🦁 V213 ANTI-BANEO | RITMO DE AYER | ${cap}")

    while True:
        t_l = time.time()
        try:
            # --- 1. PEDIR TODO DE UN SOLO GOLPE (Evita el baneo) ---
            tickers = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            for o in ops[:]:
                p_a = tickers[o['s']]
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = (diff * 100 * o['x']) - (1.5 if o['x'] == 15 else 0.5) # Comisión estimada rápida

                # SALTO A 15X (A 0.5% como ayer)
                if roi > 0.5 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"🔥 POTENCIA 15X: {o['s']}")

                # CIERRES
                cierre = False
                if roi >= 6.0:
                    o['m_r'] = max(o.get('m_r', 0), roi)
                    o['tr'] = True
                
                if o.get('tr'):
                    if roi < (o['m_r'] - 0.5): cierre = True
                elif (o['be'] and roi <= 0.1) or roi <= -0.9:
                    cierre = True
                
                if cierre:
                    cap = cap * (1 + (roi/100))
                    g_m(d=cap)
                    ops.remove(o)
                    print(f"✅ CIERRE {o['s']} | NETO: {roi:.2f}%")

            # --- 2. GATILLO DE AYER (UNA SOLA OP) ---
            if len(ops) < 1:
                # Usamos las 5 monedas que mejor te funcionaban ayer
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, v_a, o_v, o_a = cl[-2], cl[-3], op[-2], op[-3]

                    if v > o_v and v > o_a and v > e9 and e9 > e27:
                        ops.append({'s':m,'l':'LONG','p':tickers[m],'x':5,'be':False})
                        print(f"🎯 DISPARO LONG: {m}")
                        break 
                    if v < o_v and v < o_a and v < e9 and e9 < e27:
                        ops.append({'s':m,'l':'SHORT','p':tickers[m],'x':5,'be':False})
                        print(f"🎯 DISPARO SHORT: {m}")
                        break 

            print(f"💰 ${cap:.2f} | Activa: {len(ops)} | {time.strftime('%H:%M:%S')}", end='\r')
        
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10) # Si hay error, esperamos para que Binance se calme

        # --- 3. EL RITMO PERFECTO ---
        # 4 a 6 segundos es el punto dulce para no ser baneado
        time.sleep(max(2, 5 - (time.time() - t_l)))

if __name__ == "__main__": bot()
