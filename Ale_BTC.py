import os, time
from binance.client import Client
from binance.enums import *

def bot():
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET")) 
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    # MEMORIA DEL BOT (No se borra mientras la operacion siga abierta)
    max_roi = 0
    piso = -4.0

    print("🚀 V178 FIX | MURO 2.0% SIN VUELTAS")

    while True:
        try:
            acc = c.futures_account()
            disponible = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            pos = c.futures_position_information()
            activa = next((p for p in pos if float(p.get('positionAmt', 0)) != 0), None)

            if activa:
                sym = activa['symbol']
                entry = float(activa['entryPrice'])
                q = abs(float(activa['positionAmt']))
                side = 'LONG' if float(activa['positionAmt']) > 0 else 'SHORT'
                m_p = float(c.futures_mark_price(symbol=sym)['mark_price'])
                
                roi = ((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * 100 * 5 
                
                # ACTUALIZA EL MÁXIMO (MEMORIA)
                if roi > max_roi:
                    max_roi = roi
                
                # LÓGICA DEL MURO 2.0%
                if max_roi >= 2.0:
                    # Si el trailing (max-0.5) es menor a 2, se queda en 2. 
                    # Si es mayor, sube. NUNCA baja de lo que ya subio.
                    nuevo_piso = max(2.0, max_roi - 0.5)
                    if nuevo_piso > piso:
                        piso = nuevo_piso
                else:
                    piso = -4.0 
                
                # CIERRE REAL
                if roi <= piso:
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, 
                                         type=ORDER_TYPE_MARKET, quantity=q)
                    print(f"💰 CIERRE EN: {roi:.2f}% | PISO FINAL: {piso:.2f}%")
                    max_roi = 0
                    piso = -4.0
                    time.sleep(30)
                
                print(f"📊 {sym} | ROI: {roi:.2f}% | MAX: {max_roi:.2f}% | PISO: {piso:.2f}%", end='\r')

            else:
                max_roi = 0
                piso = -4.0
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl, e9, e27 = float(k[-2][4]), sum(float(x[4]) for x in k[-9:])/9, sum(float(x[4]) for x in k[-27:])/27
                    if (cl > e9 > e27) or (cl < e9 < e27):
                        side_in = SIDE_BUY if cl > e9 else SIDE_SELL
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((disponible * 0.90) * 5) / p_act, 1)
                        c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                        break
                print(f"🔍 Acechando... ${disponible:.2f}", end='\r')

        except Exception as e:
            time.sleep(2)
        time.sleep(2)

if __name__ == "__main__":
    bot()
