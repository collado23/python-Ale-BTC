import os, time, redis, threading
from binance.client import Client

# --- 🧠 MEMORIA INTELIGENTE (No se rompe si no hay Redis) ---
try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
except:
    r = None

def obtener_saldo():
    default = 11.83
    if r:
        try:
            v = r.get("saldo_eterno_ale")
            return float(v) if v else default
        except: return default
    return default

def guardar_saldo(v):
    if r:
        try: r.set("saldo_eterno_ale", str(v))
        except: pass

# --- 🚀 MOTOR DE CONFLUENCIA (EMAs + LIBRO) ---
def bot():
    c = Client()
    cap = obtener_saldo()
    ops = []
    
    print(f"⚔️ V248 LÓGICA PURA | SALDO: ${cap:.2f}")

    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE SALIDA (Usa el Libro para no esperar al Stop Loss)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.12 * o['x'])

                # ¿Qué dice el libro de velas ahora?
                k = c.get_klines(symbol=o['s'], interval='1m', limit=2)
                v_ahora = k[-1]; op_v, cl_v = float(v_ahora[1]), float(v_ahora[4])
                
                # Si el libro muestra que la fuerza se dio vuelta, cerramos para salvar capital
                cambio_fuerza = (o['l'] == 'LONG' and cl_v < op_v) or (o['l'] == 'SHORT' and cl_v > op_v)
                
                if (cambio_fuerza and roi < -0.3) or roi >= 8.0 or roi <= -1.2:
                    cap *= (1 + (roi/100))
                    guardar_saldo(cap)
                    ops.remove(o)
                    print(f"⚠️ REACCIÓN LIBRO: Salida en {o['s']} | Saldo: ${cap:.2f}")

            # 2. ENTRADA POR CONFLUENCIA (Mapa EMAs + Gatillo Libro)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    
                    # --- LAS EMAs (El Mapa de dirección) ---
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    distancia = abs(e9 - e27) / e27 * 100

                    # --- EL LIBRO DE VELAS (El Gatillo de fuerza) ---
                    v = k[-2] # Última cerrada
                    op_v, hi_v, lo_v, cl_v = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl_v - op_v)
                    rango = hi_v - lo_v
                    
                    # El libro exige: Una vela Marubozu (80% cuerpo) para confirmar la EMA
                    
                    vela_poder = cuerpo > (rango * 0.8)

                    # SOLO ENTRA SI TODO COINCIDE (Mapa + Gatillo)
                    if e9 > e27 and cl_v > op_v and vela_poder and distancia > 0.03:
                        ops.append({'s':m,'l':'LONG','p':float(c.get_symbol_ticker(symbol=m)['price']),'x':15})
                        print(f"🎯 DISPARO LONG: EMAs + Libro confirmados en {m}")
                        break
                    
                    if e9 < e27 and cl_v < op_v and vela_poder and distancia > 0.03:
                        ops.append({'s':m,'l':'SHORT','p':float(c.get_symbol_ticker(symbol=m)['price']),'x':15})
                        print(f"🎯 DISPARO SHORT: EMAs + Libro confirmados en {m}")
                        break

            print(f"💰 ${cap:.2f} | EMAs + Libro activos | {time.strftime('%H:%M:%S')}", end='\r')
        except Exception as e:
            time.sleep(2)
        
        time.sleep(max(1, 5 - (time.time() - t_l)))

if __name__ == "__main__": bot()
