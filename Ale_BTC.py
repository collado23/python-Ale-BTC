import os, time, threading
from binance.client import Client 

# --- 🌐 MOTOR V146 FULL CORREGIDO ---
def bot():
    c = Client() 
    cap = 10.0  
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0

    print(f"🐊 MOTOR V146 FULL | SALTO 15X AL 1.5% | DESCANSO 10S | $10")

    while True:
        t_l = time.time()
        ahora = time.time()
        roi_display = 0.0 # <--- Variable fija para evitar el error del log
        piso_display = -2.5

        try:
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                roi = (diff * 100 * o['x']) - 0.90
                roi_display = roi # Actualizamos para el monitor
                piso_display = o['piso']
                ganancia_usd = cap * (roi / 100)
                
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.0  
                    print(f"\n🔥 SALTO A 15X: {o['s']} | ROI: {roi:.2f}%")

                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0: n_p = 24.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 5.0:  n_p = 4.5
                    elif roi >= 2.0:  n_p = 1.5
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ ESCALADOR: {o['s']} subió piso a {o['piso']}%")

                    if roi < o['piso']:
                        cap += ganancia_usd
                        ultima_moneda = o['s']
                        tiempo_descanso = ahora
                        print(f"\n✅ COBRO: {o['s']} | Ganancia: +${ganancia_usd:.2f}")
                        ops.remove(o)
                        continue

                if not o['be'] and roi <= -2.5:
                    cap += ganancia_usd
                    ultima_moneda = o['s']
                    tiempo_descanso = ahora
                    print(f"\n⚠️ STOP LOSS: {o['s']} | Perdida: -${abs(ganancia_usd):.2f}")
                    ops.remove(o)

            # --- 🎯 BUSCADOR ---
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
                        print(f"\n🎯 ENTRADA NUEVA: {m} | Precio: {cl[-1]}")
                        break
            
            # --- 🕒 MONITOR (CORREGIDO PARA RAILWAY) ---
            if len(ops) > 0:
                txt = f" | {ops[0]['s']}: {roi_display:.2f}% (Piso: {piso_display}%)"
            elif (ahora - tiempo_descanso) <= 10:
                txt = f" | ⏳ Descanso: {int(10-(ahora-tiempo_descanso))}s"
            else:
                txt = " | 🔎 Buscando..."
            
            print(f"💰 Capital: ${cap:.2f}{txt} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except Exception as e: 
            # Si hay error, lo muestra pero no se detiene
            time.sleep(5)
            
        time.sleep(1)

if __name__ == "__main__": bot()
