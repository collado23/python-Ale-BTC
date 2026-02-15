import os, time, redis
from binance.client import Client

class CerebroContable:
    def __init__(self):
        try: self.r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
        except: self.r = None
        self.mem = {}
    def escribir(self, k, v, ex=None):
        if self.r: self.r.setex(k, ex, str(v)) if ex else self.r.set(k, str(v))
        self.mem[k] = v
    def leer(self, k):
        if self.r:
            v = self.r.get(k); return v.decode() if v else None
        return self.mem.get(k)

def bot():
    c = Client()
    m = CerebroContable()
    cap = float(m.leer("cap_real") or 13.05)
    ops = []
    
    print(f"📖 V234 LIBRO + LÓGICA | SALDO: ${cap}")

    while True:
        t_loop = time.time()
        try:
            tks = {t['symbol']: float(t['price']) for t in c.get_all_tickers()}
            
            for o in ops[:]:
                p_act = tks[o['s']]
                # ROI Neto real con comisiones de Binance
                roi = (((p_act - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_act)/o['p']) * 100 * o['x']) - (0.1 * o['x'])

                # --- 🧠 LÓGICA DEL LIBRO PARA "SUBIRLA" O "BAJARLA" ---
                k = c.get_klines(symbol=o['s'], interval='1m', limit=5)
                v1 = {'o':float(k[-1][1]), 'c':float(k[-1][4]), 'h':float(k[-1][2]), 'l':float(k[-1][3])} # Vela actual
                v2 = {'o':float(k[-2][1]), 'c':float(k[-2][4])} # Vela anterior
                
                # 1. ¿CUÁNDO LA SUBE? (A 15x)
                # Si el libro muestra una vela de fuerza total (Marubozu) a nuestro favor
                if o['x'] == 5 and roi > 0.4:
                    fuerza = (v1['c'] > v1['o'] and v1['c'] > v2['c']) if o['l'] == 'LONG' else (v1['c'] < v1['o'] and v1['c'] < v2['c'])
                    if fuerza:
                        o['x'] = 15
                        print(f"🚀 LIBRO CONFIRMA FUERZA: Subiendo a 15x en {o['s']}")

                # 2. ¿CUÁNDO LA BAJA? (CIERRE LÓGICO)
                # Si aparece un Doji (indecisión) o una vela contraria fuerte, cerramos
                cuerpo = abs(v1['c'] - v1['o'])
                rango = v1['h'] - v1['l']
                es_doji = cuerpo < (rango * 0.1) # El cuerpo es casi nada
                
                contraria = (o['l'] == 'LONG' and v1['c'] < v1['o']) or (o['l'] == 'SHORT' and v1['c'] > v1['o'])

                if (es_doji and roi > 0.5) or (contraria and cuerpo > (rango * 0.5)) or roi <= -1.1 or roi >= 15.0:
                    cap *= (1 + (roi/100))
                    m.escribir("cap_real", cap)
                    m.escribir(f"block_{o['s']}", "1", 30)
                    ops.remove(o)
                    print(f"📉 LIBRO DICE CERRAR: ROI {roi:.2f}% | BAL: ${cap:.2f}")

            # --- ENTRADA (PATRONES DEL LIBRO) ---
            if len(ops) < 1:
                for coin in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT']:
                    if m.leer(f"block_{coin}"): continue
                    
                    k = c.get_klines(symbol=coin, interval='1m', limit=20)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    v = k[-2]
                    op, hi, lo, cl_p = float(v[1]), float(v[2]), float(v[3]), float(v[4])
                    cuerpo = abs(cl_p - op)
                    rango = hi - lo
                    
                    # Lógica de entrada: Patrón Envolvente + Tendencia EMA
                    if e9 > e27 and cl_p > op and cuerpo > (rango * 0.6):
                        ops.append({'s':coin, 'l':'LONG', 'p':tks[coin], 'x':5})
                        print(f"🎯 PATRÓN ENVOLVENTE LONG: {coin}")
                        break
                    elif e9 < e27 and cl_p < op and cuerpo > (rango * 0.6):
                        ops.append({'s':coin, 'l':'SHORT', 'p':tks[coin], 'x':5})
                        print(f"🎯 PATRÓN ENVOLVENTE SHORT: {coin}")
                        break

            print(f"📡 Libro en Mano: ${cap:.2f} | {time.strftime('%H:%M:%S')}", end='\r')
        except Exception as e: time.sleep(2)
        time.sleep(max(1, 4 - (time.time() - t_loop)))

if __name__ == "__main__": bot()
