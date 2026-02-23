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

    print("🛡️ V173 | PRECISIÓN TOTAL | 90% DISPONIBLE | EMAs 9/27")

    while True:
        try:
            # 1. ESTADO DE POSICIONES
            pos_info = c.futures_position_information(recvWindow=10000)
            activa = None
            for p in pos_info:
                amt = float(p.get('positionAmt', 0))
                if amt != 0:
                    activa = {'s':p['symbol'], 'l':'LONG' if amt>0 else 'SHORT',
                              'p':float(p['entryPrice']), 'q':abs(amt), 'x':int(p.get('leverage', 5))}
                    break

            # 2. GESTIÓN SI HAY POSICIÓN (Trailing 0.5% desde 2.5%)
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
                    print(f"\n✅ CIERRE EN {activa['s']} | ROI: {roi:.2f}%")
                    piso_memoria = {}
                    ultimo_cierre_ts = time.time()
                    time.sleep(15)
                else:
                    print(f"💰 {activa['s']} | ROI: {roi:.2f}% | PISO: {piso_memoria[activa['s']]:.2f}%", end='\r')

            # 3. ENTRADA CON FILTRO DE TENDENCIA CONFIRMADA
            elif esta_en_horario():
                if time.time() - ultimo_cierre_ts < 120:
                    time.sleep(10); continue

                acc = c.futures_account(recvWindow=10000)
                disponible = float(acc['availableBalance'])

                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    
                    # Datos de vela actual y anteriores para ver la pendiente
                    cl, ov = float(k[-2][4]), float(k[-2][1])
                    
                    # Cálculo de EMAs actuales
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27
                    
                    # Cálculo de EMA 9 de la vela anterior (para ver si sube o baja)
                    e9_ant = sum([float(x[4]) for x in k[-10:-1]])/9

                    dir_e = None
                    # LONG: Precio > EMA9 > EMA27 Y EMA9 subiendo
                    if cl > e9 and e9 > e27 and e9 > e9_ant:
                        dir_e = 'LONG'
                    # SHORT: Precio < EMA9 < EMA27 Y EMA9 bajando
                    elif cl < e9 and e9 < e27 and e9 < e9_ant:
                        dir_e = 'SHORT'

                    if dir_e:
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        
                        # Cantidad al 90% con precisión por moneda
                        prec = 0 if 'XRP' in m else (1 if 'SOL' in m else 2)
                        cant = round(((disponible * 0.90) * 5) / p_act, prec)

                        if cant > 0:
                            try: c.futures_cancel_all_open_orders(symbol=m, recvWindow=10000)
                            except: pass
                            
                            c.futures_create_order(symbol=m, side=SIDE_BUY if dir_e=='LONG' else SIDE_SELL, 
                                                 type=ORDER_TYPE_MARKET, quantity=cant, recvWindow=10000)
                            print(f"\n🎯 DISPARO {dir_e} EN {m} (FILTRO DE PENDIENTE ACTIVO)")
                            time.sleep(30); break
            else:
                piso_memoria = {}
                print(f"💰 Acechando... {datetime.datetime.now().strftime('%H:%M:%S')}", end='\r')

        except Exception as e:
            time.sleep(15)
        time.sleep(10)

if __name__ == "__main__": bot()
