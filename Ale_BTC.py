import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None 
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 9.90) if r else 9.90
    print(f"🧠 V500 RAZONAMIENTO ESTRUCTURAL | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE POSICIÓN (Razonamiento de Supervivencia)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])

                # RAZONAMIENTO: Si el precio rompe la estructura que nos metió, cerramos YA.
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                # Si estamos en SHORT y el precio supera el máximo de las últimas 3 velas, la lógica falló.
                highs = [float(x[2]) for x in k[-4:-1]]
                lows = [float(x[3]) for x in k[-4:-1]]

                stop_estructural = (o['l'] == 'LONG' and p_a < min(lows)) or (o['l'] == 'SHORT' and p_a > max(highs))

                if stop_estructural or roi >= 7.0 or roi <= -1.2:
                    cap *= (1 + (roi/100))
                    if r: r.set("saldo_eterno_ale", str(cap))
                    ops.remove(o)
                    print(f"🔄 RAZONAMIENTO: Estructura rota. Cierre en {o['s']} | Saldo: ${cap:.2f}")

            # 2. ENTRADA POR ACCIÓN DE PRECIO (El Programa Piensa)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    
                    # EMAs para tendencia de fondo
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # RAZONAMIENTO: Buscamos "Velas de Intención"
                    v1, v2 = k[-2], k[-1]
                    c_v1, o_v1 = float(v1[4]), float(v1[1])
                    c_v2, o_v2 = float(v2[4]), float(v2[1])
                    
                    # ¿El mercado está haciendo escalones? (Estructura)
                    alcista = c_v1 > o_v1 and c_v2 > o_v2 and c_v2 > c_v1
                    bajista = c_v1 < o_v1 and c_v2 < o_v2 and c_v2 < c_v1

                    # Filtro de Fuerza: La vela tiene que ser sólida (80% cuerpo)
                    cuerpo_v2 = abs(c_v2 - o_v2)
                    rango_v2 = float(v2[2]) - float(v2[3])
                    fuerza_real = cuerpo_v2 > (rango_v2 * 0.8)

                    # SOLO DISPARA SI LA EMA Y LA ESTRUCTURA COINCIDEN
                    if e9 > e27 and alcista and fuerza_real:
                        ops.append({'s':m, 'l':'LONG', 'p':c_v2, 'x':15})
                        print(f"🎯 RAZONADO: Tendencia + Estructura LONG en {m}")
                        break
                    
                    if e9 < e27 and bajista and fuerza_real:
                        ops.append({'s':m, 'l':'SHORT', 'p':c_v2, 'x':15})
                        print(f"🎯 RAZONADO: Tendencia + Estructura SHORT en {m}")
                        break

            print(f"💰 ${cap:.2f} | Analizando Estructura... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(2)
        time.sleep(max(1, 5 - (time.time() - t_l)))

if __name__ == "__main__": bot()
