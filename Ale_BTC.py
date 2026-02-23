import os, time
from binance.client import Client
from binance.enums import *

def bot():
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    piso_dinamico = -4.0  
    max_roi_alcanzado = 0

    print("🚀 V178-ENGANCHE | CONECTANDO Y BUSCANDO POSICIÓN...")

    while True:
        try:
            acc = c.futures_account()
            disponible = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            pos = c.futures_position_information()
            # ESTO ENGANCHA TU OPERACIÓN ACTUAL:
            activa = next((p for p in pos if float(p.get('positionAmt', 0)) != 0), None)

            if activa:
                sym = activa['symbol']
                entry = float(activa['entryPrice'])
                q = abs(float(activa['positionAmt']))
                side = 'LONG' if float(activa['positionAmt']) > 0 else 'SHORT'
                m_p = float(c.futures_mark_price(symbol=sym)['mark_price'])
                
                diff = (m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry
                roi = diff * 100 * 5 
                
                # Actualiza el máximo apenas arranca para no perder el rastro
                if roi > max_roi_alcanzado:
                    max_roi_alcanzado = roi
                
                # --- LÓGICA DE SUELO SEGURO (Muro en 2.0%) ---
                if max_roi_alcanzado >= 2.0:
                    piso_dinamico = max(2.0, max_roi_alcanzado - 0.5)
                else:
                    piso_dinamico = -4.0 
                
                if roi <= piso_dinamico:
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, 
                                         type=ORDER_TYPE_MARKET, quantity=q)
                    print(f"💰 CIERRE EN: {roi:.2f}% | PISO FINAL: {piso_dinamico:.2f}%")
                    max_roi_alcanzado = 0
                    piso_dinamico = -4.0
                    time.sleep(30)
                
                print(f"📊 {sym} (ENGANCHADA) | ROI: {roi:.2f}% | PISO: {piso_dinamico:.2f}%", end='\r')

            else:
                # Si no hay nada abierto, busca nuevas entradas
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = float(k[-2][4])
                    e9 = sum(float(x[4]) for x in k[-9:])/9
                    e27 = sum(float(x[4]) for x in k[-27:])/27

                    if cl > e9 and e9 > e27:
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((disponible * 0.90) * 5) / p_act, 1)
                        c.futures_create_order(symbol=m, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=cant)
                        break
                    elif cl < e9 and e9 < e27:
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((disponible * 0.90) * 5) / p_act, 1)
                        c.futures_create_order(symbol=m, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=cant)
                        break
                print(f"🔍 Acechando... ${disponible:.2f}", end='\r')

        except Exception as e:
            time.sleep(2)
        time.sleep(2)

if __name__ == "__main__":
    bot()
