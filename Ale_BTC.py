import os, time, redis, threading
from binance.client import Client

r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None

def bot():
    c = Client()
    # Saldo recuperado de memoria
    cap = float(r.get("cap_v215") or 14.03)
    ops = []
    print(f"⚡ V215 RELÁMPAGO | MENTE ACTIVA | ${cap}")

    while True:
        t_inicio = time.time()
        try:
            # 1. CAPTURA DE PRECIOS INSTANTÁNEA
            tks = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            for o in ops[:]:
                p_actual = tks[o['s']]
                diff = (p_actual - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_actual)/o['p']
                roi = (diff * 100 * o['x']) - (0.1 * o['x'])

                # Salto de potencia rápido (0.4% para no dormir)
                if roi > 0.4 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True

                # Cierre dinámico para no devolver plata
                if (o['be'] and roi <= 0.1) or roi >= 6.0 or roi <= -0.8:
                    cap *= (1 + (roi/100))
                    r.set("cap_v215", str(cap))
                    # BLOQUEO CORTO (Solo 60 seg) para no perder la siguiente subida
                    r.setex(f"lock_{o['s']}", 60, "1") 
                    ops.remove(o)
                    print(f"💰 CIERRE: {roi:.2f}% | BAL: ${cap:.2f}")

            # 2. ANÁLISIS DE "MENTE RÁPIDA" (Gatillo de Segundos)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT']:
                    if r.exists(f"lock_{m}"): continue
                    
                    # Recuperar precio de hace 5-10 segundos de la memoria
                    p_pasado = r.get(f"p_{m}")
                    p_actual = tks[m]
                    r.setex(f"p_{m}", 10, str(p_actual)) # Guardar precio actual para la próxima vuelta
                    
                    if not p_pasado: continue
                    p_pasado = float(p_pasado)

                    # CÁLCULO DE VELOCIDAD (Si el precio se movió rápido en segundos)
                    velocidad = (p_actual - p_pasado) / p_pasado * 100
                    
                    # Gatillo: Si sube rápido + EMAs a favor = DISPARO
                    # No esperamos al cierre de la vela, disparamos por INERCIA
                    if velocidad > 0.05: # Subida rápida detectada en segundos
                        ops.append({'s':m,'l':'LONG','p':p_actual,'x':5,'be':False})
                        print(f"🚀 VELOCIDAD DETECTADA: LONG en {m}")
                        break
                    
                    if velocidad < -0.05: # Baja rápida detectada
                        ops.append({'s':m,'l':'SHORT','p':p_actual,'x':5,'be':False})
                        print(f"📉 VELOCIDAD DETECTADA: SHORT en {m}")
                        break

            print(f"🤖 Analizando... ${cap:.2f} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except Exception as e:
            time.sleep(2)

        # Loop de alta frecuencia (Cada 3-4 segundos)
        time.sleep(max(1, 4 - (time.time() - t_inicio)))

if __name__ == "__main__": bot()
