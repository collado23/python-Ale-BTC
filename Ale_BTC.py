import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 2.96) if r else 2.96
    print(f"👁️ V1300 PICOS LARGOS | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE POSICIÓN
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])

                if roi >= 6.0 or roi <= -1.2:
                    cap *= (1 + (roi/100))
                    if r: r.set("saldo_eterno_ale", str(cap))
                    ops.remove(o)
                    print(f"✅ CIERRE: {o['s']} | Saldo: ${cap:.2f}")

            # 2. ANÁLISIS DE PICO LARGO (Razonamiento de Amplitud)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=10)
                    
                    precios = [float(x[4]) for x in k]
                    max_p = max(precios[:-1])
                    min_p = min(precios[:-1])
                    p_actual = float(k[-1][4])
                    
                    # --- RAZONAMIENTO DE "PICO LARGO" ---
                    # Medimos qué tan largo fue el movimiento antes del pico
                    amplitud = (max_p - min_p) / min_p * 100
                    
                    # FILTRO: Si el movimiento total fue menor al 0.35%, es un pico cortito (RUIDO)
                    if amplitud < 0.35:
                        continue

                    v_pre = k[-2]
                    v_act = k[-1]
                    c_act, o_act = float(v_act[4]), float(v_act[1])
                    c_pre, o_pre = float(v_pre[4]), float(v_pre[1])

                    # CASO LONG: Hubo una caída larga y ahora el precio rebota y rompe el techo de la vela anterior
                    if p_actual == min_p or (p_actual > min_p and c_pre < o_pre):
                        if c_act > o_act and c_act > float(v_pre[2]): # Vela verde rompe máximo anterior
                            ops.append({'s':m, 'l':'LONG', 'p':c_act, 'x':15})
                            print(f"🚀 PICO LARGO ABAJO: Rebote detectado en {m} (Amplitud: {amplitud:.2f}%)")
                            break

                    # CASO SHORT: Hubo una subida larga y ahora el precio se agota y rompe el piso anterior
                    if p_actual == max_p or (p_actual < max_p and c_pre > o_pre):
                        if c_act < o_act and c_act < float(v_pre[3]): # Vela roja rompe mínimo anterior
                            ops.append({'s':m, 'l':'SHORT', 'p':c_act, 'x':15})
                            print(f"🔻 PICO LARGO ARRIBA: Agotamiento en {m} (Amplitud: {amplitud:.2f}%)")
                            break

            print(f"💰 ${cap:.2f} | Buscando picos largos (>0.35%)... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(1)
        time.sleep(max(1, 4 - (time.time() - t_l)))

if __name__ == "__main__": bot()
