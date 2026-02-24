import os, time, threading
from binance.client import Client
from binance.enums import *

# Memoria de picos para el Trailing
picos_maximos = {}

def vigilante_instantaneo(c, sym, side, q, entry, palanca, comision, stop_loss):
    """ Este hilo solo mira el precio y cierra a la velocidad del rayo """
    global picos_maximos
    picos_maximos[sym] = 0.0
    print(f"⚡ VIGILANTE ACTIVADO PARA {sym}")

    while True:
        try:
            # Pedimos solo el precio (Mark Price es el más rápido para futuros)
            m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
            
            # Cálculo de ROI Neto
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > picos_maximos[sym]:
                picos_maximos[sym] = roi
            
            # PISO: 1.05% de gatillo, con 0.3% de margen (o 0.2% si quieres más pegado)
            piso = picos_maximos[sym] - 0.3 if picos_maximos[sym] >= 1.05 else -99.0

            # GATILLO DE CIERRE AL TOQUE
            if (picos_maximos[sym] >= 1.05 and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n🚀 CIERRE INSTANTÁNEO EN {sym} | ROI: {roi:.2f}%")
                if sym in picos_maximos: del picos_maximos[sym]
                break 
            
            time.sleep(0.2) # Vigilancia extrema: 5 veces por segundo
        except Exception:
            break

def bot_quantum_flash():
    c = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca, monedas = 5, ['DOGEUSDC', 'ADAUSDC', 'XRPUSDC', 'TRXUSDC']
    comision, stop_loss = 0.001, -3.0 # Bajamos Stop Loss a -3% por seguridad

    while True:
        try:
            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            pos = c.futures_position_information()
            activas = [p for p in pos if float(p.get('positionAmt', 0)) != 0]

            if len(activas) == 0:
                print(f"📡 BUSCANDO... | SALDO: {disp:.2f}", end='\r')
                for m in monedas:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if (cl[-1] > e9 > e27) or (cl[-1] < e9 < e27):
                        side_in = SIDE_BUY if cl[-1] > e9 else SIDE_SELL
                        # Usamos 90% para cuentas chicas para llegar al mínimo de 5 USDC
                        monto = disp * 0.90 if (disp * palanca) < 5.1 else disp * 0.20
                        cant = round((monto * palanca) / cl[-1], 0 if m in ['DOGEUSDC', 'TRXUSDC'] else 1)
                        
                        if (cant * cl[-1]) >= 5.0:
                            c.futures_change_leverage(symbol=m, leverage=palanca)
                            c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                            
                            # LANZAMOS AL VIGILANTE EN OTRO HILO
                            threading.Thread(target=vigilante_instantaneo, 
                                             args=(c, m, ("LONG" if side_in==SIDE_BUY else "SHORT"), cant, cl[-1], palanca, comision, stop_loss),
                                             daemon=True).start()
                            
                            # Esperamos el descanso de 30s mientras el vigilante trabaja
                            for i in range(30, 0, -1):
                                print(f"⏳ DESCANSO POST-COMPRA: {i}s...", end='\r')
                                time.sleep(1)
                            break
            else:
                # El vigilante ya está trabajando en su propio hilo, aquí solo esperamos
                time.sleep(2)

        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    bot_quantum_flash()
