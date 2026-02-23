import os, time, threading, datetime
from binance.client import Client
from binance.enums import *

def bot():
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    ops_piso = {} 
    ultimo_cierre_ts = 0 

    def esta_en_horario():
        tz_arg = datetime.timezone(datetime.timedelta(hours=-3))
        h = datetime.datetime.now(tz_arg).hour + datetime.datetime.now(tz_arg).minute/60
        return (11.0 <= h <= 18.0) or (h >= 22.5 or h <= 6.0)

    print("🚀 V164 | ESTRATEGIA EMA | ENFRIAMIENTO: 2 MIN | TRAILING 0.5%")

    while True:
        try:
            # 1. ESCANEO DE POSICIÓN
            pos_reales = c.futures_position_information()
            pos_activa = None
            for p in pos_reales:
                amt = float(p.get('positionAmt', 0))
                if amt != 0:
                    pos_activa = {'s':p['symbol'],'l':'LONG' if amt>0 else 'SHORT',
                                  'p':float(p['entryPrice']),'q':abs(amt),'x':int(p.get('leverage', 5))}
                    break

            if not pos_activa: ops_piso = {}

            # 2. SALDO
            cap = 0.0
            for b in c.futures_account_balance():
                if b['asset'] == 'USDC': cap = float(b['balance'])

            # 3. GESTIÓN DE TRAILING (0.5%)
            if pos_activa:
                o = pos_activa
                m_p = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                diff = (m_p - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - m_p)/o['p']
                roi = diff * 100 * o['x']

                if o['s'] not in ops_piso:
                    ops_piso[o['s']] = roi - 0.7 if roi > 2.5 else -4.0

                if roi >= 2.5:
                    nuevo_piso = roi - 0.5
                    if nuevo_piso > ops_piso[o['s']]:
                        ops_piso[o['s']] = nuevo_piso

                p_f = ops_piso[o['s']]
                
                if roi <= p_f:
                    c.futures_create_order(symbol=o['s'], side=SIDE_SELL if o['l']=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"\n💰 CIERRE EN {roi:.2f}% | ESPERANDO 2 MINUTOS PARA VOLVER A EVALUAR")
                    ultimo_cierre_ts = time.time()
                    ops_piso = {}
                    time.sleep(10)
                else:
                    print(f"💰 ${cap:.2f} | {o['s']} | ROI: {roi:.2f}% | PISO: {p_f:.2f}%", end='\r')

            # 4. ENTRADA (CON FRENO DE 120 SEGUNDOS)
            elif esta_en_horario():
                # Freno de mano de 2 minutos (120 segundos)
                if time.time() - ultimo_cierre_ts < 120:
                    espera = int(120 - (time.time() - ultimo_cierre_ts))
                    print(f"⏳ ENFRIAMIENTO: {espera}s...", end='\r')
                    time.sleep(5)
                    continue

                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, ov = float(k[-2][4]), float(k[-2][1])
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27

                    # TU PATRÓN EMA 9 / 27
                    if (cl > ov and cl > e9 and e9 > e27) or (cl < ov and cl < e9 and e9 < e27):
                        c.futures_change_leverage(symbol=m, leverage=5)
                        time.sleep(2)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((cap * 0.80) * 5) / p_act, 1 if 'XRP' not in m else 0)
                        
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY if cl > ov else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"\n🎯 ENTRADA POR EMA EN {m}")
                            time.sleep(15)
                            break
            else:
                print(f"💰 ${cap:.2f} | Acechando... | {datetime.datetime.now().strftime('%H:%M:%S')}", end='\r')

        except Exception as e:
            time.sleep(10)
        time.sleep(10)

if __name__ == "__main__": bot()
