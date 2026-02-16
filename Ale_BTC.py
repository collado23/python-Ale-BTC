import os, time
from binance.client import Client

def bot():
    # Modo simulación (lectura de datos públicos)
    c = Client()
    simbolo = 'XRPUSDT'
    
    # --- PARÁMETROS DEL PROYECTO ---
    saldo_simulado = 27.58 
    ops_sim = []
    leverage = 15 
    comision_sim = 0.0004 

    print(f"🔥 PROYECTO XRP 5-2-1 ACTIVADO")
    print(f"📡 Monitoreando XRP para COMPRAS y VENTAS")
    print(f"💰 Saldo Actual: ${saldo_simulado:.2f} | Apalancamiento: {leverage}X")

    while True:
        try:
            # 1. GESTIÓN DE OPERACIONES ABIERTAS
            for o in ops_sim[:]:
                ticker = c.get_symbol_ticker(symbol=o['s'])
                p_a = float(ticker['price'])
                
                # Calculamos ROI Neto
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - (comision_sim * 2 * 100 * leverage)
                
                # Análisis de velas para salida (distancia)
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                v_ultima = k[-2]
                v_anterior = k[-3]
                color_u = "VERDE" if float(v_ultima[4]) > float(v_ultima[1]) else "ROJA"
                color_a = "VERDE" if float(v_anterior[4]) > float(v_anterior[1]) else "ROJA"

                cierre = False
                # SALIDA POR PROFIT: Si ganamos > 1.5% y vemos 2 velas en contra, cerramos.
                if roi_neto >= 1.5:
                    if (o['l'] == "LONG" and color_u == "ROJA" and color_a == "ROJA") or \
                       (o['l'] == "SHORT" and color_u == "VERDE" and color_a == "VERDE"):
                        cierre, motivo = True, "🎯 PROFIT (Giro confirmado)"
                
                # STOP LOSS RÁPIDO: Protegemos el saldo a los -2.5%
                elif roi_neto <= -2.5:
                    cierre, motivo = True, "⚠️ SL PROTECT"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    ops_sim.remove(o)
                    print(f"{motivo} | ROI: {roi_neto:.2f}% | Nuevo Saldo: ${saldo_simulado:.2f}")

            # 2. BÚSQUEDA DE ENTRADA (LÓGICA 5-2-1)
            if len(ops_sim) == 0:
                k_1m = c.get_klines(symbol=simbolo, interval='1m', limit=15)
                
                # A. SATURACIÓN (5 velas seguidas)
                v_sat = k_1m[-9:-4] 
                cinco_rojas = all(float(v[4]) < float(v[1]) for v in v_sat)
                cinco_verdes = all(float(v[4]) > float(v[1]) for v in v_sat)
                
                # B. GIRO (2 velas contrarias)
                v_giro = k_1m[-4:-2]
                dos_verdes = all(float(v[4]) > float(v[1]) for v in v_giro)
                dos_rojas = all(float(v[4]) < float(v[1]) for v in v_giro)

                # C. DISTANCIA (1 vela de confirmación)
                v_dist = k_1m[-2]
                color_dist = "VERDE" if float(v_dist[4]) > float(v_dist[1]) else "ROJA"

                p_act = float(c.get_symbol_ticker(symbol=simbolo)['price'])
                gatillo = ""

                # COMPRA: 5 rojas -> 2 verdes -> 1 verde (distancia)
                if cinco_rojas and dos_verdes and color_dist == "VERDE":
                    gatillo = "LONG"
                
                # VENTA: 5 verdes -> 2 rojas -> 1 roja (distancia)
                if cinco_verdes and dos_rojas and color_dist == "ROJA":
                    gatillo = "SHORT"

                if gatillo:
                    ops_sim.append({'s':simbolo, 'l':gatillo, 'p':p_act, 'monto': saldo_simulado})
                    print(f"🚀 ENTRADA XRP {gatillo}: Saturación 5 + Giro 2 + Distancia 1")

            print(f"📊 XRP: ${saldo_simulado:.2f} | Buscando señal 5-2-1...      ", end='\r')

        except Exception as e:
            time.sleep(2)
        time.sleep(1)

if __name__ == "__main__": bot()
