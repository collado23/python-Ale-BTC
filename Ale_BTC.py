import os, time, redis, threading
from binance.client import Client

# --- 🧠 MEMORIA ESTRATÉGICA (No es caja de zapatos) ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 11.83)
    ops = []
    
    print(f"⚔️ V247 CONFLUENCIA REAL | SALDO: ${cap:.2f}")

    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE SALIDA (Lógica de Reacción)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']) * 100 * o['x']) - (0.12 * o['x'])

                # ¿Qué dice el libro mientras estamos adentro?
                k = c.get_klines(symbol=o['s'], interval='1m', limit=2)
                v_ahora = k[-1]; op_v, cl_v = float(v_ahora[1]), float(v_ahora[4])
                
                # Si el libro muestra debilidad (vela contraria), cerramos aunque falte para el stop
                if (o['l'] == 'LONG' and cl_v < op_v) or (o['l'] == 'SHORT' and cl_v > op_v):
                    if roi < -0.4: # Si ya viene mal y la vela cambia, afuera.
                        cap *= (1 + (roi/100))
                        r.set("saldo_eterno_ale", str(cap))
                        ops.remove(o)
                        print(f"⚠️ LIBRO AVISA CAMBIO: Cerrando para proteger ${cap:.2f}")

            # 2. ENTRADA POR CONFLUENCIA (EMAs + LIBRO)
            if len(ops) < 1: # Concentramos el capital en un solo tiro bueno
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    
                    # --- LAS EMAs (El Mapa) ---
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    distancia = abs(e9 - e27) / e27 * 100

                    # --- EL LIBRO DE VELAS (El Gatillo) ---
                    v = k[-2] # Última vela cerrada
                    op_v, hi_v, lo_v, cl_v = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl_v - op_v)
                    rango = hi_v - lo_v
                    # El libro exige: Cuerpo > 80% de la vela (Fuerza Marubozu)
                    vela_de_poder = cuerpo > (rango * 0.8)

                    # --- LA MEMORIA (El Filtro de Calidad) ---
                    # Si venimos perdiendo (cap < 12), exigimos que las EMAs estén bien separadas
                    exigencia_ema = 0.04 if cap < 12 else 0.02

                    # CRUCE DE LÓGICAS:
                    if e9 > e27 and cl_v > op_v and vela_de_poder and distancia > exigencia_ema:
                        ops.append({'s':m,'l':'LONG','p':float(c.get_symbol_ticker(symbol=m)['price']),'x':15,'be':True})
                        print(f"🎯 CONFLUENCIA LONG: EMAs separadas + Libro de Poder en {m}")
                        break
                    
                    if e9 < e27 and cl_v < op_v and vela_de_poder and distancia > exigencia_ema:
                        ops.append({'s':m,'l':'SHORT','p':float(c.get_symbol_ticker(symbol=m)['price']),'x':15,'be':True})
                        print(f"🎯 CONFLUENCIA SHORT: EMAs separadas + Libro de Poder en {m}")
                        break

            print(f"💰 ${cap:.2f} | EMAs + Libro: Buscando entrada perfecta... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(2)
        time.sleep(max(1, 5 - (time.time() - t_l)))

if __name__ == "__main__": bot()
