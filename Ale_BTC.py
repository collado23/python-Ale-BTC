import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
except:
    r = None

def bot():
    c = Client()
    # Usamos el saldo real que quedó para recuperarlo con trades de calidad
    cap = float(r.get("saldo_eterno_ale") or 0.57) if r else 0.57
    print(f"📖 V1800 ACCIÓN DEL PRECIO (LIBRO) | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE POSICIÓN (Si el retroceso deja de ser chico, abortamos)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])
                
                # Salida por profit o por rotura de la estructura del escalón
                if roi >= 6.0 or roi <= -1.2:
                    cap *= (1 + (roi/100))
                    if r: r.set("saldo_eterno_ale", str(cap))
                    ops.remove(o)
                    print(f"✅ CIERRE: {o['s']} | Resultado: {'WIN' if roi>0 else 'LOSS'}")

            # 2. ANÁLISIS DE ESTRUCTURA (Impulso + Retroceso Saludable)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    # Miramos las últimas 15 velas para ver el dibujo completo
                    k = c.get_klines(symbol=m, interval='1m', limit=15)
                    precios = [float(x[4]) for x in k]
                    
                    p_min = min(precios)
                    p_max = max(precios)
                    p_actual = precios[-1]
                    
                    # MEDIMOS EL IMPULSO (Distancia que recorrió la liga)
                    impulso = (p_max - p_min) / p_min * 100
                    
                    # FILTRO: El impulso tiene que ser significativo (más de 0.25%) 
                    # para que no sea un "pico cortito"
                    if impulso < 0.25: continue

                    # ANALIZAMOS EL RETROCESO CHICO (El descanso)
                    # Para LONG: El precio tocó un máximo y ahora bajó un poquito, 
                    # pero sigue estando en la parte alta del impulso (zona de bandera).
                    caida_desde_techo = (p_max - p_actual) / p_max * 100
                    subida_desde_suelo = (p_actual - p_min) / p_min * 100
                    
                    # --- LÓGICA DE "EL LIBRO" ---
                    # Si subió fuerte y el retroceso es menor al 30% de lo que subió...
                    if subida_desde_suelo > (impulso * 0.7) and 0.03 < caida_desde_techo < 0.15:
                        # Si la vela actual empieza a superar a la anterior, ENTRA.
                        if p_actual > precios[-2]:
                            ops.append({'s':m, 'l':'LONG', 'p':p_actual, 'x':15})
                            print(f"🚀 CONTINUACIÓN LONG: Impulso {impulso:.2f}% | Retroceso CHICO detectado.")
                            break

                    # Para SHORT: Cayó fuerte y el rebote es apenas un suspiro
                    rebote_desde_suelo = (p_actual - p_min) / p_min * 100
                    if (p_max - p_actual)/p_actual > (impulso * 0.7) and 0.03 < rebote_desde_suelo < 0.15:
                        if p_actual < precios[-2]:
                            ops.append({'s':m, 'l':'SHORT', 'p':p_actual, 'x':15})
                            print(f"🔻 CONTINUACIÓN SHORT: Caída {impulso:.2f}% | Rebote CHICO detectado.")
                            break

            print(f"💰 ${cap:.2f} | Buscando escalón del libro... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(1)
        time.sleep(max(1, 3 - (time.time() - t_l)))

if __name__ == "__main__": bot()
