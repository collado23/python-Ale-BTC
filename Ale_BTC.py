import os, time, threading, datetime
from binance.client import Client
from binance.enums import *

def bot():
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    ops_piso = {} 

    def esta_en_horario():
        tz_arg = datetime.timezone(datetime.timedelta(hours=-3))
        ahora = datetime.datetime.now(tz_arg)
        h = ahora.hour + ahora.minute/60
        return (11.0 <= h <= 18.0) or (h >= 22.5 or h <= 6.0)

    print("🚀 V162 | ESTRATEGIA EMA + PISO PROTEGIDO")

    while True:
        try:
            # 1. POSICIÓN REAL
            pos_reales = c.futures_position_information()
            pos_activa = None
            for p in pos_reales:
                amt = float(p.get('positionAmt', 0))
                if amt != 0:
                    pos_activa = {'s':p['symbol'],'l':'LONG' if amt>0 else 'SHORT',
                                  'p':float(p['entryPrice']),'q':abs(amt),'x':int(p.get('leverage', 5))}
                    break

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

                # Si es nueva o reinicio, inicializar piso
                if o['s'] not in ops_piso:
                    # Si ya entra con ganancia, le damos margen de 1% para no cerrar ya
                    ops_piso[o['s']] = roi - 1.0 if roi > 2.5 else -4.0

                # Solo subimos el piso si el ROI es mayor a 2.5%
                if roi >= 2.5:
                    nuevo_posible_piso = roi - 0.5
                    if nuevo_posible_piso > ops_piso[o['s']]:
                        ops_piso[o['s']] = nuevo_posible_piso

                p_f = ops_piso[o['s']]
                
                # CIERRE (Solo si el ROI cae por debajo del piso)
                if roi <= p_f:
                    # Doble check para evitar cierres por errores de conexión
                    time.sleep(1)
                    m_p_check = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                    diff_c = (m_p_check - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - m_p_check)/o['p']
                    if (diff_c * 100 * o['x']) <= p_f:
                        c.futures_create_order(symbol=o['s'], side=SIDE_SELL if o['l']=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=o['q'])
                        print(f"\n💰 CIERRE EJECUTADO EN {roi:.2f}%")
                        ops_piso = {}; time.sleep(30)
                else:
                    print(f"💰 ${cap:.2f} | {o['s']} | ROI: {roi:.2f}% | PISO: {p_f:.2f}%", end='\r')

            # 4. ENTRADA (EMAs)
            elif esta_en_horario():
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, ov = float(k[-2][4]), float(k[-2][1])
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27

                    if (cl > ov and cl > e9 and e9 > e27) or (cl < ov and cl < e9 and e9 < e27):
                        c.futures_change_leverage(symbol=m, leverage=5)
                        time.sleep(2)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((cap * 0.80) * 5) / p_act, 1 if 'XRP' not in m else 0)
                        
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY if cl > ov else SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"\n🎯 DISPARO EN {m}")
                            time.sleep(20); break
            else:
                print(f"💰 ${cap:.2f} | Acechando... | {datetime.datetime.now().strftime('%H:%M:%S')}", end='\r')

        except Exception as e:
            time.sleep(10)
        time.sleep(10)

if __name__ == "__main__": bot()
