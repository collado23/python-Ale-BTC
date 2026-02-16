import os, time
from binance.client import Client 

def bot():
    c = Client() # Modo simulación
    simbolo = 'PEPEUSDT'
    
    # --- PARÁMETROS PEPE ---
    saldo_simulado = 27.58 
    ops_sim = []
    leverage = 15 
    comision_sim = 0.0004 

    print(f"🐸 PROYECTO PEPE 6-2-1 ACTIVADO")
    print(f"📡 Analizando rachas explosivas en PEPE")
    print(f"💰 Saldo inicial: ${saldo_simulado:.2f}")

    while True:
        try:
            # 1. GESTIÓN DE POSICIÓN
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - (comision_sim * 2 * 100 * leverage)
                
                # Salida por doble confirmación (Distancia)
                v_u = k[-2]
                v_a = k[-3]
                color_u = "VERDE" if float(v_u[4]) > float(v_u[1]) else "ROJA"
                color_a = "VERDE" if float(v_a[4]) > float(v_a[1]) else "ROJA"

                cierre = False
                if roi_neto >= 2.5: # PEPE da más profit rápido, le subimos la vara
                    if (o['l'] == "LONG" and color_u == "ROJA" and color_a == "ROJA") or \
                       (o['l'] == "SHORT" and color_u == "VERDE" and color_a == "VERDE"):
                        cierre, motivo = True, "🎯 PEPE PROFIT (Giro 2 velas)"
                
                elif roi_neto <= -2.5:
                    cierre, motivo = True, "⚠️ PEPE SL"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    ops_sim.remove(o)
                    print(f"{motivo} | ROI: {roi_neto:.2f}% | Saldo: ${saldo_simulado:.2f}")

            # 2. ENTRADA PEPE (6-2-1)
            if len(ops_sim) == 0:
                k_1m = c.get_klines(symbol=simbolo, interval='1m', limit=20)
                
                # A. SATURACIÓN (6 VELAS)
                v_sat = k_1m[-10:-4] 
                seis_rojas = all(float(v[4]) < float(v[1]) for v in v_sat)
                seis_verdes = all(float(v[4]) > float(v[1]) for v in v_sat)
                
                # B. GIRO (2 VELAS)
                v_giro = k_1m[-4:-2]
                dos_v = all(float(v[4]) > float(v[1]) for v in v_giro)
                dos_r = all(float(v[4]) < float(v[1]) for v in v_giro)

                # C. DISTANCIA (1 VELA)
                v_dist = k_1m[-2]
                dist_v = float(v_dist[4]) > float(v_dist[1])
                dist_r = float(v_dist[4]) < float(v_dist[1])

                p_act = float(c.get_symbol_ticker(symbol=simbolo)['price'])
                gatillo = ""

                if seis_rojas and dos_v and dist_v: gatillo = "LONG"
                if seis_verdes and dos_r and dist_r: gatillo = "SHORT"

                if gatillo:
                    ops_sim.append({'s':simbolo, 'l':gatillo, 'p':p_act, 'monto': saldo_simulado})
                    print(f"🚀 ENTRADA PEPE {gatillo}: Patrón 6-2-1")

            print(f"📊 PEPE: ${saldo_simulado:.2f} | Buscando racha de 6...       ", end='\r')

        except: time.sleep(1)

if __name__ == "__main__": bot()
