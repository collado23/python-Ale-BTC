import os, time, threading
from binance.client import Client

def bot():
    c = Client() 
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT'] 
    
    # --- VARIABLES DE SIMULACIÓN AJUSTADAS ---
    saldo_simulado = 30.0
    ops_sim = []
    espera_moneda = {} # Para evitar entrar mil veces en la misma
    leverage = 15
    
    print(f"🎮 V2900 SIMULADOR PROFESIONAL | $30.00 | 15X")
    print(f"🛡️ STOP LOSS AJUSTADO PARA EVITAR CIERRES RÁPIDOS")

    while True:
        try:
            # 1. GESTIÓN DE POSICIONES
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - 0.5 # Descuento de comisión fija
                
                # Salidas más largas para que la operación "respire"
                if roi_neto >= 10.0 or roi_neto <= -4.0:
                    ganancia_perdida = (o['monto'] * roi_neto / 100)
                    saldo_simulado += ganancia_perdida
                    espera_moneda[o['s']] = time.time() + 300 # 5 min de bloqueo
                    ops_sim.remove(o)
                    estado = "💰 PROFIT" if roi_neto > 0 else "❌ STOP"
                    print(f"{estado}: {o['s']} | ROI: {roi_neto:.2f}% | Saldo: ${saldo_simulado:.2f}")

            # 2. ENTRADA CON CALIBRE MÁS ESTRICTO
            if len(ops_sim) < 1:
                for m in monedas:
                    # Si la moneda está en tiempo de espera, saltar
                    if m in espera_moneda and time.time() < espera_moneda[m]: continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=20)
                    v = k[-2]
                    ap, hi, lo, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl - ap) or 0.00000001
                    m_sup, m_inf = hi - max(cl, ap), min(cl, ap) - lo
                    
                    precios = [float(x[4]) for x in k[:-2]]
                    distancia = (max(precios) - min(precios)) / min(precios) * 100

                    # Martillo de "Libro Puro": Mecha muy larga, cuerpo chico
                    es_m = (m_inf > cuerpo * 3.0) and (m_sup < cuerpo * 0.4)
                    es_i = (m_sup > cuerpo * 3.0) and (m_inf < cuerpo * 0.4)

                    if distancia > 0.50: # Exigimos más recorrido previo
                        p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                        
                        if es_m and p_act > hi:
                            ops_sim.append({'s':m, 'l':'LONG', 'p':p_act, 'monto': saldo_simulado})
                            print(f"🔨 [SIM] MARTILLO REAL en {m}. Entrando LONG.")
                            break
                        if es_i and p_act < lo:
                            ops_sim.append({'s':m, 'l':'SHORT', 'p':p_act, 'monto': saldo_simulado})
                            print(f"🛸 [SIM] ESTRELLA REAL en {m}. Entrando SHORT.")
                            break

            print(f"📊 SALDO: ${saldo_simulado:.2f} | Activas: {len(ops_sim)} | Esperando señal clara...", end='\r')

        except: time.sleep(5)
        time.sleep(2)

if __name__ == "__main__": bot()
