import os, time, redis
from binance.client import Client

# Conexión segura a memoria: si falla, usa memoria local
try:
    url = os.getenv("REDIS_URL")
    r = redis.from_url(url) if url else None
    if r: r.ping()
except:
    r = None

def g_m(k, v=None, ex=None):
    if not r: return None # Si no hay Redis, no explota
    try:
        if v is not None:
            if ex: r.setex(k, ex, str(v))
            else: r.set(k, str(v))
        return r.get(k)
    except: return None

def bot():
    c = Client()
    # Recupera capital de memoria o usa el último conocido de tus logs
    m_cap = g_m("cap_v217")
    cap = float(m_cap) if m_cap else 14.04 #
    ops = []
    
    print(f"🚀 V217 RADAR ACTIVO | SALDO: ${cap}")

    while True:
        t_ciclo = time.time()
        try:
            # SCANNER DE SEGUNDOS (Eficiente para Binance)
            tks = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            # 1. GESTIÓN DE OPERACIONES ABIERTAS
            for o in ops[:]:
                p_act = tks[o['s']]
                diff = (p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']
                roi = (diff * 100 * o['x']) - (0.1 * o['x'])

                # Potencia rápida 15x
                if roi > 0.4 and o['x'] == 5: o['x'] = 15

                # Cierre de Scalping (Rápido para no dormir)
                if roi >= 5.0 or roi <= -0.85:
                    cap *= (1 + (roi/100))
                    g_m("cap_v217", cap)
                    g_m(f"l_{o['s']}", "1", 30) # Bloqueo de 30 seg
                    ops.remove(o)
                    print(f"✅ COBRADO: {roi:.2f}% | BAL: ${cap:.2f}")

            # 2. RADAR DE ENTRADA (Analiza suba/baja en segundos)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if g_m(f"l_{m}"): continue # Salta si está bloqueada
                    
                    p_ahora = tks[m]
                    p_prev = g_m(f"p_{m}") # Mira el precio de hace 3 segundos
                    g_m(f"p_{m}", p_ahora, 10)
                    
                    if not p_prev: continue
                    
                    # CÁLCULO DE VELOCIDAD INSTANTÁNEA
                    vel = (p_ahora - float(p_prev)) / float(p_prev) * 100
                    
                    if vel > 0.055: # SUBIDA DETECTADA
                        ops.append({'s':m,'l':'LONG','p':p_ahora,'x':5})
                        print(f"📈 ENTRANDO LONG: {m} (VEL: {vel:.3f})")
                        break
                    
                    if vel < -0.055: # BAJA DETECTADA
                        ops.append({'s':m,'l':'SHORT','p':p_ahora,'x':5})
                        print(f"📉 ENTRANDO SHORT: {m} (VEL: {vel:.3f})")
                        break

            print(f"📡 Radar: ${cap:.2f} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            time.sleep(3)

        # Ajuste de tiempo para Binance (3 segundos es muy agresivo y seguro)
        time.sleep(max(1, 3 - (time.time() - t_ciclo)))

if __name__ == "__main__": bot()
