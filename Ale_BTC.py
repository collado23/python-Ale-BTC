import os, time, threading, redis, json
from binance.client import Client

# --- 🧠 CONEXIÓN A LA MEMORIA INMORTAL (Redis) ---
# Esto lee la variable REDIS_URL que acabas de conectar
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria_redis(leer=False, datos=None):
    if not r:
        return 15.77, [] # Si no hay conexión, por lo menos mantenemos tu capital real

    if leer:
        # Buscamos los trades en la base de datos
        historial = r.lrange("historial_bot", 0, -1)
        
        # Si Redis está vacío (es la primera vez), le grabamos tu capital actual
        if not historial:
            print("💾 Redis vacío. Inicializando con $15.77...")
            return 15.77, []
        
        roi_total = 0
        horas_malas = []
        for t in historial:
            trade = json.loads(t)
            roi_total += trade['roi']
            if trade['res'] == "LOSS":
                horas_malas.append(int(trade['h']))
        
        cap_actual = 15.77 + (15.77 * (roi_total / 100))
        return cap_actual, list(set(horas_malas))
    else:
        # Cuando el bot termina un trade, lo guarda aquí para siempre
        nuevo_dato = {
            'm': datos['m'], 'roi': datos['roi'], 
            'res': datos['res'], 'h': time.strftime('%H')
        }
        r.lpush("historial_bot", json.dumps(nuevo_dato))

# --- 🚀 ARRANQUE ---
capital_real, bloqueos = gestionar_memoria_redis(leer=True)
print(f"✅ BOT CON MEMORIA REAL | CAPITAL: ${capital_real:.2f}")

while True:
    # El bot ahora es inmortal. Si Railway lo apaga (Stopping Container),
    # al volver a arrancar leerá Redis y seguirá en $15.77.
    print(f"Vigilando... Cap: ${capital_real:.2f} | Horas OFF: {bloqueos}", end='\r')
    time.sleep(10)
