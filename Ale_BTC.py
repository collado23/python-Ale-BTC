import os, time
from binance.client import Client

# CONEXIÓN DIRECTA
def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
# CAMBIO DE MONEDAS: LINK, ADA, XRP
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
st = {m: {'n': 0.0, 'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False} for m in ms}

def ni(k1, k2):
    o, h, l, c_ = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cp = abs(c_ - o) if abs(c_ - o) > 0 else 0.001
    mi, ms_ = min(o, c_) - l, h - max(o, c_)
    op_p, cl_p = float(k2[1]), float(k2[4])
    cp_p = abs(cl_p - op_p)
    
    # LONG: Filtro 3.0x (Solo si la mecha inferior es gigante)
    if mi > (cp * 3.0) and ms_ < (cp * 0.5): return "🔨"
    if c_ > o and cl_p < op_p and cp > (cp_p * 1.5): return "V" # Envolvente más fuerte
    
    # SHORT: Mantenemos 2.5x (Lo que dio el +1.07% en BTC)
    if ms_ > (cp * 2.5) and mi < (cp * 0.7): return "☄️"
    if c_ < o and cl_p > op_p and cp > (cp_p * 1.2): return "R"
    return "."

print("📡 TRIDENTE ON: LI | AD | XR")

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
                    s['t'] = "LONG" if "V" in ptr or "🔨" in p else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 ENTRADA {m}: {s['t']}")
            else:
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                if roi >= 0.12: s['b'] = True # BLINDAJE ULTRA RÁPIDO
                
                # CIERRE: Si toca 0.0% después de estar en verde, sale para proteger capital
                if (s['b'] and roi <= 0.0) or (s['m'] >= 0.35 and roi <= (s['m'] - 0.10)) or roi <= -0.45:
                    res = (30.76 * (roi / 100))
                    s['n'] += res; s['o'] += 1; s['e'] = False
                    print(f"\n✅ {m} {roi:.2f}% | NETO: {s['n']:.2f}")

        time.sleep(15)
    except Exception:
        time.sleep(10); cl = c()
