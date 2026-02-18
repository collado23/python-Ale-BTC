import os, time, threading
from binance.client import Client

# --- 🌐 1. MOTOR V146 FULL - ALE (SIMULACIÓN Y REAL) ---
def bot():
    # Para real usar: c = Client(api_key, api_secret)
    c = Client() 
    cap = 10.0  # Tu capital de prueba
    ops = []
    ultima_moneda = ""
    tiempo_descanso = 0

    print(f"🐊 MOTOR V146 FULL | SALTO 15X AL 1.5% | DESCANSO 10S | $10") 

    while True:
        t_l = time.time()
        ahora = time.time()
        
        try:
            for o in ops[:]:
                # --- 📊 1. PRECIO DE ENTRADA Y ACTUAL ---
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                # Cálculo de diferencia según sea LONG o SHORT
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                # --- 💰 2. CÁLCULO DE GANANCIAS (ROI NETO -0.90%) ---
                roi = (diff * 100 * o['x']) - 0.90
                ganancia_usd = cap * (roi / 100)
                
                # --- 🚀 3. EL SALTO AL 1.5% (A 15X) ---
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15
                    o['be'] = True 
                    o['piso'] = 1.0  # Protección inicial al 1%
                    print(f"\n🔥 SALTO A 15X: {o['s']} | Precio Entr: {o['p']} | ROI: {roi:.2f}%")

                # --- 🛡️ 4. ESCALADOR DINÁMICO ---
                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0: n_p = 24.5
                    elif roi >= 10.0: n_p = 9.5
                    elif roi >= 5.0:  n_p = 4.5
                    elif roi >= 2.0:  n_p = 1.5
                    
                    if n_p > o['piso']:
                        o['piso'] = n_p
                        print(f"🛡️ ESCALADOR: {o['s']} subió piso a {o['piso']}%")

                    # CIERRE POR PISO (COBRO)
                    if roi < o['piso']:
                        cap += ganancia_usd
                        ultima_moneda = o['s']
                        tiempo_descanso = ahora
                        print(f"\n✅ COBRO: {o['s']} | Ganancia: +${ganancia_usd:.2f} | Final: ${cap:.2f}")
                        ops.remove(o)
                        continue

                # --- ⚠️ 5. STOP LOSS ---
                if not o['be'] and roi <= -2.5:
                    cap += ganancia_usd
                    ultima_moneda = o['s']
                    tiempo_descanso = ahora
                    print(f"\n⚠️ STOP LOSS: {o['s']} | Perdida: -${abs(ganancia_usd):.2f}")
                    ops.remove(o)

            # --- 🎯 6. BUSCADOR (CON ROTACIÓN Y DESCANSO) ---
            if len(ops) < 1 and (ahora - tiempo_descanso) > 10:
                monedas = ['SOLUSDT', 'XRPUSDT', 'BNBUSDT']
                for m in monedas:
                    if m == ultima_moneda: continue # No repite la misma
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], float(k[-2][1])

                    # Estrategia EMAs
                    if (v > o_v and v > e9 and e9 > e27) or (v < o_v and v < e9 and e9 < e27):
                        tipo = 'LONG' if v > o_v else 'SHORT'
                        # Guardamos precio de entrada (cl[-1])
                        ops.append({'s':m,'l':tipo,'p':cl[-1],'x':5,'be':False, 'piso': -2.5})
                        print(f"\n🎯 ENTRADA NUEVA: {m} | Precio: {cl[-1]} | Tipo: {tipo}")
                        break
            
            # --- 🕒 7. MONITOR DE CONSOLA ---
            if len(ops) > 0:
                txt = f" | {ops[0]['s']}: {roi:.2f}% (Piso: {ops[0]['piso']}%)"
            elif (ahora - tiempo_descanso) <= 10:
                txt = f" | ⏳ Descanso: {int(10-(ahora-tiempo_descanso))}s"
            else:
                txt = " | 🔎 Buscando oportunidad..."
            
            print(f"💰 Capital: ${cap:.2f}{txt} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except Exception as e: 
            print(f"\n❌ Error: {e}")
            time.sleep(5)
            
        time.sleep(1)

if __name__ == "__main__": bot()
