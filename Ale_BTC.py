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
    margen_pegado = 0.15 
    print(f"🛡️ [VIGILANTE] {sym} ENGANCHADO")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            # ROI con descuento de comisión (0.1% Binance)
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - 0.1) * 100 
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= 1.2 else -99.0

            # ESTE ES EL MENSAJE DE AYER
            print(f"📊 {sym} | ROI: {roi:.2f}% | MAX: {pico:.2f}% | PISO: {piso:.2f}%")

            # Lógica de Cierre
            if (pico >= 1.2 and roi <= piso) or (roi <= -4.0):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"🔥 CIERRE EJECUTADO EN {sym} | ROI FINAL: {roi:.2f}%")
                ultimo_cierre_tiempo = time.time()
                break

            # Limpieza si cierras manual
            if int(time.time()) % 10 == 0:
                pos = c.futures_position_information(symbol=sym)
                if not any(float(p.get('positionAmt', 0)) != 0 for p in pos): break

            time.sleep(2) # Velocidad de ayer
        except: time.sleep(5)
    
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_quantum_ayer_completo():
    global contador_ops
    print("🚀 BOT INICIADO | MODO VISUALIZACIÓN AYER")

    while True:
        try:
            api_key = os.getenv("API_KEY"); api_secret = os.getenv("API_SECRET")
            c = Client(api_key, api_secret)
            c.API_URL = 'https://fapi.binance.com/fapi/v1'

            acc = c.futures_account()
            total_w = next((float(b['walletBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            disp = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)

            pos_info = c.futures_position_information()
            reales = [p for p in pos_info if float(p.get('positionAmt', 0)) != 0]
            
            # EL RESUMEN DE AYER
            print(f"💰 WALLET: {total_w:.2f} | DISP: {disp:.2f} | ACTIVAS: {len(reales)}/1 | OPS: {contador_ops}")

            # Reconectar vigilantes (Maneja reinicios de Railway)
            for r in reales:
                if r['symbol'] not in vigilantes_activos:
                    threading.Thread(target=vigilante_bunker, args=(c, r['symbol'], "LONG" if float(r['positionAmt']) > 0 else "SHORT", abs(float(r['positionAmt'])), float(r['entryPrice']), 5), daemon=True).start()

            # Buscador (70% del capital para asegurar > 5 USD)
            if len(reales) == 0 and (time.time() - ultimo_cierre_tiempo > 30):
                for m in ['SOLUSDC', '1000PEPEUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=20)
                    cl = [float(x[4]) for x in k]
                    e9, e15 = sum(cl[-9:])/9, sum(cl[-15:])/15
                    
                    side = None
                    if cl[-1] > e9 > e15: side = SIDE_BUY
                    elif cl[-1] < e9 < e15: side = SIDE_SELL
                    
                    if side:
                        monto_op = total_w * 0.70
                        cant = round((monto_op * 5) / cl[-1], 0 if 'PEPE' in m else 2)
                        
                        if disp >= monto_op:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side=side, type=ORDER_TYPE_MARKET, quantity=cant)
                            contador_ops += 1
                            print(f"🎯 ENTRADA EN {m}")
                            break

        except Exception as e:
            time.sleep(10)
        time.sleep(15)

if __name__ == "__main__":
    bot_quantum_ayer_completo()
