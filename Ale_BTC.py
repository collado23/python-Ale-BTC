import os, time
from binance.client import Client

# CONEXIÓN NÚCLEO
def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 30.80 # Capital actualizado según tu último log

# Estructura para guardar historial 'h' de 5 operaciones
st = {m: {'n': 0.0, 'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def ni(k1, k2):
    o, h, l, c_ = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cp = abs(c_ - o) if abs(c_ - o) > 0 else 0.001
    mi, ms_ = min(o, c_) - l, h - max(o, c_)
    cl_p, op_p = float(k2[4]), float(k2[1])
    cp_p = abs(cl_p - op_p)
    # GATILLO 2.5x (Tu configuración ganadora)
    if mi > (cp * 2.5) and ms_ < (cp * 0.8): return "🔨"
    if c_ > o and cl_p < op_p and cp > (cp_p * 1.1): return "V"
    if ms_ > (cp * 2.5) and mi < (cp * 0.8): return "☄️"
    if c_ < o and cl_p > op_p and cp > (cp_p * 1.1): return "R"
    return "."

print(f"🔱 AMETRALLADORA 5-OPS | CAP: ${cap_actual:.2f} | 15s")

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
                    print(f"\n🎯 ENTRADA {m} (${cap_actual:.2f})")
            else:
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                if roi >= 0.12: s['b'] = True 
                
                # CIERRE (Stop Loss ajustado a -0.50% para no quemar el capital)
                if (s['b'] and roi <= 0.0) or (s['m'] >= 0.35 and roi <= (s['m'] - 0.10)) or roi <= -0.50:
                    ganancia_op = (cap_actual * (roi / 100))
                    cap_actual += ganancia_op 
                    s['o'] += 1
                    s['e'] = False
                    
                    # REGISTRO DE GANADAS Y PERDIDAS
                    estado = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{estado} {s['t']} {roi:.2f}%")
                    print(f"\n{estado} CIERRE {m}: {roi:.2f}% | CAP: ${cap_actual:.2f}")
                    
                    # CUADRO DE REPORTE CADA 5
                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*32}╗")
                        print(f"║ 📊 REPORTE {m[:3]} (BLOQUE 5) ║")
                        for op in s['h']:
                            print(f"║ {op.ljust(28)} ║")
                        print(f"╠{'═'*32}╣")
                        print(f"║ CAPITAL TOTAL: ${cap_actual:.2f}   ║")
                        print(f"╚{'═'*32}╝\n")
                        s['h'] = [] # Reinicia el bloque

        time.sleep(15) # Tu regla de oro de 15 segundos
    except:
        time.sleep(10); cl = c()
