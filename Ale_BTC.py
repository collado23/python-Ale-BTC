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
        # Horario Argentina: 11 a 18 y 22:30 a 06:00
        return (11.0 <= h <= 18.0) or (h >= 22.5 or h <= 6.0)

    print("🚀 V161 | TU PATRÓN EMA | TRAILING 0.5% SIN TECHO")

    while True:
        try:
            # 1. VERIFICAR POSICIÓN REAL
            pos_reales = c.futures_position_information()
            pos_activa = None
            for p in pos_reales:
                amt = float(p.get('positionAmt', 0))
                if amt != 0:
                    pos_activa = {
                        's': p['symbol'], 'l': 'LONG' if amt > 0 else 'SHORT',
                        'p': float(p['entryPrice']), 'q': abs(amt), 'x': int(p.get('leverage', 5))
                    }
                    break

            if not pos_activa: ops_piso = {} # Reseteo si no hay nada

            # 2. SALDO USDC
            cap = 0.0
            for b in c.futures_account_balance():
                if b['asset'] == 'USDC': cap = float(b['balance'])

            # 3. GESTIÓN DEL TRAILING STOP
            if pos_activa:
                o = pos_activa
                m_p = float(c.futures_mark_price(symbol=o['s'])['markPrice'])
                diff = (m_p - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - m_p)/o['p']
                roi = diff * 100 * o['x']

                if o['s'] not in ops_piso: ops_piso[o['s']] = -4.0 # SL Inicial

                # LOGICA TRAILING 0.5%: Empieza en 2.5% de ROI
                if roi >= 2.5:
                    nuevo_piso = roi - 0.5
                    if nuevo_piso > ops_piso[o['s']]:
                        ops_piso[o['s']] = nuevo_piso

                p_f = ops_piso[o['s']]
                
                # Cierre solo si toca el piso (puede llegar a ROI 50, 100, etc)
                if roi <= p_f:
                    lado_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=lado_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"\n💰 CIERRE EXITOSO EN ROI: {roi:.2f}%")
                    time.sleep(20)
                else:
                    print(f"💰 ${cap:.2f} | {o['s']} | ROI: {roi:.2f}% | PISO: {p_f:.2f}%", end='\r')

            # 4. ENTRADA (PATRÓN EMA 9/27)
            elif esta_en_horario():
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, ov = float(k[-2][4]), float(k[-2][1])
                    e9 = sum([float(x[4]) for x in k[-9:]])/9
                    e27 = sum([float(x[4]) for x in k[-27:]])/27

                    # Tu Estrategia:
                    if (cl > ov and cl > e9 and e9 > e27) or (cl < ov and cl < e9 and e9 < e27):
                        c.futures_change_leverage(symbol=m, leverage=5)
                        time.sleep(2)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((cap * 0.80) * 5) / p_act, 1 if 'XRP' not in m else 0)
                        
                        if cant > 0:
                            side_e = SIDE_BUY if cl > ov else SIDE_SELL
                            c.futures_create_order(symbol=m, side=side_e, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"\n🎯 DISPARO {m} POR CRUCE DE EMAS")
                            time.sleep(15)
                            break
            else:
                print(f"💰 ${cap:.2f} | Esperando Hora... | {datetime.datetime.now().strftime('%H:%M:%S')}", end='\r')

        except Exception as e:
            time.sleep(10)
        time.sleep(10)

if __name__ == "__main__": bot()
