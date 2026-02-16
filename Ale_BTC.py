import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None 
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 0.57) if r else 0.57
    print(f"📉 V1600 ÚLTIMO ALIENTO | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])
                
                # Si el "retroceso chico" se convierte en caída grande, cerramos sin dudar
                if roi >= 8.0 or roi <= -1.5:
                    cap *= (1 + (roi/100))
                    if r: r.set("saldo_eterno_ale", str(cap))
                    ops.remove(o)
                    print(f"✅ CIERRE: {o['s']} | Saldo: ${cap:.2f}")

            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    # Miramos los últimos 30 minutos para ver la "Distancia"
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    precios = [float(x[4]) for x in k]
                    p_actual = precios[-1]
                    
                    # 1. BUSCAMOS EL IMPULSO LARGO (Distancia)
                    # El precio tiene que haberse movido más de un 0.7% desde el inicio de la secuencia
                    impulso = (max(precios) - min(precios)) / min(precios) * 100
                    
                    if impulso < 0.7: continue # Si es cortito, no sirve.

                    # 2. BUSCAMOS EL RETROCESO CHICO (El descanso)
                    # Si venía subiendo, buscamos que baje un poquito pero que se mantenga arriba
                    if p_actual == max(precios): continue # Si sigue en el pico, esperamos el descanso
                    
                    # Definimos el "Piso" del impulso
                    piso = min(precios)
                    techo = max(precios)
                    
                    # RAZONAMIENTO: El precio bajó del techo (retroceso) 
                    # pero todavía está muy lejos del piso (sigue la fuerza)
                    distancia_al_piso = (p_actual - piso) / piso * 100
                    caida_desde_techo = (techo - p_actual) / techo * 100

                    # TU LÓGICA: Sube (distancia > 0.7), retroceso chico (caida < 0.2), vuelve a subir
                    if impulso > 0.7 and 0.05 < caida_desde_techo < 0.25:
                        if p_actual > precios[-2]: # Vuelve a subir (gatillo)
                            ops.append({'s':m, 'l':'LONG', 'p':p_actual, 'x':15})
                            print(f"🚀 TENDENCIA CONFIRMADA: Subida larga + descanso en {m}")
                            break

                    # LÓGICA SHORT: Cae fuerte, rebote chico, vuelve a caer
                    if impulso > 0.7 and 0.05 < (p_actual - min(precios))/min(precios) < 0.25:
                        if p_actual < precios[-2]: # Vuelve a caer
                            ops.append({'s':m, 'l':'SHORT', 'p':p_actual, 'x':15})
                            print(f"🔻 TENDENCIA CONFIRMADA: Caída larga + descanso en {m}")
                            break

            print(f"💰 ${cap:.2f} | Esperando impulso real... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(1)
        time.sleep(max(1, 5 - (time.time() - t_l)))

if __name__ == "__main__": bot()
