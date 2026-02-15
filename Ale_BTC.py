import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 9.05) if r else 9.05
    print(f"🧠 V700 RAZONAMIENTO DINÁMICO | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN ACTIVA: ¿Sigue teniendo sentido la operación?
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])

                # RAZONAMIENTO DE SALIDA: Si en 3 minutos no hubo ganancia, el mercado está lateral. AFUERA.
                tiempo_adentro = time.time() - o['t']
                if (tiempo_adentro > 180 and roi < 0.2) or roi >= 7.0 or roi <= -1.2:
                    cap *= (1 + (roi/100))
                    if r: r.set("saldo_eterno_ale", str(cap))
                    ops.remove(o)
                    print(f"🔄 CIERRE LÓGICO: {o['s']} | Saldo: ${cap:.2f}")

            # 2. ENTRADA POR ROMPIMIENTO (El programa analiza la intención)
            if len(ops) < 2: # Volvemos a permitir 2 operaciones para no estar quietos
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if any(x['s'] == m for x in ops): continue

                    k = c.get_klines(symbol=m, interval='1m', limit=10)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    v_previa = k[-2] # Vela de confirmación
                    v_actual = k[-1] # Vela de disparo
                    
                    low_p = float(v_previa[3])
                    high_p = float(v_previa[2])
                    p_ahora = float(v_actual[4])

                    # RAZONAMIENTO MATEMÁTICO:
                    # Para LONG: EMA9 > EMA27 Y el precio actual superó el MÁXIMO de la vela anterior.
                    # Para SHORT: EMA9 < EMA27 Y el precio actual rompió el MÍNIMO de la vela anterior.
                    
                    if e9 > e27 and p_ahora > high_p:
                        ops.append({'s':m, 'l':'LONG', 'p':p_ahora, 'x':15, 't':time.time()})
                        print(f"🚀 RAZONADO LONG: {m} rompiendo máximos.")
                        break
                    
                    if e9 < e27 and p_ahora < low_p:
                        ops.append({'s':m, 'l':'SHORT', 'p':p_ahora, 'x':15, 't':time.time()})
                        print(f"🔻 RAZONADO SHORT: {m} rompiendo mínimos.")
                        break

            print(f"💰 ${cap:.2f} | Analizando fuerza real... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(2)
        time.sleep(max(1, 4 - (time.time() - t_l)))

if __name__ == "__main__": bot()
