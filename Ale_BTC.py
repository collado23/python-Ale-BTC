import os, time, redis
from binance.client import Client

# Conexión a la memoria del bot para no perder el saldo
try:
    r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
except:
    r = None

def bot():
    c = Client()
    # Recuperamos el saldo real. Si no hay nada, asume los 0.57 que quedaron.
    cap = float(r.get("saldo_eterno_ale") or 0.57) if r else 0.57
    print(f"🦁 V2300 EL EQUILIBRISTA | MEDIDAS DEL LIBRO | SALDO: ${cap:.2f}")

    ops = []
    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE POSICIÓN (Apalancamiento 15x)
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                # ROI Neto: Restamos 0.16% de comisión por el apalancamiento
                roi = (((p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']) * 100 * o['x']) - (0.16 * o['x'])
                
                # Salida: Buscamos un 6% de ganancia o cortamos en -1.2% para proteger lo que queda
                if roi >= 6.0 or roi <= -1.2:
                    cap *= (1 + (roi/100))
                    if r: r.set("saldo_eterno_ale", str(cap))
                    ops.remove(o)
                    print(f"✅ CIERRE: {o['s']} | Saldo Actual: ${cap:.2f}")

            # 2. ANÁLISIS DE ENTRADA (Medidas de Velas Japonesas)
            if len(ops) < 1:
                # Monedas con buen movimiento para scalping
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    k = c.get_klines(symbol=m, interval='1m', limit=15)
                    v = k[-2] # Vela cerrada para medir
                    
                    # --- MEDIDAS DE LA VELA (Calibre) ---
                    ap, hi, lo, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl - ap)
                    mecha_sup = hi - max(cl, ap)
                    mecha_inf = min(cl, ap) - lo
                    rango_vela_porc = (hi - lo) / lo * 100
                    
                    if cuerpo == 0: cuerpo = 0.00000001 # Evita error matemático

                    # --- DISTANCIA PREVIA (Para que sea un pico de verdad) ---
                    precios_atras = [float(x[4]) for x in k[:-2]]
                    max_atras = max(precios_atras)
                    min_atras = min(precios_atras)
                    distancia = (max_atras - min_atras) / min_atras * 100

                    # --- EL LIBRO: DEFINICIÓN DE MARTILLOS ---
                    # Martillo: Mecha de abajo al menos 2 veces el cuerpo y poca mecha arriba
                    es_martillo = (mecha_inf > cuerpo * 2.0) and (mecha_sup < cuerpo * 0.8)
                    # Martillo Invertido: Mecha de arriba al menos 2 veces el cuerpo y poca mecha abajo
                    es_martillo_inv = (mecha_sup > cuerpo * 2.0) and (mecha_inf < cuerpo * 0.8)

                    # FILTRO DE ACTIVIDAD: La vela tiene que medir algo (0.08%) para que no sea puro ruido
                    if rango_vela_porc < 0.08: continue

                    # SENSIBILIDAD: Si hubo un movimiento de al menos 0.20%, buscamos el giro
                    if distancia > 0.20:
                        
                        # CASO LONG: Martillo en el piso después de una caída
                        if es_martillo and cl < max_atras:
                            # Gatillo: La vela actual tiene que superar el máximo del martillo
                            if float(k[-1][4]) > hi:
                                ops.append({'s':m, 'l':'LONG', 'p':float(k[-1][4]), 'x':15})
                                print(f"🔨 MARTILLO DETECTADO en {m} (Distancia: {distancia:.2f}%)")
                                break

                        # CASO SHORT: Martillo Invertido en el techo después de una subida
                        if es_martillo_inv and cl > min_atras:
                            # Gatillo: La vela actual tiene que romper el mínimo del martillo
                            if float(k[-1][4]) < lo:
                                ops.append({'s':m, 'l':'SHORT', 'p':float(k[-1][4]), 'x':15})
                                print(f"🛸 MARTILLO INV DETECTADO en {m} (Distancia: {distancia:.2f}%)")
                                break

            print(f"💰 ${cap:.2f} | Analizando picos y medidas del libro... | {time.strftime('%H:%M:%S')}", end='\r')
        except: 
            time.sleep(2)
        
        # Espera activa: revisa cada 3 segundos para no perder el "gatillo"
        time.sleep(max(1, 3 - (time.time() - t_l)))

if __name__ == "__main__":
    bot()
