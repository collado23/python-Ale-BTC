import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None 
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 9.05) if r else 9.05
    print(f"🧠 V600 ANÁLISIS CRÍTICO | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. SI ESTAMOS ADENTRO: ¿Qué está pasando con la plata?
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])

                # RAZONAMIENTO DE SALIDA: No regalamos comisiones.
                # Si el ROI es negativo, solo salimos si el precio rompe el mínimo/máximo anterior (Stop Estructural)
                k = c.get_klines(symbol=o['s'], interval='1m', limit=3)
                v_act = k[-1]
                cl_v, op_v = float(v_act[4]), float(v_act[1])
                
                # Cerramos si hay pérdida real o si llegamos al objetivo
                if roi <= -1.2 or roi >= 7.0:
                    exito = "GANANCIA" if roi > 0 else "PÉRDIDA"
                    cap *= (1 + (roi/100))
                    if r: 
                        r.set("saldo_eterno_ale", str(cap))
                        # SI PERDIMOS, la memoria guarda un "Veto de Razonamiento"
                        if roi < 0: r.set(f"fallo_{o['s']}", str(p_a), ex=600) 
                    
                    ops.remove(o)
                    print(f"✅ {exito}: {o['s']} | Nuevo Saldo: ${cap:.2f}")

            # 2. ANÁLISIS DE ENTRADA (Pensar antes de actuar)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    # RAZONAMIENTO: Si fallamos recién en esta moneda, NO entramos 
                    # hasta que el precio esté LEJOS de donde perdimos.
                    precio_fallo = float(r.get(f"fallo_{m}") or 0) if r else 0
                    p_actual = float(c.get_symbol_ticker(symbol=m)['price'])
                    
                    if precio_fallo > 0 and abs(p_actual - precio_fallo)/precio_fallo < 0.005:
                        continue # El precio está en la misma zona de poronga de antes. Ignorar.

                    k = c.get_klines(symbol=m, interval='1m', limit=20)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # El Libro: Buscamos una vela que ENVUELVA a la anterior (Engulfing)
                    v1, v2 = k[-2], k[-1]
                    o1, c1 = float(v1[1]), float(v1[4])
                    o2, c2 = float(v2[1]), float(v2[4])

                    # ¿La vela actual tiene decisión real?
                    engulfing_long = c2 > o2 and c2 > max(o1, c1) and o2 < min(o1, c1)
                    engulfing_short = c2 < o2 and c2 < min(o1, c1) and o2 > max(o1, c1)

                    # CRUCE DE RAZONAMIENTO
                    if e9 > e27 and engulfing_long:
                        ops.append({'s':m, 'l':'LONG', 'p':p_actual, 'x':15})
                        print(f"🎯 RAZONADO: Engulfing Alcista en {m} (Fuera de zona de fallo)")
                        break
                    
                    if e9 < e27 and engulfing_short:
                        ops.append({'s':m, 'l':'SHORT', 'p':p_actual, 'x':15})
                        print(f"🎯 RAZONADO: Engulfing Bajista en {m} (Fuera de zona de fallo)")
                        break

            print(f"💰 ${cap:.2f} | Razonando zonas de precio... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(2)
        time.sleep(max(1, 6 - (time.time() - t_l)))

if __name__ == "__main__": bot()
