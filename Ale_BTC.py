import os, time
from binance.client import Client

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['SOLUSDT', 'ETHUSDT', 'BNBUSDT']
st = {m: {'n': 0.0, 'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False} for m in ms}

def ni(k1, k2):
    o, h, l, c_ = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cp = abs(c_ - o) if abs(c_ - o) > 0 else 0.001
    mi, ms_ = min(o, c_) - l, h - max(o, c_)
    op_p, cl_p = float(k2[1]), float(k2[4])
    cp_p = abs(cl_p - op_p)
    
    # LONG: Más exigente (3.0x) para evitar falsos rebotes
    if mi > (cp * 3.0) and ms_ < (cp * 0.5): return "🔨"
    if c_ > o and cl_p < op_p and cp > (cp_p * 1.3): return "V"
    
    # SHORT: Mantenemos agresivo (2.5x) que está rindiendo
    if ms_ > (cp * 2.5) and mi < (cp * 0.7): return "☄️"
    if c_ < o and cl_p > op_p and cp > (cp_p * 1.2): return "R"
    return "."

print("📡 MODO FRANCOTIRADOR: SOL | ETH | BNB")

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            k = cl.get_klines(symbol=m, interval='1m', limit=3)
            p = ni(k[-1], k[-2])
            cr = float(k[-1][4])

            if not s['e']:
                if (("🔨" in p or "V" in p) and px > cr) or (("☄️" in p or "R" in p) and px < cr):
                    s['t'] = "LONG" if "V" in p or "🔨" in p else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 ENTRADA {m}: {s['t']}")
            else:
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22
                if roi > s['m']: s['m'] = roi
                if roi >= 0.15: s['b'] = True # Blindaje aún más rápido
                
                if (s['b'] and roi <= 0.0) or (s['m'] >= 0.35 and roi <= (s['m'] - 0.10)) or roi <= -0.50:
                    res = (30.76 * (roi / 100))
                    s['n'] += res; s['o'] += 1; s['e'] = False
                    print(f"✅ {m} {roi:.2f}% | NETO: ${s['n']:.4f}")
                    if s['o'] % 5 == 0:
                        print(f"\n📊 BLOQUE 5 {m} FINALIZADO - NETO: ${s['n']:.2f}")

        time.sleep(15)
    except Exception:
        time.sleep(10); cl = c()
