import os, time
from binance.client import Client

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
# MONEDAS NUEVAS
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
# CAPITAL INICIAL CON INTERÉS COMPUESTO
cap_actual = 30.76 

st = {m: {'n': 0.0, 'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False} for m in ms}

def ni(k1, k2):
    o, h, l, c_ = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cp = abs(c_ - o) if abs(c_ - o) > 0 else 0.001
    mi, ms_ = min(o, c_) - l, h - max(o, c_)
    cl_p, op_p = float(k2[4]), float(k2[1])
    cp_p = abs(cl_p - op_p)
    
    # GATILLO 2.5x (Agresividad equilibrada)
    if mi > (cp * 2.5) and ms_ < (cp * 0.8): return "🔨"
    if c_ > o and cl_p < op_p and cp > (cp_p * 1.1): return "V"
    
    if ms_ > (cp * 2.5) and mi < (cp * 0.8): return "☄️"
    if c_ < o and cl_p > op_p and cp > (cp_p * 1.1): return "R"
    return "."

print(f"🔱 AMETRALLADORA 15s | CAP: ${cap_actual:.2f} | LI-AD-XR")

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            k = cl.get_klines(symbol=m, interval='1m', limit=3)
            ptr = ni(k[-1], k[-2])
            cr = float(k[-1][4])

            if not s['e']:
                print(f"{m[:2]}:{ptr}", end=' ')
                if (("🔨" in ptr or "V" in ptr) and px > cr) or (("☄️" in ptr or "R" in ptr) and px < cr):
                    s['t'] = "LONG" if "V" in ptr or "🔨" in ptr else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🔥 ENTRADA {m} - Capital: ${cap_actual:.2f}")
            else:
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                if roi >= 0.12: s['b'] = True 
                
                # CIERRE CON ESCUDO AL 0% (Blindaje Nison)
                if (s['b'] and roi <= 0.0) or (s['m'] >= 0.35 and roi <= (s['m'] - 0.10)) or roi <= -0.50:
                    ganancia_op = (cap_actual * (roi / 100))
                    cap_actual += ganancia_op # Interés Compuesto aplicado
                    s['n'] += ganancia_op; s['o'] += 1; s['e'] = False
                    print(f"\n✅ CIERRE {m} {roi:.2f}% | NUEVO CAP: ${cap_actual:.2f}")

        # REGLA DE ORO: 15 SEGUNDOS
        time.sleep(15) 
        
    except Exception as e:
        time.sleep(10)
        cl = c()
