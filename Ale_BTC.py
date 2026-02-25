import os, time, threading
from binance.client import Client
from binance.enums import *

# === VARIABLES GLOBALES ===
vigilantes_activos = set()
ultimo_cierre_tiempo = 0
contador_ops = 0  # <--- Este es tu contador

def vigilante_bunker(c, sym, side, q, entry, palanca, comision):
    global vigilantes_activos, ultimo_cierre_tiempo
    vigilantes_activos.add(sym)
    
    stop_loss = -4.0        
    gatillo_trailing = 1.2  
    margen_pegado = 0.15    
    
    pico = 0.0
    print(f"⚡ [VIGILANTE] {sym} ACTIVO | Trail: 1.2% | Retroceso: 0.15%")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # CIERRE FLASH
            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"🔥 CIERRE EJECUTADO EN {sym} | ROI: {roi:.2f}%")
                ultimo_cierre_tiempo = time.time()
                break

            # Auto-limpieza si la cierras manual
            if int(time.time()) % 10 == 0:
                pos = c.futures_position_information(symbol=sym)
                if not any(float(p.get('positionAmt', 0)) != 0 for p in pos):
                    break

            time.sleep(1.5) 
        except:
            time.sleep(5)
    
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_quantum_v16_2():
    global contador_ops
    print("🚀 V16.2 INICIADA | SISTEMA DE CONTEO ACTIVO")

    while True:
        try:
            api_key = os.getenv("API_KEY")
            api_secret = os.getenv("API_SECRET")
            if not api_key: time.sleep(10); continue

            c = Client(api_key, api_secret)
            c.API_URL = 'https://fapi.binance.com/fapi/v1'

            acc = c.futures_account()
            total_w = next((float(b['walletBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            disp = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)

            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            for r in reales:
                if r['symbol'] not in vigilantes_activos:
                    threading.Thread(target=vigilante_bunker, args=(c, r['symbol'], "LONG" if float(r['positionAmt']) > 0 else "SHORT", abs(float(r['positionAmt'])), float(r['entryPrice']), 5, 0.001), daemon=True).start()

            # BUSCADOR DE TENDENCIA
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
                        # 65% del capital para superar los 5 USD mínimos
                        monto_in = total_w * 0.65
                        decs = 0 if 'PEPE' in m else 2
                        cant = round((monto_in * 5) / cl[-1], decs)
                        
                        if disp >= monto_in and (cant * cl[-1]) >= 5.1:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                            contador_ops += 1 # <--- Suma al contador
                            print(f"🎯 OPERACIÓN #{contador_ops} ABIERTA EN {m}")
                            time.sleep(5); break

            # Resumen en consola con el contador visible
            print(f"💰 WALLET: {total_w:.2f} | DISP: {disp:.2f} | OPS HOY: {contador_ops} | ACTIVAS: {len(simbolos_reales)}/1")

        except Exception as e:
            time.sleep(20)
        time.sleep(20)

if __name__ == "__main__":
    bot_quantum_v16_2()
