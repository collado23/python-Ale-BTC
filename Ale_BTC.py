import os, time, redis
from binance.client import Client

# --- 🧠 MEMORIA DE TRABAJO ---
mem_interna = {}
try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None 
except:
    r = None

def mente(k, v=None, ex=None):
    try:
        if v is not None:
            if r: 
                if ex: r.setex(k, ex, str(v))
                else: r.set(k, str(v))
            mem_interna[k] = v
            return v
        return r.get(k) if r else mem_interna.get(k)
    except: return mem_interna.get(k)

def bot():
    c = Client()
    cap = float(mente("cap_v219") or 14.04)
    ops = []
    
    print(f"🚀 V219 CAZADOR | AGRESIVO Y RÁPIDO | ${cap}")

    while True:
        t_ciclo = time.time()
        try:
            # Una sola petición para no ser baneado
            tks = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            for o in ops[:]:
                p_act = tks[o['s']]
                diff = (p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']
                roi = (diff * 100 * o['x']) - (0.12 * o['x']) # Comisión real ajustada

                # Salto a 15x si va bien
                if roi > 0.35 and o['x'] == 5: o['x'] = 15

                # CIERRE: Solo si hay ganancia real o pérdida de protección
                # Subimos el Stop Loss a -1.2% para que no te saque al primer respiro
                if roi >= 6.0 or roi <= -1.2 or (roi > 0.5 and diff < -0.02):
                    cap *= (1 + (roi/100))
                    mente("cap_v219", cap)
                    mente(f"bloqueo_{o['s']}", "1", 20) # Bloqueo corto de 20 seg
                    ops.remove(o)
                    print(f"💰 CIERRE {o['s']} | ROI: {roi:.2f}% | BAL: ${cap:.2f}")

            # RADAR DE ENTRADA (Sensibilidad aumentada)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if mente(f"bloqueo_{m}"): continue
                    
                    p_ahora = tks[m]
                    p_hace_poco = mente(f"h_{m}")
                    mente(f"h_{m}", p_ahora, 15)
                    
                    if not p_hace_poco: continue
                    
                    # Analizamos la VELOCIDAD en segundos
                    impulso = (p_ahora - float(p_hace_poco)) / float(p_hace_poco) * 100
                    
                    # GATILLO MÁS SENSIBLE (0.04% en vez de 0.06%)
                    # Si el precio se mueve un poquito, el bot ya muerde.
                    if impulso > 0.04: 
                        ops.append({'s':m,'l':'LONG','p':p_ahora,'x':5})
                        print(f"🔥 CAZANDO SUBIDA: {m} (+{impulso:.3f}%)")
                        break
                    
                    if impulso < -0.04:
                        ops.append({'s':m,'l':'SHORT','p':p_ahora,'x':5})
                        print(f"📉 CAZANDO BAJA: {m} ({impulso:.3f}%)")
                        break

            print(f"📡 Radar Activo: ${cap:.2f} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except Exception as e:
            time.sleep(2)

        # Ritmo de 3 segundos (Más rápido para scalping de reacción)
        time.sleep(max(1, 3 - (time.time() - t_ciclo)))

if __name__ == "__main__": bot()
