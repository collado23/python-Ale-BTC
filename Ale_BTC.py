import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None 
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 7.99) if r else 7.99
    print(f"🧠 V900 CEREBRO ANALÍTICO | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE POSICIÓN (Si falla, se analiza por qué)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])

                # RAZONAMIENTO: Si el ROI es negativo y la vela del libro nos da la espalda, cerramos.
                k = c.get_klines(symbol=o['s'], interval='1m', limit=2)
                v_act = k[-1]; cl_v, op_v = float(v_act[4]), float(v_act[1])
                cambio_fuerza = (o['l'] == 'LONG' and cl_v < op_v) or (o['l'] == 'SHORT' and cl_v > op_v)

                if (cambio_fuerza and roi < -0.4) or roi >= 6.0 or roi <= -1.2:
                    cap *= (1 + (roi/100))
                    if r:
                        r.set("saldo_eterno_ale", str(cap))
                        # EL PENSAMIENTO: Si perdimos, guardamos el ERROR para no repetirlo
                        if roi < 0:
                            # Guardamos: "En SOL, el SHORT a este precio NO SIRVE"
                            r.set(f"error_{o['s']}_{o['l']}", str(p_a), ex=600)
                    
                    ops.remove(o)
                    print(f"✅ CIERRE ANALIZADO: {o['s']} | Resultado: {'GANÓ' if roi>0 else 'PERDIÓ'}")

            # 2. ENTRADA CON CRUCE DE ERRORES (Acá es donde el programa PIENSA)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    # Miramos qué dicen las EMAs (El mapa)
                    k = c.get_klines(symbol=m, interval='1m', limit=20)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    p_ahora = float(c.get_symbol_ticker(symbol=m)['price'])
                    dir_deseada = "LONG" if e9 > e27 else "SHORT"

                    # --- EL RAZONAMIENTO ---
                    # ¿Tengo un error guardado para esta dirección en esta moneda?
                    ultimo_error_precio = r.get(f"error_{m}_{dir_deseada}") if r else None
                    
                    if ultimo_error_precio:
                        diff = abs(p_ahora - float(ultimo_error_precio)) / float(ultimo_error_precio) * 100
                        if diff < 0.6: # Si el precio no se movió al menos 0.6%, el programa RECHAZA la entrada
                            continue 

                    # El Libro: ¿La vela es de poder (Marubozu)?
                    v = k[-2]; o_v, c_v = float(v[1]), float(v[4])
                    cuerpo = abs(c_v - o_v) / o_v * 100

                    # Solo dispara si la EMA dice una cosa, el LIBRO confirma y la MEMORIA no registra fallos cerca
                    if dir_deseada == "LONG" and c_v > o_v and cuerpo > 0.1:
                        ops.append({'s':m, 'l':'LONG', 'p':p_ahora, 'x':15})
                        print(f"🎯 DISPARO ANALIZADO: LONG en {m}")
                        break
                    
                    if dir_deseada == "SHORT" and c_v < o_v and cuerpo > 0.1:
                        ops.append({'s':m, 'l':'SHORT', 'p':p_ahora, 'x':15})
                        print(f"🎯 DISPARO ANALIZADO: SHORT en {m}")
                        break

            print(f"💰 ${cap:.2f} | Razonando fallos... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(2)
        time.sleep(max(1, 5 - (time.time() - t_l)))

if __name__ == "__main__": bot()
