import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA Y CAPITAL ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini, 0
    hist = r.lrange("historial_bot", 0, -1)
    if leer:
        if not hist: return cap_ini, 0
        cap_act = cap_ini
        racha = 0
        for t in reversed(hist):
            tr = json.loads(t)
            cap_act *= (1 + (tr.get('roi', 0) / 100))
            racha = racha + 1 if tr.get('res') == "LOSS" else 0
        return float(cap_act), int(racha)
    else: r.lpush("historial_bot", json.dumps(datos))

# --- 📊 2. CEREBRO DE X DINÁMICAS ---
def obtener_rsi_rapido(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=14)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
        c = pd.to_numeric(df['c'])
        delta = c.diff()
        g = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        p = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        return 100 - (100 / (1 + (g / p))).iloc[-1]
    except: return 50

# --- 🚀 3. BUCLE MAESTRO ---
cap_total, racha_act = gestionar_memoria(leer=True)
operaciones = [] 

print(f"🦁 BOT V112 | DETALLE DE CIERRE ACTIVO | Cap: ${cap_total:.2f}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    try:
        client = Client()
        ganancia_flotante = 0

        for op in operaciones[:]:
            rsi_v = obtener_rsi_rapido(op['s'], client)
            
            # 🔥 AJUSTE DE X EN VIVO
            fuerza = (rsi_v - 50) if op['l'] == "LONG" else (50 - rsi_v)
            op['x'] = max(2, min(15, int(5 + (fuerza * 0.4))))

            t = client.get_symbol_ticker(symbol=op['s'])
            p_act = float(t['price'])
            roi = ((p_act - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - p_act)/op['p'])*100*op['x']
            pnl = op['c'] * (roi / 100)
            ganancia_flotante += pnl
            
            status_v = "🟢 G" if roi >= 0 else "🔴 P"
            print(f"📊 {op['s']} {op['l']} ({op['x']}x) | {status_v}: ${abs(pnl):.2f} ({roi:.2f}%)      ", end='\r')

            # --- 🎯 CIERRE CON DETALLE AMPLIADO ---
            if roi >= 1.6 or roi <= -1.3:
                tipo_c = "✅ CIERRE G" if roi > 0 else "❌ CIERRE P"
                # Mensaje detallado como pediste
                print(f"\n{tipo_c} {op['s']} | Final: ${abs(pnl):.2f} | ROI: {roi:.2f}% | X Final: {op['x']}x")
                
                gestionar_memoria(False, {'m': op['s'], 'roi': roi, 'res': 'WIN' if roi > 0 else 'LOSS'})
                operaciones.remove(op)
                cap_total, racha_act = gestionar_memoria(leer=True)

        print(f"💰 BILLETERA: ${cap_total + ganancia_flotante:.2f} | Base: ${cap_total:.2f}          ")

        # C. BUSCAR NUEVAS (Si hay espacio)
        if len(operaciones) < 2:
            for p in presas:
                if any(o['s'] == p for o in operaciones): continue
                rsi_e = obtener_rsi_rapido(p, client)
                if rsi_e < 32 or rsi_e > 68:
                    lado = "LONG" if rsi_e < 32 else "SHORT"
                    t = client.get_symbol_ticker(symbol=p)
                    print(f"\n🎯 [ENTRADA]: {p} {lado} (Buscando G)")
                    operaciones.append({'s': p, 'l': lado, 'p': float(t['price']), 'x': 5, 'c': cap_total * 0.4})
                    if len(operaciones) >= 2: break

        time.sleep(10)
        
    except Exception as e:
        time.sleep(5)
