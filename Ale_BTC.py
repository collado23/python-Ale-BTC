import os, time, threading
from binance.client import Client

def bot():
    c = Client() 
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT']
    
    saldo_simulado = 31.27 # Arrancamos con lo que ya ganaste
    ops_sim = []
    leverage = 15
    
    print(f"⏱️ V3000 - ANÁLISIS DE VELAS RÁPIDAS (3-5 min)")
    print(f"💰 SALDO ACTUAL: ${saldo_simulado:.2f}")

    while True:
        try:
            # 1. GESTIÓN DE POSICIONES CON RELOJ
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                minutos_transcurridos = int((time.time() - o['t_inicio']) / 60)
                
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - 0.6 # Comisión

                # --- LÓGICA DE 3 A 5 VELAS ---
                # Si llega al 4% de ganancia de saldo (aprox 7% ROI) en cualquier momento, CIERRA
                if roi_neto >= 7.0:
                    motivo = f"🎯 PROFIT RÁPIDO ({minutos_transcurridos} min)"
                    cierre = True
                # Si pasan más de 5 velas y no estamos en profit claro, cerramos para no arriesgar
                elif minutos_transcurridos >= 5 and roi_neto < 1.0:
                    motivo = "⏳ TIEMPO AGOTADO (Señal débil)"
                    cierre = True
                # Stop Loss de emergencia
                elif roi_neto <= -3.0:
                    motivo = "❌ STOP LOSS"
                    cierre = True
                else:
                    cierre = False

                if cierre:
                    ganancia_perdida = (o['monto'] * roi_neto / 100)
                    saldo_simulado += ganancia_perdida
                    ops_sim.remove(o)
                    print(f"{motivo} en {o['s']} | ROI: {roi_neto:.2f}% | Saldo: ${saldo_simulado:.2f}")

            # 2. ENTRADA (Mismo calibre del Libro)
            if len(ops_sim) < 1:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=15)
                    v = k[-2]
                    ap, hi, lo, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl - ap) or 0.00000001
                    m_sup, m_inf = hi - max(cl, ap), min(cl, ap) - lo
                    
                    precios = [float(x[4]) for x in k[:-2]]
                    distancia = (max(precios) - min(precios)) / min(precios) * 100

                    # El Martillo tiene que ser CLARO (3x el cuerpo)
                    if distancia > 0.45:
                        p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                        # LONG
                        if (m_inf > cuerpo * 3) and p_act > hi:
                            ops_sim.append({'s':m, 'l':'LONG', 'p':p_act, 'monto': saldo_simulado, 't_inicio': time.time()})
                            print(f"🔨 ENTRADA LONG: {m} (Buscando explosión en 5 velas)")
                            break
                        # SHORT
                        if (m_sup > cuerpo * 3) and p_act < lo:
                            ops_sim.append({'s':m, 'l':'SHORT', 'p':p_act, 'monto': saldo_simulado, 't_inicio': time.time()})
                            print(f"🛸 ENTRADA SHORT: {m} (Buscando explosión en 5 velas)")
                            break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | Velas transcurridas: {int((time.time() - ops_sim[0]['t_inicio'])/60) if ops_sim else 0} min", end='\r')

        except: time.sleep(2)
        time.sleep(2)

if __name__ == "__main__": bot()
