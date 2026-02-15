import os, time, redis
from binance.client import Client

# --- 🧠 MEMORIA PROPIA (BIBLIOTECA DE ESTRATEGIAS) ---
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
    cap = float(mente("cap_v227") or 13.22)
    ops = []
    
    print(f"📚 V227 BIBLIOTECA JAPONESA COMPLETA | SALDO: ${cap}")

    while True:
        t_ciclo = time.time()
        try:
            tks = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            for o in ops[:]:
                p_act = tks[o['s']]
                diff = (p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']
                roi = (diff * 100 * o['x']) - (0.12 * o['x'])

                # Trailing Profit de "Tendencia de Libro"
                # Solo cerramos si el patrón de velas indica fin de movimiento
                max_r = float(mente(f"max_{o['s']}") or 0)
                if roi > max_r: mente(f"max_{o['s']}", roi)

                if (roi > 3.0 and roi < max_r - 1.5) or roi >= 12.0 or roi <= -1.4:
                    cap *= (1 + (roi/100))
                    mente("cap_v227", cap)
                    mente(f"lock_{o['s']}", "1", 30)
                    ops.remove(o)
                    print(f"✅ CIERRE ESTRATÉGICO: {roi:.2f}% | BAL: ${cap:.2f}")

            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if mente(f"lock_{m}"): continue
                    
                    # Pedimos historial de 10 velas para analizar todos los patrones del libro
                    k = c.get_klines(symbol=m, interval='1m', limit=10)
                    def p_v(i): # Función para leer la "ropa" de cada vela
                        v = k[i]; o, h, l, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                        return {'o':o, 'h':h, 'l':l, 'c':cl, 'b':abs(cl-o), 'bull':cl>o, 'r':h-l}
                    
                    v1, v2, v3 = p_v(-2), p_v(-3), p_v(-4) # Las últimas 3 cerradas

                    # EMAs de fondo (Contexto de tendencia)
                    kl_ema = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl_ema = [float(x[4]) for x in kl_ema]
                    e9, e27 = sum(cl_ema[-9:])/9, sum(cl_ema[-27:])/27

                    decision = None

                    # --- 📖 TODO EL LIBRO DE VELAS (Lógica de Mente Propia) ---
                    
                    # 1. ANALISIS DE FUERZA (Soldados y Cuervos)
                    fuerza_alcista = v1['bull'] and v2['bull'] and v3['bull'] and v1['b'] > v2['b']
                    fuerza_bajista = not v1['bull'] and not v2['bull'] and not v3['bull'] and v1['b'] > v2['b']

                    # 2. ANALISIS DE REVERSIÓN (Martillos, Estrellas, Dojis)
                    # Martillo o Pinbar (Mecha abajo > 2 veces el cuerpo)
                    hammer = (v1['l'] < min(v1['o'], v1['c']) - v1['b']*2) and (v1['h'] < max(v1['o'], v1['c']) + v1['b'])
                    # Estrella Fugaz (Mecha arriba > 2 veces el cuerpo)
                    shooting_star = (v1['h'] > max(v1['o'], v1['c']) + v1['b']*2) and (v1['l'] > min(v1['o'], v1['c']) - v1['b'])

                    # 3. ANALISIS DE ABSORCIÓN (Envolventes)
                    engulfing_bull = v1['bull'] and not v2['bull'] and v1['c'] > v2['o'] and v1['o'] < v2['c']
                    engulfing_bear = not v1['bull'] and v2['bull'] and v1['c'] < v2['o'] and v1['o'] > v2['c']

                    # 4. ANALISIS DE CONTINUIDAD (Harami y Piercing)
                    harami_bull = v2['b'] > v1['b']*2 and v1['o'] > v2['c'] and v1['c'] < v2['o']

                    # --- GATILLO FINAL (Cruzando todo el conocimiento) ---
                    if e9 > e27: # Si la tendencia es alcista
                        if fuerza_alcista or engulfing_bull or (hammer and e9 > e27):
                            decision = 'LONG'
                    elif e9 < e27: # Si la tendencia es bajista
                        if fuerza_bajista or engulfing_bear or (shooting_star and e9 < e27):
                            decision = 'SHORT'

                    if decision:
                        ops.append({'s':m,'l':decision,'p':tks[m],'x':5})
                        print(f"📖 {decision} ACTIVADO | MOTIVO: Patrón Completo Detectado en {m}")
                        break

            print(f"📡 Mente Maestra Operando... ${cap:.2f}", end='\r')
            
        except Exception as e:
            time.sleep(2)

        time.sleep(max(1, 4 - (time.time() - t_ciclo)))

if __name__ == "__main__": bot()
