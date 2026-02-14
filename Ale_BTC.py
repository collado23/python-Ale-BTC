import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA CON APALANCAMIENTO DINÁMICO ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    capital_inicial = 15.77
    x_min = 1      # Si perdemos mucho, bajamos a 1x (sin riesgo)
    x_max = 15     # El techo que me pediste
    
    if not r: return capital_inicial, x_min, []
    
    historial = r.lrange("historial_bot", 0, -1)
    
    if leer:
        if not historial: return capital_inicial, 5, [] # Empezamos tranqui en 5x
        
        cap_acumulado = capital_inicial
        racha_perdedora = 0
        horas_malas = []
        
        # Leemos el historial para ajustar las X y el Capital
        for t in reversed(historial):
            trade = json.loads(t)
            cap_acumulado *= (1 + (trade.get('roi', 0) / 100))
            
            if trade.get('res') == "LOSS":
                racha_perdedora += 1
                horas_malas.append(int(trade.get('h', 0)))
            else:
                racha_perdedora = 0 # Si gana, resetea la mala racha
        
        # LÓGICA DE LAS X: Si pierde, baja. Si gana, sube hasta 15.
        apalancamiento_actual = max(x_min, x_max - (racha_perdedora * 3)) 
        
        return cap_acumulado, apalancamiento_actual, list(set(horas_malas))
    else:
        r.lpush("historial_bot", json.dumps(datos))

# --- 📊 2. ESTRATEGIA TÉCNICA (EMAs y RSI) ---
def analizar_mercado(simbolo, cliente):
    try:
        klines = cliente.get_klines(symbol=simbolo, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','etc1','etc2','etc3','etc4','etc5','etc6'])
        df['close'] = df['close'].astype(float)

        ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]

        precio_actual = df['close'].iloc[-1]
        caida = ((precio_actual - df['close'].iloc[-4]) / df['close'].iloc[-4]) * 100

        # Muerde si hay caída, RSI bajo y el precio está por encima de la vela anterior
        if caida < -2.0 and rsi < 30 and precio_actual > df['close'].iloc[-2]:
            return True, precio_actual, f"🐊 ATAQUE! RSI: {rsi:.1f}"
        
        return False, precio_actual, "Acechando..."
    except:
        return False, 0, "Error"

# --- 🚀 3. EJECUCIÓN CON REGLAS DE ORO ---
cap_real, x_actual, bloqueos = gestionar_memoria(leer=True)
print(f"🦁 BOT V92: MODO COCODRILO DINÁMICO")
print(f"💰 CAP: ${cap_real:.2f} | APALANCAMIENTO: {x_actual}x | MAX: 15x")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    h = int(time.strftime('%H'))
    if h in bloqueos:
        print(f"⏳ Hora {h} bloqueada. El Cocodrilo protege su capital.", end='\r')
        time.sleep(600); continue

    for p in presas:
        puedo, precio, razon = analizar_mercado(p, Client())
        print(f"🧐 {p}: {razon} | Cap: ${cap_real:.2f} | X: {x_actual}", end='\r')
        
        if puedo:
            print(f"\n🚀 [ENTRADA] {p} a {precio} con {x_actual}x y Break-even.")
            # Al terminar: gestionar_memoria(False, {'m': p, 'roi': 5.0, 'res': 'WIN', 'h': h})
            
    time.sleep(15)
