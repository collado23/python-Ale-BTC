import os, time, threading
from binance.client import Client

def bot():
    c = Client() 
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT']
    
    saldo_simulado = 31.27
    ops_sim = []
    leverage = 15
    
    print(f"🔥 V3500 - MODO EXPANSIÓN (3, 4, 5 VELAS O MÁS)")
    print(f"💰 SALDO: ${saldo_simulado:.2f} | Ganando mientras el color siga...")

    while True:
        try:
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                
                # Pedimos las velas ocurridas desde la entrada
                k = c.get_klines(symbol=o['s'], interval='1m', limit=10)
                velas_nuevas = [v for v in k if int(v[0]) > o['t_ms']]
                
                # Identificamos el color de la ÚLTIMA vela cerrada
                ultima_vela_color = "VERDE" if float(k[-2][4]) > float(k[-2][1]) else "ROJA"
                
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - 0.6
                
                cierre = False
                motivo = ""

                # --- LÓGICA DE EXPANSIÓN DE GANANCIA ---
                
                # Si ya tenemos una ganancia decente (ej. 5% ROI)
                if roi_neto >= 5.0:
                    # REGLA DE ORO: Si la última vela cambió de color, cerramos YA para asegurar
                    if (o['l'] == "LONG" and ultima_vela_color == "ROJA") or \
                       (o['l'] == "SHORT" and ultima_vela_color == "VERDE"):
                        cierre, motivo = True, f"✅ CIERRE POR CAMBIO DE COLOR (Velas: {len(velas_nuevas)})"
                    else:
                        # Si el color sigue a favor, NO CIERRA. Sigue ganando 5, 6, 7 velas...
                        pass 

                # Stop Loss de protección (por si el martillo falla de entrada)
                if roi_neto <= -4.0:
                    cierre, motivo = True, "❌ STOP LOSS"

                if cierre:
                    saldo_simulado += (o['monto'] * roi_neto / 100)
                    ops_sim.remove(o)
                    print(f"{motivo} | ROI: {roi_neto:.2f}% | Saldo Final: ${saldo_simulado:.2f}")

            # 2. ENTRADA (El martillo que arranca el movimiento)
            if len(ops_sim) < 1:
                for m in monedas:
                    k_1m = c.get_klines(symbol=m, interval='1m', limit=15)
                    v_m = k_1m[-2]
                    ap, hi, lo, cl = float(v_m[1]), float(v_m[2]), float(v_m[3]), float(v_m[4])
                    cuerpo = abs(cl - ap) or 0.00000001
                    p_act = float(c.get_symbol_ticker(symbol=m)['price'])

                    # Medimos el pico previo para entrar en el lugar justo
                    precios = [float(x[4]) for x in k_1m[:-5]]
                    distancia = (cl - (sum(precios)/len(precios))) / (sum(precios)/len(precios)) * 100

                    # Buscamos el Martillo de Libro para iniciar la racha
                    if abs(distancia) > 0.40:
                        # LONG: Martillo abajo. Esperamos racha de VERDES
                        if (min(cl, ap) - lo) > cuerpo * 3 and p_act > hi:
                            ops_sim.append({'s':m, 'l':'LONG', 'p':p_act, 'monto': saldo_simulado, 't_ms': int(time.time()*1000)})
                            print(f"🔨 INICIO RACHA LONG: {m}. ¡Que sigan las verdes!")
                            break
                        # SHORT: Estrella arriba. Esperamos racha de ROJAS
                        if (hi - max(cl, ap)) > cuerpo * 3 and p_act < lo:
                            ops_sim.append({'s':m, 'l':'SHORT', 'p':p_act, 'monto': saldo_simulado, 't_ms': int(time.time()*1000)})
                            print(f"🛸 INICIO RACHA SHORT: {m}. ¡Que sigan las rojas!")
                            break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | Velas a favor: {len(ops_sim)}...", end='\r')

        except: time.sleep(2)
        time.sleep(2)

if __name__ == "__main__": bot()
