import os, time, redis
from binance.client import Client

# --- 🧠 EL CEREBRO (No es una caja de zapatos) ---
try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
except:
    r = None

def bot():
    c = Client()
    # Recuperamos el saldo y el estado de la última batalla
    cap = float(r.get("saldo_eterno_ale") or 10.66) if r else 10.66
    last_res = r.get("resultado_anterior") or "WIN" # Por defecto asumimos WIN
    
    print(f"🧠 V255 RAZONAMIENTO ACTIVO | SALDO: ${cap:.2f} | MODO: {last_res}")

    ops = []
    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])

                # --- RAZONAMIENTO DE SALIDA ---
                # Si estamos en 15x y el ROI es positivo, no dejamos que se vuelva pérdida
                if o['x'] == 15 and roi > 0.5:
                    o['sl'] = 0.1 # Ponemos un stop en ganancia (Break Even)

                if roi <= o.get('sl', -1.1) or roi >= 8.0:
                    res_final = "WIN" if roi > 0 else "LOSS"
                    cap *= (1 + (roi/100))
                    
                    if r:
                        r.set("saldo_eterno_ale", str(cap))
                        r.set("resultado_anterior", res_final)
                        if res_final == "LOSS":
                            r.set(f"enfriar_{o['s']}", "1", ex=600) # 10 min de castigo a la moneda
                    
                    ops.remove(o)
                    print(f"✅ {res_final} | NUEVO SALDO: ${cap:.2f}")

            # --- RAZONAMIENTO DE ENTRADA (Cruce de EMAs + Libro de Poder) ---
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if r and r.get(f"enfriar_{m}"): continue # No tropezar con la misma piedra

                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # El Libro: Analizamos las últimas 3 velas para ver TENDENCIA REAL
                    v1, v2 = k[-2], k[-1]
                    cuerpo_v1 = float(v1[4]) - float(v1[1])
                    cuerpo_v2 = float(v2[4]) - float(v2[1])

                    # --- EL RAZONAMIENTO MATEMÁTICO ---
                    # Si venimos de LOSS, el bot se vuelve un "Francotirador"
                    # Exige que las EMAs estén más separadas y que la vela sea un 0.2% del precio
                    filtro_recuperacion = 1.8 if last_res == b"LOSS" else 1.0
                    distancia_minima = 0.04 * filtro_recuperacion
                    separacion = abs(e9 - e27) / e27 * 100

                    # ¿Hay fuerza real en la dirección de las EMAs?
                    if e9 > e27 and cuerpo_v1 > 0 and cuerpo_v2 > 0 and separacion > distancia_minima:
                        ops.append({'s':m, 'l':'LONG', 'p':float(v2[4]), 'x':15})
                        print(f"🎯 DISPARO PENSADO (LONG): {m} | Filtro: x{filtro_recuperacion}")
                        break
                    
                    if e9 < e27 and cuerpo_v1 < 0 and cuerpo_v2 < 0 and separacion > distancia_minima:
                        ops.append({'s':m, 'l':'SHORT', 'p':float(v2[4]), 'x':15})
                        print(f"🎯 DISPARO PENSADO (SHORT): {m} | Filtro: x{filtro_recuperacion}")
                        break

            print(f"💰 ${cap:.2f} | Razonando mercado... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(2)
        time.sleep(max(1, 5 - (time.time() - t_l)))

if __name__ == "__main__": bot()
