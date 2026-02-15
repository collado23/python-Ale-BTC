import os, time, redis, threading
from binance.client import Client

r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None 

def bot():
    c = Client()
    # Saldo real recuperado
    cap = float(r.get("cap_v216") or 14.03)
    ops = []
    print(f"⚡ V216 SCALPER PRO | ANTI-BANEO | ${cap}")

    while True:
        t_inicio = time.time()
        try:
            # --- 1. SCANNER TOTAL (1 sola petición a Binance = NO BANEO) ---
            tks = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            for o in ops[:]:
                p_actual = tks[o['s']]
                diff = (p_actual - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_actual)/o['p']
                
                # ROI Neto (Calculando comisión de 15x para no mentir)
                roi = (diff * 100 * o['x']) - (0.1 * o['x'])

                # Salto de potencia rápido (0.5% para asegurar el tiro)
                if roi > 0.5 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True

                # Cierres rápidos (Scalping puro)
                cierre = False
                if roi >= 6.0:
                    o['m_r'] = max(o.get('m_r', 0), roi)
                    o['tr'] = True
                
                if o.get('tr'):
                    if roi < (o['m_r'] - 0.4): cierre = True # Si baja un poquito del tope, cobramos
                elif (o['be'] and roi <= 0.1) or roi <= -0.9:
                    cierre = True
                
                if cierre:
                    cap *= (1 + (roi/100))
                    r.set("cap_v216", str(cap))
                    r.setex(f"lock_{o['s']}", 45, "1") # Bloqueo cortito de 45 seg
                    ops.remove(o)
                    print(f"✅ CIERRE: {roi:.2f}% | BAL: ${cap:.2f}")

            # --- 2. MENTE DE SEGUNDOS (Analiza suba/baja instantánea) ---
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT']:
                    if r.exists(f"lock_{m}"): continue
                    
                    p_ahora = tks[m]
                    p_hace_instante = r.get(f"v_{m}") # Precio que la memoria guardó hace 5 seg
                    r.setex(f"v_{m}", 10, str(p_ahora)) # Guardamos el de ahora para la próxima
                    
                    if not p_hace_instante: continue
                    
                    # ¿Qué tan rápido se movió en estos segundos?
                    impulso = (p_ahora - float(p_hace_instante)) / float(p_hace_instante) * 100
                    
                    # DISPARO POR INERCIA (Si detecta suba o baja brusca en segundos)
                    if impulso > 0.06: # SUBE RÁPIDO
                        ops.append({'s':m,'l':'LONG','p':p_ahora,'x':5,'be':False})
                        print(f"🚀 SUBIDA DETECTADA: {m} (+{impulso:.3f}%)")
                        break
                    
                    if impulso < -0.06: # BAJA RÁPIDO
                        ops.append({'s':m,'l':'SHORT','p':p_ahora,'x':5,'be':False})
                        print(f"📉 BAJA DETECTADA: {m} ({impulso:.3f}%)")
                        break

            print(f"🤖 Vigilando... ${cap:.2f} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except Exception as e:
            time.sleep(5) # Si hay error de conexión, frenamos un poco

        # --- 3. TIEMPO DE RESPIRACIÓN (Crucial para Binance) ---
        # 4 segundos es perfecto: es rápido para scalping pero Binance no lo banea
        time.sleep(max(1, 4 - (time.time() - t_inicio)))

if __name__ == "__main__": bot()
