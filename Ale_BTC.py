import os, time, threading
from binance.client import Client 
from binance.enums import *

# === VARIABLES GLOBALES ===
vigilantes_activos = set()
ultimo_cierre_tiempo = 0
contador_ops = 0 

def vigilante_bunker(c, sym, side, q, entry, palanca, comision):
    global vigilantes_activos, ultimo_cierre_tiempo
    vigilantes_activos.add(sym)
    
    # TUS AJUSTES
    stop_loss = -4.0        
    gatillo_trailing = 1.2  
    margen_pegado = 0.15    # Retroceso ultra-corto
    
    pico = 0.0
    print(f"🛡️ [ADOPTADA] {sym} bajo vigilancia | Trail: 1.2% | Retroceso: 0.15%")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # CIERRE FLASH SI TOCA EL PISO
            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"🔥 CIERRE EJECUTADO EN {sym} | ROI: {roi:.2f}%")
                ultimo_cierre_tiempo = time.time()
                break

            # Si la cerrás vos en la app, el vigilante se apaga solo
            if int(time.time()) % 10 == 0:
                pos = c.futures_position_information(symbol=sym)
                if not any(float(p.get('positionAmt', 0)) != 0 for p in pos):
                    print(f"🧹 {sym} ya no está en Binance. Vigilante cerrado.")
                    break

            time.sleep(1.5) 
        except:
            time.sleep(5)
    
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_quantum_v16_3():
    global contador_ops
    print("🚀 V16.3 | MODO ADOPCIÓN Y DESBLOQUEO (80% CAP)")

    while True:
        try:
            api_key = os.getenv("API_KEY")
            api_secret = os.getenv("API_SECRET")
            c = Client(api_key, api_secret)
            c.API_URL = 'https://fapi.binance.com/fapi/v1'

            acc = c.futures_account()
            total_w = next((float(b['walletBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            disp = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)

            # 1. DETECTAR MONEDAS YA ABIERTAS (PARA PONERLES LA PATA)
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            for r in reales:
                sym = r['symbol']
                if sym not in vigilantes_activos:
                    # El bot "adopta" la moneda y le pone el vigilante
                    threading.Thread(target=vigilante_bunker, args=(
                        c, sym, 
                        "LONG" if float(r['positionAmt']) > 0 else "SHORT", 
                        abs(float(r['positionAmt'])), 
                        float(r['entryPrice']), 
                        5, 0.001
                    ), daemon=True).start()

            # 2. BUSCADOR (Solo si el disponible es suficiente y no hay nada abierto)
            if len(simbolos_reales) == 0 and (time.time() - ultimo_cierre_tiempo > 60):
                for m in ['SOLUSDC', '1000PEPEUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    side_order = None
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant): side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant): side_order = SIDE_SELL
                    
                    if side_order:
                        # Usar el 80% para que supere los 5 USD mínimos de Binance
                        monto_in = total_w * 0.80
                        cant = round((monto_in * 5) / cl[-1], 0 if 'PEPE' in m else 2)
                        
                        if disp >= (monto_in * 0.9):
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                            contador_ops += 1
                            print(f"🎯 NUEVA OPERACIÓN #{contador_ops} EN {m}")
                            break

            print(f"💰 WALLET: {total_w:.2f} | DISP: {disp:.2f} | OPS: {contador_ops} | ACTIVAS: {len(simbolos_reales)}")

        except Exception as e:
            time.sleep(15)
        time.sleep(15)

if __name__ == "__main__":
    bot_quantum_v16_3()
