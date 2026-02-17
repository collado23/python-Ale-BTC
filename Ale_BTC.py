import os, time
from binance.client import Client

def bot_simulacion():
    c = Client() 
    cap = 15.77  
    ops = []
    monedas = ['SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    idx = 0
    
    print(f"🧪 SIMULACIÓN CON SALTO 15X | SALDO: ${cap:.2f}")

    while True:
        try:
            m = monedas[idx]
            p_act = float(c.get_symbol_ticker(symbol=m)['price'])
            
            for o in ops[:]:
                # Cálculo de ROI dinámico según el apalancamiento actual (o['x'])
                diff = (p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']
                roi_n = (diff * 100 * o['x']) - 0.9
                
                # EL SALTO: Si llega a 2%, sube a 15x y activa BE
                if roi_n >= 2.0 and o['x'] == 5: 
                    o['x'] = 15
                    o['be'] = True
                    print(f"\n🔥 [SIM] SALTO A 15X EN {o['s']} | PROTECCIÓN 0.5% ON")
                
                # CIERRES
                if (o['be'] and roi_n <= 0.5) or roi_n >= 3.5 or roi_n <= -2.5:
                    cap *= (1 + (roi_n/100))
                    ops.remove(o)
                    print(f"\n✅ [SIM] CIERRE {m} | ROI FINAL: {roi_n:.2f}% | SALDO: ${cap:.2f}")
                    idx = (idx + 1) % len(monedas)

            if len(ops) < 1:
                k = c.get_klines(symbol=m, interval='1m', limit=33)
                cl = [float(x[4]) for x in k]
                e32 = sum(cl[-32:])/32
                
                # Entrada al toque de la línea
                if p_act >= e32:
                    ops.append({'s': m, 'l': 'LONG', 'p': p_act, 'x': 5, 'be': False})
                    print(f"\n🚀 [SIM] ENTRADA LONG: {m} | Precio: {p_act}")
                elif p_act <= e32:
                    ops.append({'s': m, 'l': 'SHORT', 'p': p_act, 'x': 5, 'be': False})
                    print(f"\n🚀 [SIM] ENTRADA SHORT: {m} | Precio: {p_act}")

            print(f"⏳ {m} a ${p_act} | ROI: {roi_n if ops else 0:.2f}% | X: {ops[0]['x'] if ops else 5}   ", end='\r')
            time.sleep(2)
        except: time.sleep(5)

if __name__ == "__main__": bot_simulacion()
