import os, time, redis, threading
from binance.client import Client

# --- 🗝️ CONFIGURACIÓN DE ENTORNO ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None

def g_m(leer=False, d=None):
    c_i = 15.77  # Saldo inicial si no hay Redis
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_real_v143")
            return float(h) if h else c_i
        else: r.set("cap_real_v143", str(d))
    except: return c_i

# --- 🚀 MOTOR DEL BOT ---
def bot_real():
    c = Client(API_KEY, API_SECRET)
    cap = g_m(leer=True)
    ops = []
    monedas = ['SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    idx = 0
    
    print(f"💰 BOT ESCALADOR ACTIVADO | SALDO: ${cap:.2f}")

    while True:
        try:
            m = monedas[idx]
            p_act = float(c.get_symbol_ticker(symbol=m)['price'])
            
            # --- 📈 GESTIÓN DE POSICIÓN ABIERTA ---
            for o in ops[:]:
                diff = (p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']
                roi_n = (diff * 100 * o['x']) - 0.9 # ROI Neto con comisión
                
                # 1. SALTO A 15X (Se activa al 2% neto)
                if roi_n >= 2.0 and o['x'] == 5: 
                    o['x'] = 15
                    o['be'] = 0.5  # Primer piso de protección
                    print(f"\n🔥 SALTO A 15X EN {o['s']} | PISO INICIAL: 0.5%")

                # 2. EL ESCALADOR (Trailing manual por niveles)
                if o['x'] == 15:
                    # Nivel 2: Si llega a 3%, sube piso a 1.5%
                    if roi_n >= 3.0 and o['be'] < 1.5:
                        o['be'] = 1.5
                        print(f"\n🔼 ESCALÓN 2: ROI {roi_n:.1f}% | PISO: 1.5%")
                    
                    # Nivel 3: Si llega a 4%, sube piso a 2.5%
                    if roi_n >= 4.0 and o['be'] < 2.5:
                        o['be'] = 2.5
                        print(f"\n🔼 ESCALÓN 3: ROI {roi_n:.1f}% | PISO: 2.5%")
                    
                    # Nivel 4: Si llega a 5%, sube piso a 3.5%
                    if roi_n >= 5.0 and o['be'] < 3.5:
                        o['be'] = 3.5
                        print(f"\n🔼 ESCALÓN 4: ROI {roi_n:.1f}% | PISO: 3.5%")

                # 3. CONDICIONES DE CIERRE (Piso / Profit 15% / Stop -2.5%)
                if (o['be'] > 0 and roi_n <= o['be']) or roi_n >= 15.0 or roi_n <= -2.5:
                    n_c = cap * (1 + (roi_n/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"\n✅ CIERRE EN {o['s']} | ROI FINAL: {roi_n:.2f}% | SALDO: ${cap:.2f}")
                    idx = (idx + 1) % len(monedas) # Rota a la siguiente moneda

            # --- 🎯 GATILLO DE ENTRADA (La Cruz de Ale) ---
            if len(ops) < 1:
                # Calculamos EMA 32
                k = c.get_klines(symbol=m, interval='1m', limit=33)
                cl = [float(x[4]) for x in k]
                e32 = sum(cl[-32:])/32
                
                # DISPARO AL TOQUE DE LÍNEA
                if p_act >= e32: 
                    ops.append({'s': m, 'l': 'LONG', 'p': p_act, 'x': 5, 'be': 0})
                    print(f"\n❌ COMPRA REAL LONG: {m} tocando línea {e32:.2f}")
                elif p_act <= e32:
                    ops.append({'s': m, 'l': 'SHORT', 'p': p_act, 'x': 5, 'be': 0})
                    print(f"\n❌ VENTA REAL SHORT: {m} tocando línea {e32:.2f}")

            # Estado en consola
            status = f"ROI: {roi_n:.2f}% (Piso: {o['be']}%)" if len(ops) > 0 else f"Acechando {m}..."
            print(f"💰 ${cap:.2f} | {status} | {time.strftime('%H:%M:%S')}   ", end='\r')
            
            time.sleep(2) # Seguro Anti-Ban

        except Exception as e:
            if "429" in str(e): time.sleep(30)
            else: time.sleep(5)

if __name__ == "__main__": bot_real()
