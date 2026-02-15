import os, time, redis
from binance.client import Client

# --- 🧠 MEMORIA CONECTADA (Sin errores) ---
try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
except:
    r = None

def get_mem(k, d):
    if r:
        try:
            v = r.get(k)
            return v.decode() if v else d
        except: return d
    return d

# --- 🚀 MOTOR DE RAZONAMIENTO ---
def bot():
    c = Client()
    cap = float(get_mem("saldo_eterno_ale", 10.66))
    last_res = get_mem("ultimo_resultado", "WIN") # Lee si la última fue pérdida
    
    print(f"🧠 V260 RAZONANDO | SALDO: ${cap:.2f} | MODO: {last_res}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE SALIDA (No regalar comisiones)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])

                # Si el Libro dice que la vela cambió, pero el ROI es muy bajo, aguantamos un poco
                k = c.get_klines(symbol=o['s'], interval='1m', limit=2)
                v_act = k[-1]; cl_v, op_v = float(v_act[4]), float(v_act[1])
                cambio = (o['l'] == 'LONG' and cl_v < op_v) or (o['l'] == 'SHORT' and cl_v > op_v)

                if (cambio and roi < -0.5) or roi >= 8.0 or roi <= -1.2:
                    res = "WIN" if roi > 0 else "LOSS"
                    cap *= (1 + (roi/100))
                    if r:
                        r.set("saldo_eterno_ale", str(cap))
                        r.set("ultimo_resultado", res)
                        if res == "LOSS": r.set(f"bloqueo_{o['s']}", "1", ex=480) # Castigo de 8 min
                    ops.remove(o)
                    print(f"✅ CIERRE {res} | SALDO: ${cap:.2f}")

            # 2. ENTRADA CON LÓGICA DE ESCARMIENTO
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if r and r.get(f"bloqueo_{m}"): continue # No entrar donde perdimos recién

                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # El Libro de Velas (Confirmación de Dirección)
                    v_c = k[-2]; o_c, c_c = float(v_c[1]), float(v_c[4])
                    fuerza = abs(c_c - o_c) / o_c * 100

                    # --- EL RAZONAMIENTO ---
                    # Si venimos de pérdida, la separación de EMAs tiene que ser mayor (0.06%)
                    # y la vela del libro tiene que ser "gigante" (0.15%)
                    min_ema = 0.06 if last_res == "LOSS" else 0.03
                    min_vela = 0.15 if last_res == "LOSS" else 0.08
                    
                    separacion = abs(e9 - e27) / e27 * 100

                    if e9 > e27 and c_c > o_c and separacion > min_ema and fuerza > min_vela:
                        ops.append({'s':m, 'l':'LONG', 'p':float(c.get_symbol_ticker(symbol=m)['price']), 'x':15})
                        print(f"🎯 DISPARO PENSADO LONG: {m}")
                        break
                    
                    if e9 < e27 and c_c < o_c and separacion > min_ema and fuerza > min_vela:
                        ops.append({'s':m, 'l':'SHORT', 'p':float(c.get_symbol_ticker(symbol=m)['price']), 'x':15})
                        print(f"🎯 DISPARO PENSADO SHORT: {m}")
                        break

            print(f"💰 ${cap:.2f} | {last_res} | Razonando... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(2)
        time.sleep(max(1, 5 - (time.time() - t_l)))

if __name__ == "__main__": bot()
