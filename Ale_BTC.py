import os, time
from binance.client import Client

def bot():
    c = Client() # Modo Simulación
    monedas = ['SHIBUSDT', 'PEPEUSDT']
    
    saldo_simulado = 27.58 
    ops_sim = [] # Máximo 1 operación a la vez
    leverage = 15 
    
    # Comisiones (0.08% total ida y vuelta). A 15X representa 1.2% del ROI.
    comision_total_roi = 1.2 

    print(f"🔥 PROYECTO MEMES ACTIVADO (SHIB + PEPE)")
    print(f"🎯 ESTRATEGIA: 4 Sat + 2 Giro + 1 Distancia")
    print(f"💰 OBJETIVO: 1.5% NETO por operación")

    while True:
        try:
            # 1. GESTIÓN DE OPERACIÓN ABIERTA
            if len(ops_sim) > 0:
                o = ops_sim[0]
                ticker = c.get_symbol_ticker(symbol=o['s'])
                p_a = float(ticker['price'])
                
                # Cálculo de ROI Neto (Descontando comisiones)
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_bruto = diff * 100 * leverage
                roi_neto = roi_bruto - comision_total_roi
                
                # Análisis de velas para salida
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                v_u = k[-2] # Última cerrada
                color_u = "VERDE" if float(v_u[4]) > float(v_u[1]) else "ROJA"

                cierre = False
                # SALIDA SI YA TENEMOS EL 1.5% NETO Y HAY GIRO
                if roi_neto >= 1.5:
                    if (o['l'] == "LONG" and color_u == "ROJA") or \
                       (o['l'] == "SHORT" and color_u == "VERDE"):
                        cierre, motivo = True, "🎯 PROFIT 1.5% NETO"
                
                # STOP LOSS (Protección ante desplomes)
                elif roi_neto <= -2.5:
                    cierre, motivo = True, "⚠️ SL PROTECT"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    print(f"\n{motivo} | ROI: {roi_neto:.2f}% | Nuevo Saldo: ${saldo_simulado:.2f}")
                    ops_sim.pop()

            # 2. BÚSQUEDA DE ENTRADA (Lógica 4-2-1)
            else:
                for m in monedas:
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=15)
                    
                    # A. SATURACIÓN (4 velas del mismo color)
                    v_sat = k_1m[-8:-4] 
                    s_r = all(float(v[4]) < float(v[1]) for v in v_sat)
                    s_v = all(float(v[4]) > float(v[1]) for v in v_sat)
                    
                    # B. GIRO (2 velas contrarias)
                    v_giro = k_1m[-4:-2]
                    g_v = all(float(v[4]) > float(v[1]) for v in v_giro)
                    g_r = all(float(v[4]) < float(v[1]) for v in v_giro)

                    # C. DISTANCIA (1 vela de confirmación)
                    v_dist = k_1m[-2]
                    c_dist = "VERDE" if float(v_dist[4]) > float(v_dist[1]) else "ROJA"

                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                    gatillo = ""

                    # Si hubo 4 rojas -> 2 verdes -> 1 verde de distancia = COMPRA
                    if s_r and g_v and c_dist == "VERDE": gatillo = "LONG"
                    
                    # Si hubo 4 verdes -> 2 rojas -> 1 roja de distancia = VENTA
                    if s_v and g_r and c_dist == "ROJA": gatillo = "SHORT"

                    if gatillo:
                        ops_sim.append({'s':m, 'l':gatillo, 'p':p_act, 'monto': saldo_simulado})
                        print(f"\n🚀 ENTRADA EN {m} ({gatillo}) | Patrón 4-2-1 Confirmado")
                        break

            # Status en una sola línea para no llenar la consola
            if len(ops_sim) == 0:
                print(f"📊 SALDO: ${saldo_simulado:.2f} | Buscando racha de 4 en SHIB/PEPE...      ", end='\r')
            else:
                print(f"⏳ EN POSICIÓN: {ops_sim[0]['s']} | ROI NETO: {roi_neto:.2f}%      ", end='\r')

        except Exception as e:
            time.sleep(2)
        time.sleep(1)

if __name__ == "__main__": bot()
