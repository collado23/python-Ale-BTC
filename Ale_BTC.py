import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None  
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 0.57) if r else 0.57
    print(f"📐 V2200 ESTRATEGA | MEDIDAS + COMISIÓN | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE SALIDA (Aprovechando las 15x)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                # ROI neto (restando comisiones de entrada y salida aprox 0.15% * x)
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.16 * o['x'])
                
                # Buscamos recorridos que paguen la fiesta: Profit 7% o Loss -1.3%
                if roi >= 7.0 or roi <= -1.3:
                    cap *= (1 + (roi/100))
                    if r: r.set("saldo_eterno_ale", str(cap))
                    ops.remove(o)
                    print(f"✅ CIERRE ESTRATÉGICO: {o['s']} | Neto: ${cap:.2f}")

            # 2. ANÁLISIS DE MEDIDAS (LIBRO DE VELAS)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=15)
                    v = k[-2]
                    
                    # Medidas de la vela
                    op, hi, lo, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl - op)
                    mecha_sup = hi - max(cl, op)
                    mecha_inf = min(cl, op) - lo
                    rango_vela = (hi - lo) / lo * 100 # Tamaño de la vela en %

                    # FILTRO DE COMISIÓN: Si la vela entera mide menos de 0.12%, 
                    # es muy chica para operar a 15x. El ruido nos mataría.
                    if rango_vela < 0.12: continue

                    # Tendencia previa (Distancia)
                    precios = [float(x[4]) for x in k[:-2]]
                    distancia = (max(precios) - min(precios)) / min(precios) * 100

                    # --- RAZONAMIENTO DE MEDIDAS ---
                    # Martillo: Mecha inferior > 2.5x cuerpo y sin mecha arriba
                    es_martillo = (mecha_inf > cuerpo * 2.5) and (mecha_sup < cuerpo * 0.5)
                    # Martillo Invertido: Mecha superior > 2.5x cuerpo y sin mecha abajo
                    es_martillo_inv = (mecha_sup > cuerpo * 2.5) and (mecha_inf < cuerpo * 0.5)

                    if distancia > 0.40: # Solo en picos largos
                        # LONG por Martillo
                        if es_martillo and cl < max(precios):
                            if float(k[-1][4]) > hi: # Confirmación
                                ops.append({'s':m, 'l':'LONG', 'p':float(k[-1][4]), 'x':15})
                                print(f"🔨 MARTILLO: Medida perfecta en {m}. Entrando...")
                                break
                        
                        # SHORT por Martillo Invertido
                        if es_martillo_inv and cl > min(precios):
                            if float(k[-1][4]) < lo: # Confirmación
                                ops.append({'s':m, 'l':'SHORT', 'p':float(k[-1][4]), 'x':15})
                                print(f"🛸 ESTRELLA: Medida perfecta en {m}. Entrando...")
                                break

            print(f"💰 ${cap:.2f} | Midiendo con precisión... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(1)
        time.sleep(max(1, 4 - (time.time() - t_l)))

if __name__ == "__main__": bot()
