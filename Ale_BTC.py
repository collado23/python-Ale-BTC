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
    else: r.lpush("historial_bot", json.dumps(datos))

# --- 📊 2. CEREBRO ANALISTA DOBLE VÍA (LONG & SHORT) ---
def cerebro_analista_completo(simbolo, cliente, racha):
    try:
        klines = cliente.get_klines(symbol=simbolo, interval='5m', limit=50)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
        df['close'] = pd.to_numeric(df['c'])
        
        # Indicadores
        ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        pre_act = df['close'].iloc[-1]

        # 🧠 ANÁLISIS DE LAS "X"
        x_base = 5
        # Si el RSI es extremo (bajo 35 o sobre 65), aumentamos fuerza
        fuerza = abs(50 - rsi) * 0.5
        x_final = int(min(15, x_base + fuerza))
        if racha > 0: x_final = max(1, x_final - (racha * 3))

        # --- 🐊 DECISIÓN DE DIRECCIÓN ---

        # 1. DIRECCIÓN SUBIDA (LONG): RSI bajo o Cruce Alcista
        if rsi < 36 or (ema9 > ema21 and rsi < 60):
            return True, "LONG", pre_act, x_final, f"🚀 LONG: RSI {rsi:.1f} | Objetivo: Subida"

        # 2. DIRECCIÓN BAJADA (SHORT): RSI alto o Cruce Bajista
        # Si el RSI está arriba de 65 y las EMAs se cruzan para abajo, ganamos si CAE.
        if rsi > 64 or (ema9 < ema21 and rsi > 45):
            return True, "SHORT", pre_act, x_final, f"📉 SHORT: RSI {rsi:.1f} | Objetivo: Caída"

        return False, None, pre_act, 0, f"Analizando... RSI: {rsi:.1f}"

    except Exception: return False, None, 0, 0, "Buscando oportunidad..."

# --- 🚀 3. BUCLE DE OPERACIÓN ---
cap_real, racha_act = gestionar_memoria(leer=True)
print(f"🦁 BOT V101 | ANALISTA LONG/SHORT | Cap: ${cap_real:.2f}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    for p in presas:
        puedo, lado, precio, x_fin, razon = cerebro_analista_completo(p, Client(), racha_act)
        print(f"🧐 {p}: {razon} | X: {x_fin}   ", end='\r')
        
        if puedo:
            print(f"\n🎯 [OPORTUNIDAD DETECTADA EN {p}]")
            print(f"💰 DIRECCIÓN: {lado} | Precio: {precio} | Apalancamiento: {x_fin}x")
            # El bot lanza la orden según el lado (LONG o SHORT)
            
    time.sleep(15)
