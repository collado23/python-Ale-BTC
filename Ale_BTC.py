import os, time, redis
from binance.client import Client

# --- 🧠 LÓGICA DE PERSISTENCIA TOTAL ---
class MemoriaBlindada:
    def __init__(self):
        # Conexión a la memoria externa (Redis)
        try:
            self.r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
        except:
            self.r = None
        
    def set(self, clave, valor, expira=None):
        if self.r:
            self.r.set(clave, str(valor))
            if expira: self.r.expire(clave, expira)

    def get(self, clave, default=None):
        if self.r:
            v = self.r.get(clave)
            return v.decode() if v else default
        return default

def bot():
    c = Client()
    db = MemoriaBlindada()

    # --- 1. RECUPERAR INFORMACIÓN GUARDADA ---
    # Aunque cambies el código, si 'saldo_eterno' existe en Redis, lo usa.
    cap = float(db.get("saldo_eterno", 12.85))
    ops = []

    print(f"🧠 MEMORIA BLINDADA V237 | RECUPERADO: ${cap}")

    while True:
        t_ciclo = time.time()
        try:
            tks = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            for o in ops[:]:
                p_act = tks[o['s']]
                # Lógica Contable con comisiones de Binance
                roi = (((p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']) * 100 * o['x']) - (0.12 * o['x'])

                # --- 2. LÓGICA DE "LA SUBE" O "LA BAJA" ---
                # Si el ROI neto es > 0.5%, la sube a 15x
                if o['x'] == 5 and roi > 0.5:
                    o['x'] = 15
                    print(f"🔥 LÓGICA: Tendencia confirmada. Subiendo a 15x en {o['s']}")

                # --- 3. GUARDAR RESULTADOS EN LA MEMORIA EXTERNA ---
                if roi <= -1.2 or (o['x'] == 15 and roi < 0.2) or roi >= 15.0:
                    cap *= (1 + (roi/100))
                    
                    # AQUÍ SE GUARDA LA INFO PARA EL PRÓXIMO CÓDIGO
                    db.set("saldo_eterno", cap) 
                    if roi < 0:
                        db.set(f"bloqueo_{o['s']}", "true", 600) # Bloquea 10 min si perdió
                    
                    ops.remove(o)
                    print(f"💾 INFO GUARDADA EN REDIS | NUEVO SALDO: ${cap:.2f}")

            # --- 4. LÓGICA DE ENTRADA (LIBRO DE VELAS) ---
            if len(ops) < 1:
                for coin in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    # Revisa si la moneda está bloqueada en la memoria externa
                    if db.get(f"bloqueo_{coin}"): continue
                    
                    k = c.get_klines(symbol=coin, interval='1m', limit=5)
                    v = k[-2] # Última vela cerrada
                    op, hi, lo, cp = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    
                    # Lógica del Libro: Cuerpo vs Mecha
                    cuerpo = abs(cp - op)
                    rango = hi - lo
                    
                    # Solo entra si el cuerpo es dominante (Lógica de Fuerza)
                    if cuerpo > (rango * 0.7) and (cuerpo/op) > 0.0008:
                        # Confirmamos con EMAs
                        kl_e = c.get_klines(symbol=coin, interval='1m', limit=30)
                        cl_e = [float(x[4]) for x in kl_e]
                        e9, e27 = sum(cl_e[-9:])/9, sum(cl_e[-27:])/27

                        if e9 > e27 and cp > op:
                            ops.append({'s':coin, 'l':'LONG', 'p':tks[coin], 'x':5})
                            print(f"🎯 ENTRADA 5x: {coin} (Patrón de Fuerza)")
                            break
                        elif e9 < e27 and cp < op:
                            ops.append({'s':coin, 'l':'SHORT', 'p':tks[coin], 'x':5})
                            print(f"🎯 ENTRADA 5x: {coin} (Patrón de Fuerza)")
                            break

            print(f"📡 Memoria Activa (Redis): ${cap:.2f} | {time.strftime('%H:%M:%S')}", end='\r')
            
        except Exception as e:
            time.sleep(2)

        time.sleep(max(1, 4 - (time.time() - t_ciclo)))

if __name__ == "__main__": bot()
