import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA Y GESTIÓN DE CAPITAL ---
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

# --- 📊 2. CEREBRO ANALISTA (X Dinámicas + Análisis de ROI) ---
def cerebro_analista(simbolo, cliente, racha):
    try:
        # Traemos más datos para asegurar que el RSI y EMAs sean precisos
        klines = cliente.get_candles(symbol=simbolo, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
        
        # Corrección técnica para evitar el error 'close'
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])

        # Indicadores
        ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        pre_act = df['close'].iloc[-1]

        # 🧠 EL ANÁLISIS DE LAS "X":
        # Cuanto más bajo el RSI, más confianza tiene el bot para usar más X.
        if rsi < 35:
            fuerza = (35 - rsi) * 1.5
            x_calculadas = int(min(15, 5 + fuerza)) # Base 5x, sube según la oportunidad
            
            # Si hay racha negativa, el analista es prudente y baja las X
            if racha > 0: x_calculadas = max(1, x_calculadas - (racha * 2))

            # Cálculo de ROI proyectado para ver si vale la pena
            distancia_media = ((ema21 - pre_act) / pre_act) * 100
            roi_proyectado = distancia_media * x_calculadas

            if roi_proyectado > 1.2: # Solo entra si el análisis da un ROI decente
                return True, pre_act, x_calculadas, f"🐊 ANALIZADO: Rebote RSI {rsi:.1f} | ROI Est: {roi_proyectado:.1f}%"
            else:
                return False, pre_act, 0, f"⏳ ROI {roi_proyectado:.1f}% muy bajo. No entro."

        return False, pre_act, 0, f"Analizando... RSI: {rsi:.1f}"

    except Exception as e:
        return False, 0, 0, f"Error en análisis: {str(e)}"

# --- 🚀 3. EJECUCIÓN ---
cap_real, racha_act = gestionar_memoria(leer=True)
print(f"🦁 BOT V98: ANALISTA SIN ERRORES | Cap: ${cap_real:.2f}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    for p in presas:
        puedo, precio, x_final, razon = cerebro_analista(p, Client(), racha_act)
        print(f"🧐 {p}: {razon} | Cap: ${cap_real:.2f} | X Sugerida: {x_final}", end='\r')
        
        if puedo:
            print(f"\n🎯 [OPORTUNIDAD CONFIRMADA] {p} a {precio}")
            print(f"💰 El analista decidió entrar con {x_final}x | {razon}")
            # Aquí iría la orden real...
            
    time.sleep(15)
