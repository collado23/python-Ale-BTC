import os, time, threading
from binance.client import Client

def bot():
    c = Client() 
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT'] 
    
    saldo_simulado = 31.27
    ops_sim = []
    # --- CONFIGURACIÓN DE PODER ---
    leverage = 15 
    comision_por_movimiento = 0.04 # 0.04% de Binance
    
    print(f"🚀 V3550 - EL LIBRO DINÁMICO (3-5 VELAS O MÁS)")
    print(f"💰 SALDO: ${saldo_simulado:.2f} | APALANCAMIENTO: {leverage}X")

    while True:
        try:
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                
                # Análisis de la última vela cerrada para ver si el zigzag sigue
                v_cerrada = k[-2]
                color_ultimo = "VERDE" if float(v_cerrada[4]) > float(v_cerrada[1]) else "ROJA"
                
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                # Comisión: entrada + salida * leverage
                roi_neto = (diff * 100 * leverage) - (comision_por_movimiento * 2 * leverage)
                
                cierre = False
                # SI GANAMOS (más del 5% ROI), buscamos estirar la racha de 3, 4, 5 velas...
                if roi_neto >= 5.0:
                    # Si el color cambia, significa que la racha de 3-5 velas terminó. CERRAMOS.
                    if (o['l'] == "LONG" and color_ultimo == "ROJA") or \
                       (o['l'] == "SHORT" and color_ultimo == "VERDE"):
                        cierre, motivo = True, "🎯 CIERRE DE RACHA (Zig-Zag cumplido)"
                
                # Stop Loss de protección
                elif roi_neto <= -4.0:
                    cierre, motivo = True, "❌ STOP LOSS (Martillo fallido)"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    ops_sim.remove(o)
                    print(f"{motivo} | ROI: {roi_neto:.2f}% | Saldo: ${saldo_simulado:.2f}")

            # 2. ENTRADA (Solo en los extremos del Zig-Zag)
            if len(ops_sim) < 1:
                for m in monedas:
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=15)
                    v = k_1m[-2]
                    ap, hi, lo, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl - ap) or 0.00000001
                    
                    # Medimos el agotamiento previo
                    precios_v = [float(x[4]) for x in k_1m[:-5]]
                    distancia = (cl - (sum(precios_v)/len(precios_v))) / (sum(precios_v)/len(precios_v)) * 100
                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])

                    if abs(distancia) > 0.42:
                        # LONG: Martillo abajo + Confirmación
                        if (min(cl, ap) - lo) > cuerpo * 3 and p_act > hi:
                            ops_sim.append({'s':m, 'l':'LONG', 'p':p_act, 'monto': saldo_simulado, 't_ms': int(time.time()*1000)})
                            print(f"🔨 LONG: {m}. ¡Buscando racha de verdes!")
                            break
                        # SHORT: Estrella arriba + Confirmación
                        if (hi - max(cl, ap)) > cuerpo * 3 and p_act < lo:
                            ops_sim.append({'s':m, 'l':'SHORT', 'p':p_act, 'monto': saldo_simulado, 't_ms': int(time.time()*1000)})
                            print(f"🛸 SHORT: {m}. ¡Buscando racha de rojas!")
                            break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | 15X | Vigilando...", end='\r')

        except: time.sleep(2)
        time.sleep(2)

if __name__ == "__main__": bot()
