import os, time, threading
from binance.client import Client 
from binance.enums import *

# === VARIABLES GLOBALES ===
vigilantes_activos = set()
ultimo_cierre_tiempo = 0
contador_ops = 0 

def vigilante_bunker(c, sym, side, q, entry, palanca):
    global vigilantes_activos, ultimo_cierre_tiempo
    if sym in vigilantes_activos: return
    vigilantes_activos.add(sym)
    
    pico = 0.0
    margen_pegado = 0.15 # Tu ajuste solicitado
    
    print(f"🛡️ [VIGILANTE] {sym} ACTIVO | Retroceso: 0.15%")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            # Cálculo de ROI
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - 0.1) * 100 # 0.1 de comisión Binance
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= 1.2 else -99.0

            # CIERRE FLASH (Gatillo 1.2% - Retroceso 0.15% o Stop Loss -4%)
            if (pico >= 1.2 and roi <= piso) or (roi <= -4.0):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"🔥 CIERRE EJECUTADO EN {sym} | ROI: {roi:.2f}%")
                ultimo_cierre_tiempo = time.time()
                break

            # Verificación de si la moneda sigue existiendo cada 5 segundos
            if int(time.time()) % 5 == 0:
                pos = c.futures_position_information(symbol=sym)
                if not any(float(p.get('positionAmt', 0)) != 0 for p in pos):
                    print(f"🧹 Moneda {sym} cerrada fuera del bot. Limpiando...")
                    break

            time.sleep(1.2) # Velocidad máxima de reacción
        except:
            time.sleep(5)
    
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_quantum_v16_4():
    global contador_ops
    print("🚀 V16.4 | MODO SIN FRENOS | INVERSIÓN FIJA 7.50 USD")

    while True:
        try:
            api_key = os.getenv("API_KEY")
            api_secret = os.getenv("API_SECRET")
            c = Client(api_key, api_secret)
            c.API_URL = 'https://fapi.binance.com/fapi/v1'

            # 1. ESCANEO DE POSICIONES ABIERTAS (Adopta lo que esté en Binance)
            pos_info = c.futures_position_information()
            reales = [p for p in pos_info if float(p.get('positionAmt', 0)) != 0]
            
            for r in reales:
                sym = r['symbol']
                if sym not in vigilantes_activos:
                    threading.Thread(target=vigilante_bunker, args=(
                        c, sym, 
                        "LONG" if float(r['positionAmt']) > 0 else "SHORT", 
                        abs(float(r['positionAmt'])), 
                        float(r['entryPrice']), 5
                    ), daemon=True).start()

            # 2. BUSCADOR DE TENDENCIA (Solo si no hay nada activo)
            if len(reales) == 0 and (time.time() - ultimo_cierre_tiempo > 60):
                for m in ['SOLUSDC', '1000PEPEUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    side_order = None
                    # Condición de tendencia con fuerza
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant): side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant): side_order = SIDE_SELL
                    
                    if side_order:
                        # MONTO FIJO PARA NO FRENARSE (7.50 USD es > 5 USD mínimo)
                        monto_fijo = 7.50
                        cant = round((monto_fijo * 5) / cl[-1], 0 if 'PEPE' in m else 2)
                        
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                        contador_ops += 1
                        print(f"🎯 ¡OPERACIÓN #{contador_ops} LANZADA EN {m}!")
                        break

            # Resumen de estado
            acc = c.futures_account()
            total_w = next((float(b['asset'] == 'USDC' and b['walletBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            print(f"💰 WALLET: {total_w:.2f} | OPS HOY: {contador_ops} | ACTIVAS: {len(reales)}/1")

        except Exception as e:
            time.sleep(10)
        time.sleep(15)

if __name__ == "__main__":
    bot_quantum_v16_4()
