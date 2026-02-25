import os, time, threading
from binance.client import Client
from binance.enums import *

# === VARIABLES DE CONTROL ===
vigilantes_activos = set()
ultimo_cierre_tiempo = 0

def vigilante_real(c, sym, side, q, entry, palanca):
    global vigilantes_activos, ultimo_cierre_tiempo
    if sym in vigilantes_activos: return
    vigilantes_activos.add(sym)
    
    pico = 0.0
    margen_pegado = 0.15 
    print(f"🛡️ [OK] Vigilando {sym}")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            # ROI Real (Cálculo directo de ayer)
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - 0.1) * 100 
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= 1.2 else -99.0

            # ESTO ES LO QUE TIENE QUE APARECER SI O SI:
            print(f"📊 {sym} | ROI: {roi:.2f}% | MAX: {pico:.2f}% | PISO: {piso:.2f}%")

            # Cierre (Gatillo 1.2% o Stop Loss -4%)
            if (pico >= 1.2 and roi <= piso) or (roi <= -4.0):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"✅ CIERRE EJECUTADO | ROI: {roi:.2f}%")
                ultimo_cierre_tiempo = time.time()
                break

            time.sleep(1.5) 
        except:
            time.sleep(5)
    
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_estilo_ayer():
    print("🚀 BOT QUANTUM | CARGANDO VERSIÓN ESTABLE...")
    while True:
        try:
            api_key = os.getenv("API_KEY"); api_secret = os.getenv("API_SECRET")
            c = Client(api_key, api_secret)
            c.API_URL = 'https://fapi.binance.com/fapi/v1'

            acc = c.futures_account()
            total_w = next((float(b['walletBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            
            pos_info = c.futures_position_information()
            reales = [p for p in pos_info if float(p.get('positionAmt', 0)) != 0]

            # REPORTE EN PANTALLA
            print(f"💰 BALANCE: {total_w:.2f} | ACTIVAS: {len(reales)}/1")

            # RE-ENGANCHE (Si se reinicia, busca la moneda al toque)
            for r in reales:
                if r['symbol'] not in vigilantes_activos:
                    threading.Thread(target=vigilante_real, args=(
                        c, r['symbol'], 
                        "LONG" if float(r['positionAmt']) > 0 else "SHORT", 
                        abs(float(r['positionAmt'])), 
                        float(r['entryPrice']), 5
                    ), daemon=True).start()

            # BUSCADOR (75% del capital para no fallar por mínimo de Binance)
            if len(reales) == 0 and (time.time() - ultimo_cierre_tiempo > 25):
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

        except:
            time.sleep(10)
        time.sleep(15)

if __name__ == "__main__":
    bot_estilo_ayer()
