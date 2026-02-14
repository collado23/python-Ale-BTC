import os, time, redis, json 
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA DE CAPITAL ---
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
        return cap_act, racha
    else:
        r.lpush("historial_bot", json.dumps(datos))

# --- 📊 2. CEREBRO ANALISTA DE OPORTUNIDAD ---
def cerebro_analista(simbolo, cliente, racha):
    try:
        # Volvemos a get_klines (la función oficial que no da error)
        klines = cliente.get_klines(symbol=simbolo, interval='5m', limit=50)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
        
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])

        # Indicadores para el análisis
        ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        pre_act = df['close'].iloc[-1]

        # 🧠 EL ANÁLISIS DE LAS "X":
        if rsi < 36:
            # Cuanto más bajo el RSI, más X le damos (Máximo 15x)
            x_base = 5
            bono_fuerza = (36 - rsi) * 1.2
            x_calculadas = int(min(15, x_base + bono_fuerza))
            
            # Si hay racha negativa, el analista baja el riesgo drásticamente
            if racha > 0: x_calculadas = max(1, x_calculadas - (racha * 3))

            # Proyectamos el ROI: Si no es mayor a 1.2% neto, no entramos
            distancia_media = ((ema21 - pre_act) / pre_act) * 100
            roi_proyectado = distancia_media * x_calculadas

            if roi_proyectado > 1.2:
                return True, pre_act, x_calculadas, f"🐊 ANALIZADO: Morder con {x_calculadas}x | ROI: {roi_proyectado:.1f}%"
            else:
                return False, pre_act, 0, f"⏳ ROI {roi_proyectado:.1f}% insuficiente"

        return False, pre_act, 0, f"Analizando... RSI: {rsi:.1f}"

    except Exception as e:
        # Si hay error, lo mostramos pero no frenamos el bot
        return False, 0, 0, f"Buscando señal..."

# --- 🚀 3. BUCLE DE OPERACIÓN (15 Segundos de Seguridad) ---
cap_real, racha_act = gestionar_memoria(leer=True)
print(f"🦁 BOT V100 | ANALISTA SEGURO (15s) | Cap: ${cap_real:.2f}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    for p in presas:
        puedo, precio, x_final, razon = cerebro_analista(p, Client(), racha_act)
        print(f"🧐 {p}: {razon} | Cap: ${cap_real:.2f} | X Sugerida: {x_final}   ", end='\r')
        
        if puedo:
            print(f"\n🎯 [OPORTUNIDAD CONFIRMADA EN {p}]")
            print(f"💰 Acción: Comprar a {precio} con {x_final}x")
            # El bot aquí lanzaría la orden...
            
    time.sleep(15) # ⏱️ TIEMPO DE SEGURIDAD PARA BINANCE
