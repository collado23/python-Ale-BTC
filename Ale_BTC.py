import os, time, threading
from binance.client import Client

def bot():
    c = Client() 
    # Agregamos monedas volátiles para que haya acción
    monedas = ['SHIBUSDT', 'PEPEUSDT', 'DOGEUSDT', 'XRPUSDT', 'SOLUSDT']
    saldo_sim = 27.58
    ops_sim = []
    leverage = 15
    comision_roi = 1.2 

    print(f"🔥 MODO MULTI-MONEDA ACTIVADO (5 MONEDAS)")
    print(f"🎯 BUSCANDO: 2 Sat + 1 Giro + 1 Distancia")

    while True:
        try:
            if len(ops_sim) > 0:
                o = ops_sim[0]
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi_neto = (diff * 100 * leverage) - comision_roi
                
                if roi_neto >= 0.8 or roi_neto <= -1.2:
                    saldo_sim += (o['monto'] * roi_neto / 100)
                    print(f"\n✅ CIERRE EN {o['s']} | NETO: {roi_neto:.2f}% | SALDO: ${saldo_sim:.2f}")
                    ops_sim.pop()
            else:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=10)
                    v_sat = k[-5:-3]
                    s_r = all(float(v[4]) < float(v[1]) for v in v_sat)
                    s_v = all(float(v[4]) > float(v[1]) for v in v_sat)
                    v_giro = k[-3]
                    g_v = float(v_giro[4]) > float(v_giro[1])
                    g_r = float(v_giro[4]) < float(v_giro[1])
                    v_dist = k[-2]
                    c_dist = "VERDE" if float(v_dist[4]) > float(v_dist[1]) else "ROJA"

                    if (s_r and g_v and c_dist == "VERDE") or (s_v and g_r and c_dist == "ROJA"):
                        lado = "LONG" if (s_r and g_v) else "SHORT"
                        ops_sim.append({'s':m, 'l':lado, 'p':float(c.get_symbol_ticker(symbol=m)['price']), 'monto': saldo_sim})
                        print(f"\n🚀 DISPARO EN {m} ({lado})")
                        break

            print(f"📊 SIM: ${saldo_sim:.2f} | Monitoreando 5 monedas...      ", end='\r')

        except: time.sleep(2)
        time.sleep(1)

if __name__ == "__main__": bot()
