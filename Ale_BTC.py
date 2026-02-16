import os, time
from binance.client import Client

def bot():
    c = Client()
    monedas = ['SHIBUSDT', 'PEPEUSDT']
    saldo_simulado = 27.58 
    ops_sim = []
    leverage = 15 
    
    # Comisiones: 0.04% por operación (entrada + salida = 0.08% total)
    # A 15X, la comisión se come un 1.2% de tu ROI bruto.
    comision_total_roi = 1.2 

    print(f"🎯 PROYECTO 1.5% NETO (SHIB + PEPE)")
    print(f"📊 Objetivo: Ganar en 2-4 velas después de la confirmación")

    while True:
        try:
            if len(ops_sim) > 0:
                o = ops_sim[0]
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                
                # Calculamos ROI BRUTO y le restamos la COMISIÓN para tener el NETO
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_bruto = diff * 100 * leverage
                roi_neto = roi_bruto - comision_total_roi
                
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                v_u, v_a = k[-2], k[-3]
                color_u = "VERDE" if float(v_u[4]) > float(v_u[1]) else "ROJA"
                color_a = "VERDE" if float(v_a[4]) > float(v_a[1]) else "ROJA"

                cierre = False
                # --- ESTRATEGIA DE SALIDA RÁPIDA (2-3 velas) ---
                if roi_neto >= 1.5: 
                    # Si ya tenemos el 1.5% neto y sale UNA sola vela en contra, cerramos.
                    if (o['l'] == "LONG" and color_u == "ROJA") or \
                       (o['l'] == "SHORT" and color_u == "VERDE"):
                        cierre, motivo = True, "💰 1.5% NETO ASEGURADO"
                
                elif roi_neto <= -2.0: # Stop Loss un poco más corto
                    cierre, motivo = True, "⚠️ SL PROTECT"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    print(f"{motivo} | Neto: {roi_neto:.2f}% | Saldo: ${saldo_simulado:.2f}")
                    ops_sim.pop()

            else:
                for m in monedas:
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=20)
                    # Lógica 6-2-1
                    v_sat = k_1m[-10:-4] 
                    s_r = all(float(v[4]) < float(v[1]) for v in v_sat)
                    s_v = all(float(v[4]) > float(v[1]) for v in v_sat)
                    
                    v_giro = k_1m[-4:-2]
                    g_v = all(float(v[4]) > float(v[1]) for v in v_giro)
                    g_r = all(float(v[4]) < float(v[1]) for v in v_giro)

                    v_dist = k_1m[-2]
                    c_dist = "VERDE" if float(v_dist[4]) > float(v_dist[1]) else "ROJA"

                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                    gat = ""
                    if s_r and g_v and c_dist == "VERDE": gat = "LONG"
                    if s_v and g_r and c_dist == "ROJA": gat = "SHORT"

                    if gat:
                        ops_sim.append({'s':m, 'l':gat, 'p':p_act, 'monto': saldo_simulado})
                        print(f"🚀 ENTRADA {m} {gat} | Buscando 1.5% neto...")
                        break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | Esperando racha de 6...      ", end='\r')

        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__": bot()
