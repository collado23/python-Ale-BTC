import os, time, redis
from binance.client import Client

# --- 🧠 CEREBRO CON AUTOCRÍTICA ---
mem = {}
try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
except: r = None

def mente(k, v=None, ex=None):
    try:
        if v is not None:
            if r: 
                if ex: r.setex(k, ex, str(v))
                else: r.set(k, str(v))
            mem[k] = v
            return v
        return r.get(k).decode() if r and r.exists(k) else mem.get(k)
    except: return mem.get(k)

def bot():
    c = Client()
    cap = float(mente("cap_v223") or 13.45)
    ops = []
    
    # La memoria recuerda qué tan exigente debe ser (Separación de EMAs)
    # Si pierde, este número sube solo. Si gana, baja.
    exigencia = float(mente("exigencia_ema") or 0.02) 

    print(f"🧠 V223 AUTO-ADAPTATIVO | SALDO: ${cap} | EXIGENCIA: {exigencia}%")

    while True:
        t_ciclo = time.time()
        try:
            tks = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            for o in ops[:]:
                p_act = tks[o['s']]
                diff = (p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']
                roi = (diff * 100 * o['x']) - (0.12 * o['x'])

                if roi > 0.4 and o['x'] == 5: o['x'] = 15

                # CIERRE Y APRENDIZAJE
                if roi >= 6.0 or roi <= -1.1:
                    if roi < 0: # SI PERDIÓ, LA MEMORIA APRENDE
                        exigencia = min(0.06, exigencia + 0.005)
                        print(f"⚠️ Cruce falso detectado. Subiendo exigencia a {exigencia}%")
                    else: # SI GANÓ, SE RELAJA
                        exigencia = max(0.015, exigencia - 0.002)
                    
                    mente("exigencia_ema", exigencia)
                    cap *= (1 + (roi/100))
                    mente("cap_v223", cap)
                    mente(f"lock_{o['s']}", "1", 60)
                    ops.remove(o)
                    print(f"✅ BALANCE: ${cap:.2f} | NUEVA EXIGENCIA: {exigencia}%")

            # RADAR DE ANÁLISIS DE EMAs
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if mente(f"lock_{m}"): continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9 = sum(cl[-9:])/9
                    e27 = sum(cl[-27:])/27
                    
                    # Distancia entre EMAs (el "Gap")
                    distancia = ((e9 - e27) / e27) * 100
                    
                    # La memoria decide si la distancia es suficiente basada en la "exigencia"
                    
                    
                    # LONG: EMA9 arriba de EMA27 + Distancia mayor a la exigencia aprendida
                    if e9 > e27 and distancia > exigencia:
                        ops.append({'s':m,'l':'LONG','p':tks[m],'x':5})
                        print(f"🎯 MEMORIA APRUEBA LONG: {m} (Gap: {distancia:.3f}%)")
                        break
                        
                    # SHORT: EMA9 abajo de EMA27 + Distancia negativa mayor a la exigencia
                    if e9 < e27 and distancia < -exigencia:
                        ops.append({'s':m,'l':'SHORT','p':tks[m],'x':5})
                        print(f"🎯 MEMORIA APRUEBA SHORT: {m} (Gap: {distancia:.3f}%)")
                        break

            print(f"📡 Cerebro Analizando (Exigencia {exigencia:.3f}%): ${cap:.2f}", end='\r')
            
        except Exception as e:
            time.sleep(2)

        time.sleep(max(1, 4 - (time.time() - t_ciclo)))

if __name__ == "__main__": bot()
