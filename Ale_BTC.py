import os, time, threading
from binance.client import Client

def bot():
    c = Client() 
    # Las mejores para Zig-Zag rápido
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT']
    
    saldo_simulado = 31.27
    ops_sim = []
    leverage = 15 
    comision_sim = 0.0004 

    print(f"🦅 V3900 - ESTRATEGIA DE SATURACIÓN SEMANAL")
    print(f"💰 SALDO: ${saldo_simulado:.2f} | 15X | FOCO: RACHAS LARGAS")

    while True:
        try:
            # 1. MONITOR DE LA RACHA (3, 4, 5 velas...)
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                
                # Miramos la vela que acaba de cerrar
                v_cerrada = k[-2]
                color_ultimo = "VERDE" if float(v_cerrada[4]) > float(v_cerrada[1]) else "ROJA"
                
                # ROI Neto (15x y comisiones descontadas)
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - (comision_sim * 2 * 100 * leverage)
                
                cierre = False
                # Si ya estamos en profit, NO cerramos mientras el color sea nuestro amigo
                if roi_neto >= 4.0:
                    # Si el color cambia, se terminó el Zig-Zag, cobramos.
                    if (o['l'] == "LONG" and color_ultimo == "ROJA") or \
                       (o['l'] == "SHORT" and color_ultimo == "VERDE"):
                        cierre, motivo = True, "🎯 RACHA COMPLETADA (Profit)"
                
                # Stop Loss dinámico para no perder lo ganado
                elif roi_neto <= -3.2:
                    cierre, motivo = True, "❌ SL PROTECT"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    ops_sim.remove(o)
                    print(f"{motivo} | ROI: {roi_neto:.2f}% | Saldo: ${saldo_simulado:.2f}")

            # 2. ENTRADA POR SATURACIÓN (Buscamos el giro después de 3 velas previas)
            if len(ops_sim) == 0:
                for m in monedas:
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=10)
                    
                    # Analizamos las 3 velas previas al martillo para ver si hay saturación
                    v1, v2, v3 = k_1m[-5], k_1m[-4], k_1m[-3]
                    v_martillo = k_1m[-2]
                    
                    # Colores previos
                    eran_rojas = all(float(v[4]) < float(v[1]) for v in [v1, v2, v3])
                    eran_verdes = all(float(v[4]) > float(v[1]) for v in [v1, v2, v3])
                    
                    ap, hi, lo, cl = float(v_martillo[1]), float(v_martillo[2]), float(v_martillo[3]), float(v_martillo[4])
                    cuerpo = abs(cl - ap) or 0.00000001
                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])

                    # --- GATILLO DE ALTA PROBABILIDAD ---
                    
                    # LONG: 3 Rojas previas + Martillo abajo + Rotura de Máximo
                    if eran_rojas and (min(cl, ap) - lo) > cuerpo * 2 and p_act > hi:
                        ops_sim.append({'s':m, 'l':'LONG', 'p':p_act, 'monto': saldo_simulado})
                        print(f"🔨 SATURACIÓN BAJISTA en {m}: Entrando LONG para racha...")
                        break

                    # SHORT: 3 Verdes previas + Estrella arriba + Rotura de Mínimo
                    if eran_verdes and (hi - max(cl, ap)) > cuerpo * 2 and p_act < lo:
                        ops_sim.append({'s':m, 'l':'SHORT', 'p':p_act, 'monto': saldo_simulado})
                        print(f"🛸 SATURACIÓN ALCISTA en {m}: Entrando SHORT para racha...")
                        break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | Buscando saturación de velas... ", end='\r')

        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__": bot()
