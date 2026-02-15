import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None 
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 7.99) if r else 7.99
    print(f"🌊 V1100 DETECTOR DE PICOS | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE SALIDA (Si el pico se confirma en contra, cerramos)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])

                if roi >= 6.0 or roi <= -1.2:
                    cap *= (1 + (roi/100))
                    if r: r.set("saldo_eterno_ale", str(cap))
                    ops.remove(o)
                    print(f"✅ SALIDA: {o['s']} | Saldo: ${cap:.2f}")

            # 2. ANÁLISIS DE PICO (Lo que vos ves en la imagen)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=6)
                    
                    # Buscamos el Mínimo y Máximo de las últimas 5 velas
                    lows = [float(x[3]) for x in k[:-1]]
                    highs = [float(x[2]) for x in k[:-1]]
                    p_actual = float(k[-1][4])
                    v_act_c = float(k[-1][4])
                    v_act_o = float(k[-1][1])

                    # --- RAZONAMIENTO DEL PICO ---
                    
                    # CASO A: PICO ABAJO Y SUBE (Lo que me marcás)
                    # El precio venía haciendo mínimos, pero la vela actual cierra VERDE 
                    # y por encima del mínimo del pico.
                    pico_abajo = min(lows)
                    if v_act_c > v_act_o and p_actual > pico_abajo:
                        # Si la vela actual tiene fuerza de rebote
                        if v_act_c > float(k[-2][2]): # Supera el máximo de la vela anterior
                            ops.append({'s':m, 'l':'LONG', 'p':p_actual, 'x':15})
                            print(f"📈 PICO ABAJO DETECTADO: Pegando la vuelta en {m}")
                            break

                    # CASO B: PICO ARRIBA Y BAJA
                    # El precio tocó un techo y la vela actual es ROJA rompiendo el mínimo anterior.
                    pico_arriba = max(highs)
                    if v_act_c < v_act_o and p_actual < pico_arriba:
                        if v_act_c < float(k[-2][3]): # Rompe el mínimo de la vela anterior
                            ops.append({'s':m, 'l':'SHORT', 'p':p_actual, 'x':15})
                            print(f"📉 PICO ARRIBA DETECTADO: Empezando a caer en {m}")
                            break

            print(f"💰 ${cap:.2f} | Buscando el giro del pico... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(1)
        time.sleep(max(1, 3 - (time.time() - t_l)))

if __name__ == "__main__": bot()
