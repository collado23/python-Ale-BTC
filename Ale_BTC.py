import os, time
from binance.client import Client
from binance.enums import *

def bot():
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET")) 
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    max_roi = 0
    piso = -4.0

    print("🚀 V180 DEFINITIVO | MURO 2% | ESPERA 30s | TRAILING 0.5%")

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
                
                # PRECIO MARK (CORRECTO)
                res = c.futures_mark_price(symbol=sym)
                m_p = float(res['markPrice'])
                
                roi = ((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * 100 * 5 
                
                if roi > max_roi:
                    max_roi = roi
                
                # --- LÓGICA RÍGIDA DE SALIDA ---
                if max_roi >= 2.5:
                    piso = max_roi - 0.5  # Trailing activo arriba de 2.5%
                elif max_roi >= 2.0:
                    piso = 2.0            # Muro clavado en 2.0%
                else:
                    piso = -4.0           # Stop Loss inicial
                
                # CIERRE DE POSICIÓN
                if roi <= piso:
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, 
                                         type=ORDER_TYPE_MARKET, quantity=q)
                    print(f"\n💰 CIERRE EJECUTADO EN: {roi:.2f}% | PISO: {piso:.2f}%")
                    
                    # --- EL REINICIO CON ESPERA ---
                    max_roi = 0
                    piso = -4.0
                    print("⏳ ESPERA OBLIGATORIA DE 30 SEGUNDOS...")
                    time.sleep(30) # Se duerme 30 segundos antes de volver al bucle
                    continue # Salta al inicio del while para refrescar todo
                
                print(f"📊 {sym} | ROI: {roi:.2f}% | MAX: {max_roi:.2f}% | PISO: {piso:.2f}% | Saldo: {disponible:.2f}", end='\r')

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
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"\n🚀 ENTRADA: {m} | CANT: {cant}")
                            break
                print(f"🔍 BUSCANDO ENTRADA... | SALDO: {disponible:.2f} USDC", end='\r')

        except Exception as e:
            time.sleep(5)
        time.sleep(2)

if __name__ == "__main__":
    bot()
