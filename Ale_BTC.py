import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 7.99) if r else 7.99
    print(f"🧠 V800 CEREBRO ANALÍTICO | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE POSICIÓN (Si el análisis falla, salimos y aprendemos)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])

                if roi <= -1.1 or roi >= 7.0:
                    cap *= (1 + (roi/100))
                    if r:
                        r.set("saldo_eterno_ale", str(cap))
                        # EL ANÁLISIS: Si perdimos, guardamos que la dirección era ERRÓNEA en este precio
                        if roi < 0:
                            r.set(f"error_{o['s']}_{o['l']}", str(p_a), ex=300) 
                    
                    ops.remove(o)
                    print(f"✅ CIERRE ANALIZADO: {o['s']} | Saldo: ${cap:.2f}")

            # 2. ENTRADA CON CRUCE DE FALLOSAnterior
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=15)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    p_ahora = float(c.get_symbol_ticker(symbol=m)['price'])
                    
                    # --- EL RAZONAMIENTO ---
                    # 1. ¿Ya intenté este movimiento y falló hace poco?
                    intento_fallido = r.get(f"error_{m}_LONG") if e9 > e27 else r.get(f"error_{m}_SHORT")
                    
                    if intento_fallido:
                        # Si el precio sigue cerca de donde fallamos, el programa RAZONA que la señal es falsa
                        if abs(p_ahora - float(intento_fallido))/float(intento_fallido) < 0.003:
                            continue 

                    # 2. Análisis del Libro: ¿La vela tiene volumen y dirección?
                    v = k[-2]
                    op_v, cl_v = float(v[1]), float(v[4])
                    fuerza = abs(cl_v - op_v) / op_v * 100
                    
                    # 3. Disparo solo si la EMA y la vela confirman que salimos del ruido
                    if e9 > e27 and cl_v > op_v and fuerza > 0.08:
                        ops.append({'s':m, 'l':'LONG', 'p':p_ahora, 'x':15})
                        print(f"🚀 ANÁLISIS OK: Entrando LONG en {m}")
                        break
                    
                    if e9 < e27 and cl_v < op_v and fuerza > 0.08:
                        ops.append({'s':m, 'l':'SHORT', 'p':p_ahora, 'x':15})
                        print(f"🔻 ANÁLISIS OK: Entrando SHORT en {m}")
                        break

            print(f"💰 ${cap:.2f} | Analizando fallos previos... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(2)
        time.sleep(max(1, 5 - (time.time() - t_l)))

if __name__ == "__main__": bot()
