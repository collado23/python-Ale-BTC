import os, time, datetime
from binance.client import Client
from binance.enums import *

def bot():
    # Timeout optimizado para respuesta rápida
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"), {"timeout": 10})
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    piso_memoria = {} 
    ultimo_cierre_ts = 0

    def esta_en_horario():
        tz_arg = datetime.timezone(datetime.timedelta(hours=-3))
        ahora = datetime.datetime.now(tz_arg)
        h = ahora.hour + ahora.minute/60
        return (11.0 <= h <= 18.0) or (h >= 22.5 or h <= 6.0)

    print("⚡ V178 | VELOCIDAD MÁXIMA | PRIORIDAD SOLUSDC | 90% CAP")

    while True:
        try:
            # Check rápido de saldo al principio
            acc = c.futures_account(recvWindow=5000)
            disponible = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)

            pos_info = c.futures_position_information(recvWindow=5000)
            activa = next((p for p in pos_info if float(p.get('positionAmt', 0)) != 0 and 'USDC' in p['symbol']), None)

            if activa:
                # Datos de posición
                sym = activa['symbol']
                entry = float(activa['entryPrice'])
                q = abs(float(activa['positionAmt']))
                lev = int(activa.get('leverage', 5))
                side = 'LONG' if float(activa['positionAmt']) > 0 else 'SHORT'
                
                m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
                diff = (m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry
                roi = diff * 100 * lev

                if sym not in piso_memoria: piso_memoria[sym] = -4.0
                if roi >= 2.5:
                    piso_memoria[sym] = max(piso_memoria[sym], roi - 0.5)
                
                if roi <= piso_memoria[sym]:
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, 
                                         type=ORDER_TYPE_MARKET, quantity=q, recvWindow=5000)
                    print(f"\n⚡ CIERRE RÁPIDO {sym} | ROI: {roi:.2f}%")
                    piso_memoria = {}; ultimo_cierre_ts = time.time()
                    time.sleep(5)
                else:
                    print(f"💰 ${disponible:.2f} | {sym} | ROI: {roi:.2f}% | PISO: {piso_memoria[sym]:.2f}%", end='\r')

            elif esta_en_horario():
                if time.time() - ultimo_cierre_ts < 60: # Bajé el enfriamiento a 1 min para no perder chances
                    time.sleep(2); continue

                # Escaneo ultra-veloz
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl, ov = float(k[-2][4]), float(k[-2][1])
                    e9 = sum(float(x[4]) for x in k[-9:])/9
                    e27 = sum(float(x[4]) for x in k[-27:])/27
                    e9_ant = sum(float(x[4]) for x in k[-10:-1])/9

                    dir_e = None
                    if cl > e9 and e9 > e27 and e9 > e9_ant: dir_e = 'LONG'
                    elif cl < e9 and e9 < e27 and e9 < e9_ant: dir_e = 'SHORT'

                    if dir_e:
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        prec = 0 if 'XRP' in m else (1 if 'SOL' in m else 2)
                        cant = round(((disponible * 0.90) * 5) / p_act, prec)

                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY if dir_e=='LONG' else SIDE_SELL, 
                                                 type=ORDER_TYPE_MARKET, quantity=cant, recvWindow=5000)
                            print(f"\n🚀 DISPARO {dir_e} EN {m} A LAS {datetime.datetime.now().strftime('%H:%M:%S')}")
                            time.sleep(10); break
                
                print(f"💰 ${disponible:.2f} | Acechando... {datetime.datetime.now().strftime('%H:%M:%S')}", end='\r')
            else:
                print(f"💰 ${disponible:.2f} | Fuera de horario", end='\r')

        except Exception:
            time.sleep(5)
        time.sleep(3) # Escaneo más frecuente (cada 3 seg)

if __name__ == "__main__": bot()
