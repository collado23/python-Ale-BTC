import os, time, threading
from binance.client import Client

def bot():
    # Usamos la API solo para LEER precios, no para operar real
    c = Client() 
    
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT'] 
    
    # --- VARIABLES DE SIMULACIÓN ---
    saldo_simulado = 30.0
    ops_sim = []
    leverage = 15
    comision_sim = 0.0004 # 0.04% por operación (entrada y salida)
    
    print(f"🎮 MODO SIMULACIÓN ACTIVADO")
    print(f"💰 SALDO INICIAL SIMULADO: ${saldo_simulado:.2f} | 15X")
    print(f"📖 BUSCANDO MARTILLOS DEL LIBRO...")
    print("-" * 40)

    while True:
        try:
            # 1. GESTIÓN DE POSICIONES SIMULADAS
            for o in ops_sim[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                
                # Cálculo de ROI para el simulador
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_bruto = diff * 100 * leverage
                # Restamos comisión simulada (entrada + salida * leverage)
                roi_neto = roi_bruto - (comision_sim * 2 * 100 * leverage)
                
                # Reglas de salida del Libro (Profit 7% o Stop 2%)
                if roi_neto >= 7.0 or roi_neto <= -2.0:
                    ganancia_perdida = (o['monto'] * roi_neto / 100)
                    saldo_simulado += ganancia_perdida
                    ops_sim.remove(o)
                    print(f"✅ CIERRE SIMULADO: {o['s']} | ROI: {roi_neto:.2f}% | Saldo: ${saldo_simulado:.2f}")

            # 2. ANÁLISIS DE ENTRADA (Midiendo velas)
            if len(ops_sim) < 1:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=20)
                    v = k[-2]
                    
                    ap, hi, lo, cl = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(float(cl) - float(ap)) or 0.00000001
                    m_sup, m_inf = float(hi) - max(float(cl), float(ap)), min(float(cl), float(ap)) - float(lo)
                    
                    # Distancia de agotamiento
                    precios = [float(x[4]) for x in k[:-2]]
                    distancia = (max(precios) - min(precios)) / min(precios) * 100

                    # Filtro de Martillo estricto
                    es_m = (m_inf > cuerpo * 2.5) and (m_sup < cuerpo * 0.5)
                    es_i = (m_sup > cuerpo * 2.5) and (m_inf < cuerpo * 0.5)

                    if distancia > 0.40:
                        p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                        
                        # Entrada LONG
                        if es_m and float(cl) < max(precios) and p_act > float(hi):
                            ops_sim.append({'s':m, 'l':'LONG', 'p':p_act, 'monto': saldo_simulado})
                            print(f"🔨 [SIM] MARTILLO en {m}. Entrando LONG a {p_act}")
                            break

                        # Entrada SHORT
                        if es_i and float(cl) > min(precios) and p_act < float(lo):
                            ops_sim.append({'s':m, 'l':'SHORT', 'p':p_act, 'monto': saldo_simulado})
                            print(f"🛸 [SIM] ESTRELLA en {m}. Entrando SHORT a {p_act}")
                            break

            print(f"📊 SIMULADO: ${saldo_simulado:.2f} | Activas: {len(ops_sim)} | Buscando... ", end='\r')

        except Exception as e:
            time.sleep(5)
        
        time.sleep(2)

if __name__ == "__main__":
    bot()
