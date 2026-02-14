import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA DE CAPITAL Y RACHA ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini, 0 # Retornamos racha 0 si no hay redis
    hist = r.lrange("historial_bot", 0, -1)
    if leer:
        if not hist: return cap_ini, 0
        cap_act = cap_ini
        racha_perdedora = 0
        for t in reversed(hist):
            tr = json.loads(t)
            cap_act *= (1 + (tr.get('roi', 0) / 100))
            racha_perdedora = racha_perdedora + 1 if tr.get('res') == "LOSS" else 0
        return cap_act, racha_perdedora
    else:
        r.lpush("historial_bot", json.dumps(datos))

# --- 📊 2. EL CEREBRO: ANALIZA OPORTUNIDAD + X ÓPTIMAS ---
def cerebro_analista(simbolo, cliente, racha):
    try:
        klines = cliente.get_klines(symbol=simbolo, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','t1','t2','t3','t4','t5','t6'])
        df['close'] = df['close'].astype(float)

        # Indicadores
        ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        pre_act = df['close'].iloc[-1]

        # 🧠 EL BOT ANALIZA LAS "X" IDEALES:
        # Empezamos con un cálculo basado en qué tan lejos estamos del RSI extremo
        # Si RSI es 20, la fuerza es mucha. Si RSI es 34, la fuerza es poca.
        fuerza_oportunidad = max(0, (35 - rsi) * 2) # A menor RSI, más fuerza
        
        # Ajustamos las X según la racha y la fuerza (Mínimo 1x, Máximo 15x)
        x_recomendadas = int(min(15, fuerza_oportunidad + 5))
        
        # Si venimos de perder, el cerebro aplica un "castigo" de seguridad
        if racha > 0:
            x_recomendadas = max(1, x_recomendadas - (racha * 3))

        # 🧠 DECISIÓN ANALÍTICA
        roi_est = ((ema21 - pre_act) / pre_act) * 100 * x_recomendadas

        # CASO 1: Rebote por Pánico
        if rsi < 34:
            if roi_est > 1.5:
                return True, pre_act, x_recomendadas, f"🐊 ANALIZADO: Morder con {x_recomendadas}x (ROI Est: {roi_est:.1f}%)"
            else:
                return False, pre_act, 0, f"⏳ RSI bajo ({rsi:.1f}) pero ROI insuficiente con {x_recomendadas}x"

        # CASO 2: Tendencia (Solo si hay fuerza clara)
        if pre_act > ema9 and ema9 > ema21 and rsi < 60:
            x_tendencia = min(8, x_recomendadas) # En tendencia somos más conservadores que en rebotes
            return True, pre_act, x_tendencia, f"🚀 ANALIZADO: Seguir tendencia con {x_tendencia}x"

        return False, pre_act, 0, f"Analizando... RSI: {rsi:.1f} | X Sugeridas: {x_recomendadas}"

    except Exception as e:
        return False, 0, 0, f"Error: {e}"

# --- 🚀 3. BUCLE DE EJECUCIÓN ---
cap_real, racha_actual = gestionar_memoria(leer=True)
print(f"🦁 BOT V97 | ANALISTA DE RIESGO DINÁMICO")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    for p in presas:
        puedo, precio, x_final, razon = cerebro_analista(p, Client(), racha_actual)
        print(f"🧐 {p}: {razon} | Cap: ${cap_real:.2f}", end='\r')
        
        if puedo:
            print(f"\n🎯 [ESTRATEGIA CALCULADA]")
            print(f"💰 Operando {p} a {precio} usando {x_final}x")
            print(f"📝 Razón: {razon}")
            # Ejecutar con x_final...
            
    time.sleep(10)
