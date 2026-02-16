import os, time
from binance.client import Client

def bot():
    c = Client()
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT'] 
    
    saldo_simulado = 27.58 # Arrancamos donde quedó el log
    ops_sim = []
    leverage = 15 
    comision_sim = 0.0004 

    print(f"🕵️ V4500-SIM - FILTRO DE DISTANCIA ACTIVADO")
    print(f"💰 SALDO: ${saldo_simulado:.2f} | Esperando confirmación +1 vela")

    while True:
        try:
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - (comision_sim * 2 * 100 * leverage)
                
                # Velas para salida con distancia
                v_ultima = k[-2]
                v_anterior = k[-3]
                color_u = "VERDE" if float(v_ultima[4]) > float(v_ultima[1]) else "ROJA"
                color_a = "VERDE" if float(v_anterior[4]) > float(v_anterior[1]) else "ROJA"

                cierre = False
                # Si estamos en profit (+1.5%), esperamos que se confirmen 2 velas en contra para salir
                if roi_neto >= 1.5:
                    if (o['l'] == "LONG" and color_u == "ROJA" and color_a == "ROJA") or \
                       (o['l'] == "SHORT" and color_u == "VERDE" and color_a == "VERDE"):
                        cierre, motivo = True, "💰 CIERRE CONFIRMADO (Distancia)"
                
                # Stop Loss más inteligente: si toca -2.5% cerramos al toque
                elif roi_neto <= -2.5:
                    cierre, motivo = True, "⚠️ SL PREVENTIVO"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    ops_sim.remove(o)
                    print(f"{motivo} | ROI: {roi_neto:.2f}% | Saldo: ${saldo_simulado:.2f}")

            # 2. ENTRADA CON VELA DE DISTANCIA
            if len(ops_sim) == 0:
                for m in monedas:
                    # Pedimos más velas para analizar la distancia
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=15)
                    
                    # 1. Saturación (4 velas seguidas en contra)
                    # Tomamos un bloque anterior para dejar la "vela de distancia"
                    v_saturacion = k_1m[-8:-4] 
                    eran_rojas = all(float(v[4]) < float(v[1]) for v in v_saturacion)
                    eran_verdes = all(float(v[4]) > float(v[1]) for v in v_saturacion)
                    
                    # 2. Confirmación de giro (2 velas a favor)
                    v_giro = k_1m[-4:-2]
                    giro_v = all(float(v[4]) > float(v[1]) for v in v_giro)
                    giro_r = all(float(v[4]) < float(v[1]) for v in v_giro)

                    # 3. LA VELA DE DISTANCIA (La última cerrada tiene que mantener el color)
                    v_distancia = k_1m[-2]
                    color_dist = "VERDE" if float(v_distancia[4]) > float(v_distancia[1]) else "ROJA"

                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                    gatillo = ""

                    # Si hubo 4 rojas, luego 2 verdes, y la última sigue siendo verde -> ENTRAMOS
                    if eran_rojas and giro_v and color_dist == "VERDE":
                        gatillo = "LONG"
                    
                    # Si hubo 4 verdes, luego 2 rojas, y la última sigue siendo roja -> ENTRAMOS
                    if eran_verdes and giro_r and color_dist == "ROJA":
                        gatillo = "SHORT"

                    if gatillo:
                        ops_sim.append({'s':m, 'l':gatillo, 'p':p_act, 'monto': saldo_simulado})
                        print(f"🚀 ENTRADA CON DISTANCIA: {gatillo} en {m}")
                        break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | Acechando con filtro de distancia... ", end='\r')

        except: time.sleep(2)
        time.sleep(1)

if __name__ == "__main__": bot()
