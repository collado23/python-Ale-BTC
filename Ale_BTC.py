import os, time, threading
from binance.client import Client

def bot():
    c = Client()
    monedas = ['SHIBUSDT', 'PEPEUSDT']
    saldo_sim = 22.19  # Tu saldo actual tras el error
    ops_sim = []
    leverage = 15
    comision_roi = 1.2 
    ultimo_trade_time = 0

    print(f"🛡️ MODO FRANCOTIRADOR CORREGIDO (Anti-Sangría)")
    print(f"💰 Saldo inicial: ${saldo_sim:.2f}")

    while True:
        try:
            ahora = time.time()
            if len(ops_sim) > 0:
                o = ops_sim[0]
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - comision_roi
                
                # --- GESTIÓN DE SALIDA INTELIGENTE ---
                # Solo cerramos si hay ganancia real o una pérdida mayor al margen de entrada
                if roi_neto >= 1.0: 
                    motivo = "✅ PROFIT"
                elif roi_neto <= -3.5: # Stop Loss más largo para aguantar el movimiento
                    motivo = "❌ STOP LOSS"
                else: motivo = None

                if motivo:
                    saldo_sim += (o['monto'] * roi_neto / 100)
                    print(f"\n{motivo} en {o['s']} | Neto: {roi_neto:.2f}% | Saldo: ${saldo_sim:.2f}")
                    ops_sim.pop()
                    ultimo_trade_time = ahora # Activamos descanso
            
            # Solo busca entrada si pasaron 5 min del último trade
            elif ahora - ultimo_trade_time > 300: 
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=10)
                    # Volvemos a 3 velas para mayor seguridad
                    v_sat = k[-6:-3]
                    s_r = all(float(v[4]) < float(v[1]) for v in v_sat)
                    s_v = all(float(v[4]) > float(v[1]) for v in v_sat)
                    
                    v_giro = k[-3]
                    g_v = float(v_giro[4]) > float(v_giro[1])
                    g_r = float(v_giro[4]) < float(v_giro[1])
                    
                    v_dist = k[-2] # Tu vela de distancia
                    c_dist = "VERDE" if float(v_dist[4]) > float(v_dist[1]) else "ROJA"

                    if (s_r and g_v and c_dist == "VERDE") or (s_v and g_r and c_dist == "ROJA"):
                        p_act = float(c.get_symbol_ticker(symbol=m)['price'])
                        lado = "LONG" if (s_r and g_v) else "SHORT"
                        ops_sim.append({'s':m, 'l':lado, 'p':p_act, 'monto': saldo_sim})
                        print(f"\n🚀 DISPARO SEGURO EN {m} ({lado})")
                        break

            print(f"📊 SIM: ${saldo_sim:.2f} | Descanso/Acecho activo...      ", end='\r')

        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
