import os, time, redis
from binance.client import Client

try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None 
except:
    r = None

def bot():
    c = Client()
    cap = float(r.get("saldo_eterno_ale") or 0.57) if r else 0.57
    print(f"📏 V1500 DISTANCIA Y RETROCESO | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN: Si el retroceso deja de ser chico y rompe el origen, afuera.
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.15 * o['x'])
                
                if roi >= 7.0 or roi <= -1.4:
                    cap *= (1 + (roi/100))
                    if r: r.set("saldo_eterno_ale", str(cap))
                    ops.remove(o)
                    print(f"✅ CIERRE: {o['s']} | Saldo: ${cap:.2f}")

            # 2. ANÁLISIS DE DISTANCIA (La película que vos ves)
            if len(ops) < 1:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=20)
                    precios = [float(x[4]) for x in k]
                    
                    # Medimos el Impulso (La distancia que recorrió)
                    p_inicio = precios[0]
                    p_actual = precios[-1]
                    p_max = max(precios)
                    p_min = min(precios)
                    
                    distancia_total = (p_max - p_min) / p_min * 100
                    
                    # SI EL PRECIO SUBIÓ MUCHO (Impulso largo)
                    if p_max == max(precios[-10:-3]) and distancia_total > 0.50:
                        # Calculamos el retroceso desde el pico
                        retroceso = (p_max - p_actual) / p_max * 100
                        
                        # RAZONAMIENTO: Si subió 0.50% y el retroceso es "chico" (ej: menos del 0.20%)
                        # y el precio vuelve a apuntar arriba... ENTRA.
                        if 0.05 < retroceso < 0.20:
                            if p_actual > precios[-2]: # Volvió a subir un poquito
                                ops.append({'s':m, 'l':'LONG', 'p':p_actual, 'x':15})
                                print(f"🚀 IMPULSO LONG: Distancia {distancia_total:.2f}% | Retroceso chico: {retroceso:.2f}%")
                                break

                    # SI EL PRECIO CAYÓ MUCHO (Impulso largo para abajo)
                    if p_min == min(precios[-10:-3]) and distancia_total > 0.50:
                        # Calculamos el retroceso (rebote) desde el piso
                        retroceso = (p_actual - p_min) / p_min * 100
                        
                        # RAZONAMIENTO: Si cayó mucho y el rebote es apenas un suspiro
                        if 0.05 < retroceso < 0.20:
                            if p_actual < precios[-2]: # Vuelve a caer
                                ops.append({'s':m, 'l':'SHORT', 'p':p_actual, 'x':15})
                                print(f"🔻 IMPULSO SHORT: Distancia {distancia_total:.2f}% | Retroceso chico: {retroceso:.2f}%")
                                break

            print(f"💰 ${cap:.2f} | Midiendo distancias y retrocesos... | {time.strftime('%H:%M:%S')}", end='\r')
        except: time.sleep(1)
        time.sleep(max(1, 4 - (time.time() - t_l)))

if __name__ == "__main__": bot()
