import os, time, threading
from binance.client import Client

# --- 🚀 MOTOR V146 ALE - VERSIÓN FINAL SALTO 1.5% ---
def bot():
    c = Client()
    cap = 10.0  # Tu capital de prueba
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0

    print(f"🐊 SIM V146 FINAL | SALTO 15X AL 1.5% | PISO INICIAL 1.0%")

    while True:
        t_l = time.time()
        ahora = time.time()
        
        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # ROI Neto (ya restando el -0.90% de comisión)
                roi = (diff * 100 * o['x']) - 0.90
                ganancia_usd = cap * (roi / 100)
                
                # 🔥 EL SALTO QUE ME PEDISTE: AL 1.5%
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.0  # <--- PROTECCIÓN AL 1.0%
                    print(f"\n🚀 SALTO A 15X (1.5% TOCADO): {o['s']}")

                # 🛡️ EL ESCALADOR (Mantiene margen de 0.5%)
                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0: n_p = 24.5
                    elif roi >= 20.0: n_p = 19.5
                    elif roi >= 15.0: n_p = 14.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 5.0:  n_p = 4.5
                    elif roi >= 2.5:  n_p = 2.0
                    elif roi >= 2.0:  n_p = 1.5 # <--- ESCALÓN INTERMEDIO
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ ESCALADOR: {o['s']} subió piso a {o['piso']}%")

                    # CIERRE POR PISO (GANANCIA)
                    if roi < o['piso']:
                        cap += ganancia_usd
                        ultima_moneda = o['s']
                        tiempo_descanso = ahora
                        print(f"\n✅ COBRO: {o['s']} | +${ganancia_usd:.2f} | PISO: {o['piso']}%")
                        ops.remove(o)
                        continue

                # STOP LOSS (Mientras no saltó a 15x)
                if not o['be'] and roi <= -2.5:
                    cap += ganancia_usd
                    ultima_moneda = o['s']
                    tiempo_descanso = ahora
                    print(f"\n⚠️ STOP LOSS: {o['s']} | -${abs(ganancia_usd):.2f}")
                    ops.remove(o)

            # --- 🎯 BUSCADOR (CON DESCANSO 10S Y ROTACIÓN) ---
            if len(ops) < 1 and (ahora - tiempo_descanso) > 10:
                for m in ['SOLUSDT', 'XRPUSDT', 'BNBUSDT']:
                    if m == ultima_moneda: continue 
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], float(k[-2][1])

                    if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                        tipo = 'LONG' if v > o_v else 'SHORT'
                        ops.append({'s':m,'l':tipo,'p':cl[-1],'x':5,'be':False, 'piso': -2.5})
                        print(f"\n🎯 ENTRADA: {m} ({tipo})")
                        break
            elif len(ops) < 1 and (ahora - tiempo_descanso) <= 10:
                print(f"⏳ Pausa 10s... {int(10-(ahora-tiempo_descanso))}s", end='\r')

            # MONITOR
            if len(ops) > 0:
                print(f"💰 Cap: ${cap:.2f} | {ops[0]['s']}: {roi:.2f}% (Piso: {ops[0]['piso']}%)", end='\r')
            
        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
