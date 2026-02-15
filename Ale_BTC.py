import os, time, redis
from binance.client import Client

# --- 🧠 LÓGICA DE MEMORIA ---
class MemoriaLógica:
    def __init__(self):
        try: self.r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None 
        except: self.r = None
        self.local = {}
    def escribir(self, k, v, ex=None):
        if self.r: self.r.setex(k, ex, str(v)) if ex else self.r.set(k, str(v))
        self.local[k] = v
    def leer(self, k):
        if self.r:
            v = self.r.get(k)
            if v: return v.decode()
        return self.local.get(k)

def bot():
    c = Client()
    mem = MemoriaLógica()
    cap = float(mem.leer("cap_final") or 13.05)
    ops = []

    print(f"🦁 V231 LÓGICA ESTRUCTURAL | SALDO: ${cap}")

    while True:
        t_loop = time.time()
        try:
            tks = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            for o in ops[:]:
                p_act = tks[o['s']]
                diff = (p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']
                roi = (diff * 100 * o['x']) - (0.1 * o['x'])

                # --- 🚀 LÓGICA DE ESCALADA (CUÁNDO METER 15x) ---
                if o['x'] == 5 and roi > 0.5: # Si ya ganamos el 0.5% con 5x...
                    # Consultamos al Libro de Velas por fuerza extra
                    k = c.get_klines(symbol=o['s'], interval='1m', limit=3)
                    v_ahora = float(k[-1][4]) # Precio cierre actual
                    v_ante = float(k[-2][4])
                    
                    # Si la vela actual sigue confirmando la dirección
                    if (o['l'] == 'LONG' and v_ahora > v_ante) or (o['l'] == 'SHORT' and v_ahora < v_ante):
                        o['x'] = 15
                        print(f"🔥 LÓGICA: Tendencia confirmada. Subiendo a 15x en {o['s']}")

                # --- LÓGICA DE SALIDA (TRAILING) ---
                max_r = float(mem.leer(f"max_{o['s']}") or 0)
                if roi > max_r: mem.escribir(f"max_{o['s']}", roi)

                # Si el 15x falla y baja del pico, cerramos rápido para no perder
                if roi <= -1.1 or (roi > 1.5 and roi < max_r - 1.0) or roi >= 15.0:
                    cap *= (1 + (roi/100))
                    mem.escribir("cap_final", cap)
                    mem.escribir(f"block_{o['s']}", "1", 40)
                    ops.remove(o)
                    print(f"✅ CIERRE LÓGICO: {roi:.2f}% | BAL: ${cap:.2f}")

            # --- LÓGICA DE ENTRADA (EL LIBRO) ---
            if len(ops) < 1:
                for coin in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if mem.leer(f"block_{coin}"): continue
                    
                    k = c.get_klines(symbol=coin, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # Datos de la última vela (Libro)
                    v = k[-2]; o_p, h_p, l_p, c_p = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(c_p - o_p)
                    rango = h_p - l_p

                    # Lógica de Entrada: Cruce de EMAs + Vela de Decisión (Cuerpo > 60% del rango)
                    if e9 > e27 and c_p > o_p and cuerpo > (rango * 0.6):
                        ops.append({'s':coin, 'l':'LONG', 'p':tks[coin], 'x':5})
                        print(f"🎯 ENTRADA 5x: {coin} (Esperando fuerza para 15x)")
                        break
                    if e9 < e27 and c_p < o_p and cuerpo > (rango * 0.6):
                        ops.append({'s':coin, 'l':'SHORT', 'p':tks[coin], 'x':5})
                        print(f"🎯 ENTRADA 5x: {coin} (Esperando fuerza para 15x)")
                        break

            print(f"📡 Lógica Activa: ${cap:.2f} | {time.strftime('%H:%M:%S')}", end='\r')
        except Exception as e: time.sleep(2)
        time.sleep(max(1, 4 - (time.time() - t_loop)))

if __name__ == "__main__": bot()
