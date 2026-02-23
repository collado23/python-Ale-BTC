import os, time, datetime
from binance.client import Client
from binance.enums import *

def bot():
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"), {"timeout": 20})
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    piso_memoria = {} 
    ultimo_cierre_ts = 0

    def esta_en_horario():
        tz_arg = datetime.timezone(datetime.timedelta(hours=-3))
        ahora = datetime.datetime.now(tz_arg)
        h = ahora.hour + ahora.minute/60
        return (11.0 <= h <= 18.0) or (h >= 22.5 or h <= 6.0)

    print("🚀 V177 | FOCO TOTAL USDC | 90% CAPITAL | EMAs 9/27")

    while True:
        try:
            # --- BUSCAMOS EL SALDO EN USDC ---
            acc_info = c.futures_account(recvWindow=10000)
            disponible = 0.0
            for b in acc_info['assets']:
                if b['asset'] == 'USDC': # PRIORIDAD ABSOLUTA USDC
                    disponible = float(b['availableBalance'])
                    break

            # 1. VERIFICAR POSICIONES EN USDC
            pos_info = c.futures_position_information(recvWindow=10000)
            activa = None
            for p in pos_info:
                amt = float(p.get('positionAmt', 0))
                # Solo tomamos posiciones de pares USDC
                if amt != 0 and 'USDC' in p['symbol']:
                    activa = {'s':p['symbol'], 'l':'LONG' if amt>0 else 'SHORT',
                              'p':float(p['entryPrice']), 'q':abs(amt), 'x':int(p.get('leverage', 5))}
                    break

            # 2. GESTIÓN DE POSICIÓN (TRAILING 0.5% DESDE 2.5%)
            if activa:
                m_p = float(c.futures_mark_price(symbol=activa['s'])['markPrice'])
                diff = (m_p - activa['p'])/activa['p'] if activa['l']=="LONG" else (activa['p'] - m_p)/activa['p']
                roi = diff * 100 * activa['x']

                if activa['s'] not in piso_memoria: piso_memoria[activa['s']] = -4.0

                if roi >= 2.5:
                    nuevo_piso = roi - 0.5
                    if nuevo_piso > piso_memoria[activa['s']]:
                        piso_memoria[activa['s']] = nuevo_piso
                
                if roi <= piso_memoria[activa['s']]:
                    c.futures_create_order(symbol=activa['s'], side=SIDE_SELL if activa['l']=="LONG" else SIDE_BUY, 
                                         type=ORDER_TYPE_MARKET, quantity=activa['q'], recvWindow=10000)
                    print(f"\n✅ CIERRE USDC EN {activa['s']} | ROI: {roi:.2f}%")
                    piso_memoria = {}; ultimo_cierre_ts = time.time()
                    time.sleep(15)
                else:
                    print(f"💰 ${disponible:.2f} USDC | {activa['s']} | ROI: {roi:.2f}% | PISO: {piso_memoria[activa['s']]:.2f}%", end='\r')

            # 3. ENTRADA SOLO PARES USDC AL 90%
            elif esta_en_horario():
                if time.time() - ultimo_cierre_ts < 120:
                    print(f"⏳ ${disponible:.2f} USDC | Enfriamiento...", end='\r')
                    time.sleep(10); continue

                # Solo escaneamos pares USDC
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, ov = float(k[-2][4]), float(k[-2][1])
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27
                    e9_ant = sum([float(x[4]) for x in k[-10:-1]])/9

                    dir_e = None
                    if cl > e9 and e9 > e27 and e9 > e9_ant: dir_e = 'LONG'
                    elif cl < e9 and e9 < e27 and e9 < e9_ant: dir_e = 'SHORT'

                    if dir_e:
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        prec = 0 if 'XRP' in m else (1 if 'SOL' in m else 2)
                        
                        # USAMOS EL 90% DEL DISPONIBLE EN USDC
                        cant = round(((disponible * 0.90) * 5) / p_act, prec)

                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY if dir_e=='LONG' else SIDE_SELL, 
                                                 type=ORDER_TYPE_MARKET, quantity=cant, recvWindow=10000)
                            print(f"\n🎯 ENTRADA USDC {dir_e} EN {m}")
                            time.sleep(30); break
                
                print(f"💰 ${disponible:.2f} USDC | Acechando... {datetime.datetime.now().strftime('%H:%M:%S')}", end='\r')
            else:
                print(f"💰 ${disponible:.2f} USDC | Fuera de horario", end='\r')

        except Exception as e:
            time.sleep(15)
        time.sleep(10)

if __name__ == "__main__": bot()
