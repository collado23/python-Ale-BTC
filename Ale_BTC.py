import os, time
from binance.client import Client

# --- VARIABLES DE ENTORNO ---
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

def bot():
    c = Client(API_KEY, API_SECRET)
    monedas = ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'ADAUSDT']
    leverage = 15 
    capital_real = 15.0 

    print(f"🦅 V4300 - ANALIZANDO DOBLE VELA (Filtro Anti-Rachas Malas)")
    print(f"💰 CAPITAL: ${capital_real} | 15X")

    while True:
        try:
            posiciones = c.futures_position_information()
            activa = [p for p in posiciones if float(p['positionAmt']) != 0]

            if activa:
                p = activa[0]
                simbolo = p['symbol']
                lado = "LONG" if float(p['positionAmt']) > 0 else "SHORT"
                p_entrada = float(p['entryPrice'])
                p_actual = float(c.futures_symbol_ticker(symbol=simbolo)['price'])
                
                diff = (p_actual - p_entrada)/p_entrada if lado=="LONG" else (p_entrada - p_actual)/p_actual
                roi_neto = (diff * 100 * leverage) - 1.2 
                
                # Para salir también miramos las últimas 2 velas
                k = c.futures_klines(symbol=simbolo, interval='1m', limit=5)
                # Si las últimas 2 velas cerraron en contra de nuestra posición, salimos
                v_cerrada1 = k[-2]
                v_cerrada2 = k[-3]
                
                color1 = "VERDE" if float(v_cerrada1[4]) > float(v_cerrada1[1]) else "ROJA"
                color2 = "VERDE" if float(v_cerrada2[4]) > float(v_cerrada2[1]) else "ROJA"

                cierre = False
                if roi_neto >= 3.0: # Bajamos un poco el objetivo para asegurar ante la volatilidad
                    if (lado == "LONG" and color1 == "ROJA" and color2 == "ROJA") or \
                       (lado == "SHORT" and color1 == "VERDE" and color2 == "VERDE"):
                        cierre, motivo = True, "🎯 PROFIT (Doble vela de giro)"
                
                elif roi_neto <= -3.5:
                    cierre, motivo = True, "❌ SL PROTECT"

                if cierre:
                    side_out = "SELL" if lado == "LONG" else "BUY"
                    c.futures_create_order(symbol=simbolo, side=side_out, type="MARKET", quantity=abs(float(p['positionAmt'])))
                    print(f"{motivo} | ROI: {roi_neto:.2f}%")
            
            else:
                for m in monedas:
                    k_1m = c.futures_klines(symbol=m, interval='1m', limit=10)
                    # 4 velas previas para saturación
                    v_previa = k_1m[-7:-3] 
                    # 2 velas para confirmar el giro (análisis de cada dos velas)
                    v_giro = k_1m[-3:-1] 
                    
                    eran_rojas = all(float(v[4]) < float(v[1]) for v in v_previa)
                    eran_verdes = all(float(v[4]) > float(v[1]) for v in v_previa)
                    
                    giro_verde = all(float(v[4]) > float(v[1]) for v in v_giro)
                    giro_rojo = all(float(v[4]) < float(v[1]) for v in v_giro)

                    p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                    gatillo = ""

                    # LONG: 4 rojas + 2 verdes seguidas (Confirmación de subida)
                    if eran_rojas and giro_verde:
                        gatillo = "BUY"
                    # SHORT: 4 verdes + 2 rojas seguidas (Confirmación de caída)
                    if eran_verdes and giro_rojo:
                        gatillo = "SELL"

                    if gatillo:
                        info = c.futures_exchange_info()
                        prec = [i['quantityPrecision'] for i in info['symbols'] if i['symbol'] == m][0]
                        qty = round((capital_real * leverage) / p_act, prec)
                        c.futures_create_order(symbol=m, side=gatillo, type="MARKET", quantity=qty)
                        print(f"🚀 ENTRADA CONFIRMADA (2 VELAS): {gatillo} en {m}")
                        break

            print(f"📊 Analizando pares de velas... Capital: ${capital_real}    ", end='\r')

        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__": bot()
