import os, time
from binance.client import Client

def bot():
    c = Client() # Simulación
    monedas = ['SHIBUSDT', 'PEPEUSDT']
    
    saldo_simulado = 27.58 
    ops_sim = [] # Lista de operaciones (máximo 1)
    leverage = 15 
    comision_sim = 0.0004 

    print(f"🔥 PROYECTO MEMES: SHIB + PEPE")
    print(f"🔒 MODO: Una sola moneda a la vez")
    print(f"💰 Saldo inicial: ${saldo_simulado:.2f}")

    while True:
        try:
            # 1. GESTIÓN DE LA OPERACIÓN ACTUAL
            # Si hay una operación, la monitoreamos hasta que cierre
            if len(ops_sim) > 0:
                o = ops_sim[0] # Tomamos la única operación abierta
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - (comision_sim * 2 * 100 * leverage)
                
                # Velas para salida con distancia
                v_u, v_a = k[-2], k[-3]
                color_u = "VERDE" if float(v_u[4]) > float(v_u[1]) else "ROJA"
                color_a = "VERDE" if float(v_a[4]) > float(v_a[1]) else "ROJA"

                cierre = False
                target = 2.0 if o['s'] == 'SHIBUSDT' else 2.5
                
                if roi_neto >= target:
                    # Esperamos 2 velas en contra para confirmar fin de racha
                    if (o['l'] == "LONG" and color_u == "ROJA" and color_a == "ROJA") or \
                       (o['l'] == "SHORT" and color_u == "VERDE" and color_a == "VERDE"):
                        cierre, motivo = True, f"✅ {o['s']} PROFIT"
                
                elif roi_neto <= -2.5:
                    cierre, motivo = True, f"❌ {o['s']} STOP LOSS"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    print(f"{motivo} | ROI: {roi_neto:.2f}% | Nuevo Saldo: ${saldo_simulado:.2f}")
                    ops_sim.pop() # Vaciamos la lista para permitir una nueva compra

            # 2. BÚSQUEDA DE NUEVA ENTRADA (Solo si no hay nada abierto)
            else:
                for m in monedas:
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=20)
                    
                    # PATRÓN 6-2-1
                    v_sat = k_1m[-10:-4] 
                    seis_r = all(float(v[4]) < float(v[1]) for v in v_sat) # 6 Rojas
                    seis_v = all(float(v[4]) > float(v[1]) for v in v_sat) # 6 Verdes
                    
                    v_giro = k_1m[-4:-2]
                    dos_v = all(float(v[4]) > float(v[1]) for v in v_giro) # 2 Verdes
                    dos_r = all(float(v[4]) < float(v[1]) for v in v_giro) # 2 Rojas

                    v_dist = k_1m[-2] # Vela de Distancia
                    color_dist = "VERDE" if float(v_dist[4]) > float(v_dist[1]) else "ROJA"

                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                    gatillo = ""

                    if seis_r and dos_v and color_dist == "VERDE": gatillo = "LONG"
                    if seis_v and dos_r and color_dist == "ROJA": gatillo = "SHORT"

                    if gatillo:
                        # Entramos y rompemos el bucle para no buscar más monedas
                        ops_sim.append({'s':m, 'l':gatillo, 'p':p_act, 'monto': saldo_simulado})
                        print(f"🚀 ENTRANDO EN {m} ({gatillo}) | Esperando que esta termine...")
                        break

            # Mostrar estado en consola
            if len(ops_sim) == 0:
                msg = f"📊 SALDO: ${saldo_simulado:.2f} | Acechando SHIB/PEPE... "
            else:
                msg = f"⏳ EN CURSO: {ops_sim[0]['s']} ({ops_sim[0]['l']}) | ROI: {roi_neto:.2f}% "
            
            print(msg, end='\r')

        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__": bot()
