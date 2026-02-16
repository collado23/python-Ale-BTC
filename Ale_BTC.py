import os, time, threading
from binance.client import Client

def bot():
    c = Client() 
    # Solo Altcoins volátiles para scalping rápido
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT'] 
    
    saldo_simulado = 31.27
    ops_sim = []
    leverage = 15 
    comision_sim = 0.0004 # 0.04% por movimiento (0.08% total)

    print(f"🔥 V3800 - SCALPING EXPLOSIVO (ALTS ONLY)")
    print(f"💰 SALDO: ${saldo_simulado:.2f} | APALANCAMIENTO: {leverage}X")
    print(f"🚫 BTC/ETH ELIMINADOS - FOCO EN VOLATILIDAD")

    while True:
        try:
            # 1. GESTIÓN DE LA POSICIÓN ÚNICA
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                
                # Análisis de la última vela cerrada para ver si el zigzag sigue
                v_cerrada = k[-2]
                color_ultimo = "VERDE" if float(v_cerrada[4]) > float(v_cerrada[1]) else "ROJA"
                
                # ROI Neto con comisiones (15x * 0.08% = 1.2% de ROI de costo)
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - (comision_sim * 2 * 100 * leverage)
                
                cierre = False
                # ESTRATEGIA DE RACHA: Si ganamos > 4%, aguantamos mientras el color acompañe
                if roi_neto >= 4.0:
                    if (o['l'] == "LONG" and color_ultimo == "ROJA") or \
                       (o['l'] == "SHORT" and color_ultimo == "VERDE"):
                        cierre, motivo = True, "🎯 FIN DE RACHA (Cobro)"
                
                # Stop Loss rápido para proteger el capital
                elif roi_neto <= -3.5:
                    cierre, motivo = True, "❌ SL (Cambio de impulso)"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    ops_sim.remove(o)
                    print(f"{motivo} | ROI FINAL: {roi_neto:.2f}% | Saldo: ${saldo_simulado:.2f}")

            # 2. ENTRADA RÁPIDA (Sin BTC/ETH)
            if len(ops_sim) == 0:
                for m in monedas:
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=10)
                    v = k_1m[-2] # El Martillo
                    ap, hi, lo, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl - ap) or 0.00000001
                    
                    # Filtro de distancia (Agotamiento de 0.28%)
                    precios_v = [float(x[4]) for x in k_1m[:-3]]
                    distancia = (cl - (sum(precios_v)/len(precios_v))) / (sum(precios_v)/len(precios_v)) * 100
                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])

                    # --- GATILLO SCALPER (Mecha 2x Cuerpo) ---
                    # LONG
                    if (min(cl, ap) - lo) > cuerpo * 2 and p_act > hi:
                        ops_sim.append({'s':m, 'l':'LONG', 'p':p_act, 'monto': saldo_simulado})
                        print(f"🚀 GATILLO LONG: {m} (100% Capital). ¡Buscando velas verdes!")
                        break
                    # SHORT
                    if (hi - max(cl, ap)) > cuerpo * 2 and p_act < lo:
                        ops_sim.append({'s':m, 'l':'SHORT', 'p':p_act, 'monto': saldo_simulado})
                        print(f"🚀 GATILLO SHORT: {m} (100% Capital). ¡Buscando velas rojas!")
                        break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | 15X | Esperando Martillo en Alts... ", end='\r')

        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__": bot()
