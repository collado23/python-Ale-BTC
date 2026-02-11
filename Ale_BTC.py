import os, time
from datetime import datetime
from binance.client import Client

# CONEXIÓN DIRECTA
def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
# MONEDAS SELECCIONADAS: SOL, ETH, BNB
ms = ['SOLUSDT', 'ETHUSDT', 'BNBUSDT']
st = {m: {'n': 0.0, 'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False} for m in ms}

def ni(k1, k2):
    o, h, l, c_ = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cp = abs(c_ - o) if abs(c_ - o) > 0 else 0.001
    mi, ms_ = min(o, c_) - l, h - max(o, c_)
    op_p, cl_p = float(k2[1]), float(k2[4])
    cp_p = abs(cl_p - op_p)
    # PATRONES NISON 2.5x (Agresivos)
    if mi > (cp * 2.5) and ms_ < (cp * 0.7): return "🔨" # Martillo
    if ms_ > (cp * 2.5) and mi < (cp * 0.7): return "☄️" # Estrella
    if c_ > o and cl_p < op_p and cp > (cp_p * 1.1): return "V" # Env. Verde
    if c_ < o and cl_p > op_p and cp > (cp_p * 1.1): return "R" # Env. Roja
    return "."

print("🚀 AMETRALLADORA UNIFICADA: SOL | ETH | BNB")

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            k = cl.get_klines(symbol=m, interval='1m', limit=3)
            p = ni(k[-1], k[-2])
            cr = float(k[-1][4])

            if not s['e']:
                print(f"{m[:2]}:{p}", end=' ')
                # Gatillos rápidos
                if (("🔨" in p or "V" in p) and px > cr) or (("☄️" in p or "R" in p) and px < cr):
                    s['t'] = "LONG" if "V" in p or "🔨" in p else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🔥 ENTRADA {m}: {s['t']} a {px}")
            else:
                # Cálculo de ROI con apalancamiento x10
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22
                if roi > s['m']: s['m'] = roi
                if roi >= 0.18: s['b'] = True # Escudo Break Even
                
                # Lógica de Cierre
                if (s['b'] and roi <= 0.01) or (s['m'] >= 0.40 and roi <= (s['m'] - 0.12)) or roi <= -0.55:
                    res = (30.76 * (roi / 100))
                    s['n'] += res
                    s['o'] += 1
                    s['e'] = False
                    print(f"\n✅ CIERRE {m}: {roi:.2f}% | NETO: ${s['n']:.4f}")
                    
                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*30}╗\n║ 📊 REPORTE 5 OPS {m[:3]} ║\n║ NETO ACUM: ${s['n']:.4f} ║\n╚{'═'*30}╝")

        time.sleep(15) # Sincronización cada 15 seg
    except Exception:
        time.sleep(10)
        cl = c()
