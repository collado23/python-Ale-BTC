import os, time, threading
from binance.client import Client
from binance.enums import *

# === VARIABLES DE CONTROL ===
vigilantes_vivos = set()
ultimo_cierre = 0

def vigilante_ayer(c, sym, side, q, entry, palanca):
    global vigilantes_vivos, ultimo_cierre
    if sym in vigilantes_vivos: return
    vigilantes_vivos.add(sym)
    
    pico = 0.0
    margen_pegado = 0.15 # Tu ajuste de ayer
    print(f"🛡️ [VIGILANTE] {sym} RECUPERADO / ACTIVO")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            # ROI de ayer (descontando 0.1% de comisión de Binance)
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - 0.1) * 100 
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= 1.2 else -99.0

            # ESTO ES LO QUE NO PUEDE FALTAR (Visualización de ayer)
            print(f"📊 {sym} | ROI: {roi:.2f}% | MAX: {pico:.2f}% | PISO: {piso:.2f}%")

            # Lógica de salida
            if (pico >= 1.2 and roi <= piso) or (roi <= -4.0):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"🔥 CIERRE EJECUTADO EN {sym} | ROI: {roi:.2f}%")
                ultimo_cierre = time.time()
                break

            # Si la moneda desaparece (cierre manual), matamos el hilo
            if int(time.time()) % 10 == 0:
                p = c.futures_position_information(symbol=sym)
                if not any(float(x.get('positionAmt', 0)) != 0 for x in p): break

            time.sleep(1.5) 
        except:
            time.sleep(5)
    
    if sym in vigilantes_vivos: vigilantes_vivos.remove(sym)

def bot_quantum_ayer_real():
    print("🚀 BOT QUANTUM INICIADO | ESTILO AYER | MODO BLINDADO")
    while True:
        try:
            api_key = os.getenv("API_KEY"); api_secret = os.getenv("API_SECRET")
            c = Client(api_key, api_secret)
            c.API_URL = 'https://fapi.binance.com/fapi/v1'

            # 1. ESTADO DE CUENTA
            acc = c.futures_account()
            total_w = next((float(b['walletBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            disp = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            
            pos_info = c.futures_position_information()
            reales = [p for p in pos_info if float(p.get('positionAmt', 0)) != 0]

            print(f"💰 WALLET: {total_w:.2f} | ACTIVAS: {len(reales)}/1 | BUSCANDO...")

            # 2. AUTO-ADOPCIÓN (Si Railway reinicia, esto engancha la moneda al toque)
            for r in reales:
                if r['symbol'] not in vigilantes_vivos:
                    threading.Thread(target=vigilante_ayer, args=(
                        c, r['symbol'], 
                        "LONG" if float(r['positionAmt']) > 0 else "SHORT", 
                        abs(float(r['positionAmt'])), 
                        float(r['entryPrice']), 5
                    ), daemon=True).start()

            # 3. BUSCADOR (75% del capital para no fallar por margen bajo)
            if len(reales) == 0 and (time.time() - ultimo_cierre > 30):
                for m in ['SOLUSDC', '1000PEPEUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=20)
                    cl = [float(x[4]) for x in k]
                    e9, e15 = sum(cl[-9:])/9, sum(cl[-15:])/15
                    
                    side = None
                    if cl[-1] > e9 > e15: side = SIDE_BUY
                    elif cl[-1] < e9 < e15: side = SIDE_SELL
                    
                    if side:
                        monto = total_w * 0.75
                        cant = round((monto * 5) / cl[-1], 0 if 'PEPE' in m else 2)
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side=side, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"🎯 DISPARO EN {m}")
                        break

        except Exception as e:
            time.sleep(10)
        time.sleep(15)

if __name__ == "__main__":
    bot_quantum_ayer_real()
