import os, time
from binance.client import Client

def bot():
    c = Client() # Simulación (no necesita keys reales para lectura)
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT'] 
    
    saldo_simulado = 30.36 # El saldo donde quedamos tras el SL
    ops_sim = []
    leverage = 15 
    comision_sim = 0.0004 

    print(f"🧪 V4300-SIM - TESTEO DE DOBLE CONFIRMACIÓN")
    print(f"💰 SALDO SIMULADO: ${saldo_simulado:.2f} | 15X")

    while True:
        try:
            # 1. GESTIÓN DE LA POSICIÓN (Salida por doble vela)
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                k = c.get_klines(symbol=o['s'], interval='1m', limit=6)
                
                # ROI Neto
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - (comision_sim * 2 * 100 * leverage)
                
                # Análisis de las últimas 2 velas cerradas
                v_c1 = k[-2] # Última cerrada
                v_c2 = k[-3] # Penúltima cerrada
                color1 = "VERDE" if float(v_c1[4]) > float(v_c1[1]) else "ROJA"
                color2 = "VERDE" if float(v_c2[4]) > float(v_c2[1]) else "ROJA"

                cierre = False
                # Si ganamos > 3.5%, esperamos a que 2 velas cambien de color para salir
                if roi_neto >= 3.5:
                    if (o['l'] == "LONG" and color1 == "ROJA" and color2 == "ROJA") or \
                       (o['l'] == "SHORT" and color1 == "VERDE" and color2 == "VERDE"):
                        cierre, motivo = True, "🎯 PROFIT (Giro confirmado)"
                
                # Stop Loss más corto para proteger
                elif roi_neto <= -3.0:
                    cierre, motivo = True, "❌ SL PROTECT"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    ops_sim.remove(o)
                    print(f"{motivo} | ROI: {roi_neto:.2f}% | Nuevo Saldo: ${saldo_simulado:.2f}")

            # 2. ENTRADA POR DOBLE CONFIRMACIÓN
            if len(ops_sim) == 0:
                for m in monedas:
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=12)
                    
                    # 1. Buscamos saturación (4 velas seguidas)
                    v_previa = k_1m[-7:-3] 
                    eran_rojas = all(float(v[4]) < float(v[1]) for v in v_previa)
                    eran_verdes = all(float(v[4]) > float(v[1]) for v in v_previa)
                    
                    # 2. Buscamos confirmación de giro (2 velas seguidas al revés)
                    v_giro = k_1m[-3:-1] 
                    giro_verde = all(float(v[4]) > float(v[1]) for v in v_giro)
                    giro_rojo = all(float(v[4]) < float(v[1]) for v in v_giro)

                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])

                    if eran_rojas and giro_verde:
                        ops_sim.append({'s':m, 'l':'LONG', 'p':p_act, 'monto': saldo_simulado})
                        print(f"🚀 ENTRADA SIM (2 Velas Verdes): {m}")
                        break
                    
                    if eran_verdes and giro_rojo:
                        ops_sim.append({'s':m, 'l':'SHORT', 'p':p_act, 'monto': saldo_simulado})
                        print(f"🚀 ENTRADA SIM (2 Velas Rojas): {m}")
                        break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | Filtro: 4 contra 2...       ", end='\r')

        except: time.sleep(2)
        time.sleep(1)

if __name__ == "__main__": bot()
