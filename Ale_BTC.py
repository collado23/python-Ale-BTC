import os, time, redis, threading
from binance.client import Client

# --- 🗝️ CONFIGURACIÓN ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None

def g_m(leer=False, d=None):
    c_i = 15.77 
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_real_v143")
            # PARCHE: Si lo que lee es 'inf' o '-inf', resetea a 15.77
            if h in [None, 'inf', '-inf', 'nan']: return c_i
            return float(h)
        else: 
            # PARCHE: No guardar si es infinito
            if str(d) in ['inf', '-inf', 'nan']: d = 15.77
            r.set("cap_real_v143", str(d))
    except: return c_i

def bot_real():
    c = Client(API_KEY, API_SECRET)
    cap = g_m(leer=True)
    ops = []
    monedas = ['SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    idx = 0
    
    print(f"💰 BOT FRANCOTIRADOR V144 | SALDO: ${cap:.2f}")

    while True:
        try:
            m = monedas[idx]
            p_act = float(c.get_symbol_ticker(symbol=m)['price'])
            
            # --- 📈 GESTIÓN DE POSICIÓN ---
            for o in ops[:]:
                diff = (p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']
                roi_n = (diff * 100 * o['x']) - 0.9 
                
                # 1. SALTO A 15X
                if roi_n >= 2.0 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = 0.5
                    print(f"\n🔥 SALTO A 15X | PISO: 0.5%")

                # 2. ESCALADOR (Trailing)
                if o['x'] == 15:
                    if roi_n >= 3.0 and o['be'] < 1.5: o['be'] = 1.5
                    if roi_n >= 4.0 and o['be'] < 2.5: o['be'] = 2.5
                    if roi_n >= 5.0 and o['be'] < 3.5: o['be'] = 3.5

                # 3. CIERRE CON ESCUDO ANTI-INFINITO
                if (o['be'] > 0 and roi_n <= o['be']) or roi_n >= 15.0 or roi_n <= -2.5:
                    n_c = cap * (1 + (roi_n/100))
                    
                    # 🛡️ PROTECCIÓN CRÍTICA
                    if n_c <= 0 or n_c > 1000000 or str(n_c) == 'inf': 
                        n_c = 15.77
                        print("\n⚠️ SALDO CORRUPTO DETECTADO: Reseteando a $15.77")

                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"\n✅ CIERRE EN {o['s']} | ROI: {roi_n:.2f}% | SALDO: ${cap:.2f}")
                    idx = (idx + 1) % len(monedas)

            # --- 🎯 GATILLO (La Cruz de Ale) ---
            if len(ops) < 1:
                k = c.get_klines(symbol=m, interval='1m', limit=33)
                cl = [float(x[4]) for x in k]
                e32 = sum(cl[-32:])/32
                
                # Tolerancia mínima para entrar JUSTO en la línea (0.05%)
                if p_act >= e32 and p_act <= (e32 * 1.0005): 
                    ops.append({'s': m, 'l': 'LONG', 'p': p_act, 'x': 5, 'be': 0})
                    print(f"\n❌ COMPRA LONG: {m} tocando línea")
                elif p_act <= e32 and p_act >= (e32 * 0.9995):
                    ops.append({'s': m, 'l': 'SHORT', 'p': p_act, 'x': 5, 'be': 0})
                    print(f"\n❌ VENTA SHORT: {m} tocando línea")

            status = f"ROI: {roi_n:.2f}%" if len(ops) > 0 else f"Acechando {m}..."
            print(f"💵 ${cap:.2f} | {status} | {time.strftime('%H:%M:%S')}   ", end='\r')
            time.sleep(2) 

        except Exception as e:
            if "429" in str(e): time.sleep(30)
            else: time.sleep(5)

if __name__ == "__main__": bot_real()
