import time
from binance.client import Client 

def bot_simulacion():
    c = Client() 
    cap = 15.77  
    ops = []
    monedas = ['SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    idx = 0
    
    print(f"🧪 SIMULACIÓN V146 | EMAs 9/27 | DETALLE DE PRECIOS")

    while True:
        try:
            m = monedas[idx]
            p_act = float(c.get_symbol_ticker(symbol=m)['price'])
            
            # --- 📈 GESTIÓN DE POSICIÓN ---
            for o in ops[:]:
                diff = (p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']
                roi_n = (diff * 100 * o['x']) - 0.9 
                
                # Salto a 15x
                if roi_n >= 2.0 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = 0.5 
                    print(f"\n🔥 [SIM] SALTO A 15X EN {o['s']} | PISO: 0.5%")

                # Escalador
                if o['x'] == 15:
                    if roi_n >= 3.0 and o['be'] < 1.5: o['be'] = 1.5
                    if roi_n >= 4.0 and o['be'] < 2.5: o['be'] = 2.5

                # 🏁 CIERRE CON DETALLE DE PRECIO
                if (o['be'] > 0 and roi_n <= o['be']) or roi_n >= 15.0 or roi_n <= -2.5:
                    ganancia_usd = cap * (roi_n/100)
                    cap += ganancia_usd
                    
                    print(f"\n✅ CIERRE EN {o['s']}")
                    print(f"   🔹 Entró a: {o['p']}")
                    print(f"   🔸 Salió a: {p_act}") # <--- PRECIO DE VENTA/CIERRE
                    print(f"   📊 ROI: {roi_n:.2f}% | Ganancia: ${ganancia_usd:.2f}")
                    print(f"   💰 Nuevo Saldo: ${cap:.2f}")
                    
                    ops.remove(o)
                    idx = (idx + 1) % len(monedas)

            # --- 🎯 ENTRADA CON DETALLE DE PRECIO ---
            if len(ops) < 1:
                k = c.get_klines(symbol=m, interval='1m', limit=30)
                cl = [float(x[4]) for x in k]
                ema27_act = sum(cl[-27:])/27
                cierre_ant = cl[-1]
                ema27_ant = sum(cl[-28:-1])/27
                
                # Cruce Long
                if cierre_ant <= ema27_ant and p_act > ema27_act:
                    ops.append({'s': m, 'l': 'LONG', 'p': p_act, 'x': 5, 'be': 0})
                    print(f"\n🚀 ENTRADA LONG EN {m}")
                    print(f"   📍 Precio de Compra: {p_act}") # <--- PRECIO DE COMPRA
                
                # Cruce Short
                elif cierre_ant >= ema27_ant and p_act < ema27_act:
                    ops.append({'s': m, 'l': 'SHORT', 'p': p_act, 'x': 5, 'be': 0})
                    print(f"\n🚀 ENTRADA SHORT EN {m}")
                    print(f"   📍 Precio de Venta (Entrada): {p_act}") # <--- PRECIO DE ENTRADA EN SHORT

            # Status rápido
            msg = f"ROI: {roi_n:.2f}%" if ops else f"Acechando {m}"
            print(f"🧪 ${cap:.2f} | {msg} | {time.strftime('%H:%M:%S')}   ", end='\r')
            
            time.sleep(2) 

        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    bot_simulacion()
