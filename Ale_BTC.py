import os, time, threading
from binance.client import Client

def bot():
    c = Client() 
    # Monedas con mucho movimiento para Scalping rápido
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT', 'BTCUSDT', 'ETHUSDT'] 
    
    saldo_simulado = 31.27
    ops_sim = []
    leverage = 15 
    comision_sim = 0.0004 # 0.04% (Binance VIP0)

    print(f"🎯 V3700 - MODO FRANCOTIRADOR (100% Capital)")
    print(f"💰 SALDO: ${saldo_simulado:.2f} | 15X | UNA SOLA OPERACIÓN")

    while True:
        try:
            # 1. GESTIÓN DE LA ÚNICA POSICIÓN
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                
                # Analizamos el color de la vela cerrada para el Zig-Zag
                v_cerrada = k[-2]
                color_ultimo = "VERDE" if float(v_cerrada[4]) > float(v_cerrada[1]) else "ROJA"
                
                # Cálculo de ROI Neto (Descontando comisiones de entrada y salida)
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - (comision_sim * 2 * 100 * leverage)
                
                cierre = False
                # Si vamos ganando, estiramos la racha de 3, 4, 5 velas...
                if roi_neto >= 4.0:
                    # Si el color de la vela cambia, cortamos y cobramos la racha
                    if (o['l'] == "LONG" and color_ultimo == "ROJA") or \
                       (o['l'] == "SHORT" and color_ultimo == "VERDE"):
                        cierre, motivo = True, "🎯 RACHA COMPLETADA (Cobro)"
                
                # Stop Loss ajustado para no quemar el saldo
                elif roi_neto <= -3.5:
                    cierre, motivo = True, "❌ SL (Cambio de Zig-Zag)"

                if cierre:
                    ganancia_real = (o['monto'] * roi_neto / 100)
                    saldo_simulado += ganancia_real
                    ops_sim.remove(o)
                    print(f"{motivo} | ROI: {roi_neto:.2f}% | Saldo Nuevo: ${saldo_simulado:.2f}")

            # 2. BÚSQUEDA DE LA PRÓXIMA OPORTUNIDAD (Solo si no hay nada abierto)
            if len(ops_sim) == 0:
                for m in monedas:
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=10)
                    v = k_1m[-2] # Vela del martillo
                    ap, hi, lo, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl - ap) or 0.00000001
                    
                    # Filtro de distancia suave para Scalping Real (0.25%)
                    precios_v = [float(x[4]) for x in k_1m[:-3]]
                    distancia = (cl - (sum(precios_v)/len(precios_v))) / (sum(precios_v)/len(precios_v)) * 100
                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])

                    # --- GATILLO DEL LIBRO (Mecha 2x Cuerpo) ---
                    # LONG
                    if (min(cl, ap) - lo) > cuerpo * 2 and p_act > hi:
                        ops_sim.append({'s':m, 'l':'LONG', 'p':p_act, 'monto': saldo_simulado, 't_ms': int(time.time()*1000)})
                        print(f"🚀 ENTRANDO 100% LONG: {m} | Buscando racha verde...")
                        break
                    # SHORT
                    if (hi - max(cl, ap)) > cuerpo * 2 and p_act < lo:
                        ops_sim.append({'s':m, 'l':'SHORT', 'p':p_act, 'monto': saldo_simulado, 't_ms': int(time.time()*1000)})
                        print(f"🚀 ENTRANDO 100% SHORT: {m} | Buscando racha roja...")
                        break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | Buscando el mejor martillo...    ", end='\r')

        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__": bot()
