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
    margen_pegado = 0.15 # Tu ajuste de 0.15%
    print(f"⚡ [VIGILANTE] {sym} ACTIVO | ROI Objetivo: 1.2% | Trail: 0.15%")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - 0.1) * 100 
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= 1.2 else -99.0

            # CIERRE FLASH
            if (pico >= 1.2 and roi <= piso) or (roi <= -4.0):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"🔥 CIERRE EJECUTADO EN {sym} | ROI FINAL: {roi:.2f}%")
                ultimo_cierre_tiempo = time.time()
                break

            # Verificación de cierre manual
            if int(time.time()) % 5 == 0:
                pos = c.futures_position_information(symbol=sym)
                if not any(float(p.get('positionAmt', 0)) != 0 for p in pos): break

            time.sleep(1.0) # REVISIÓN CADA 1 SEGUNDO
        except: time.sleep(2)
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_quantum_v16_7():
    global contador_ops
    print("🚀 V16.7 | VERSIÓN DIRECTA | SIN FILTROS DE ESPERA")

    while True:
        try:
            api_key = os.getenv("API_KEY"); api_secret = os.getenv("API_SECRET")
            c = Client(api_key, api_secret)
            c.API_URL = 'https://fapi.binance.com/fapi/v1'

            # 1. ESCANEO INMEDIATO DE POSICIONES
            pos_info = c.futures_position_information()
            reales = [p for p in pos_info if float(p.get('positionAmt', 0)) != 0]
            
            for r in reales:
                if r['symbol'] not in vigilantes_activos:
                    threading.Thread(target=vigilante_bunker, args=(c, r['symbol'], "LONG" if float(r['positionAmt']) > 0 else "SHORT", abs(float(r['positionAmt'])), float(r['entryPrice']), 5), daemon=True).start()

            # 2. BUSCADOR ULTRA-RÁPIDO (Sin candado de 60s)
            if len(reales) == 0:
                for m in ['SOLUSDC', '1000PEPEUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=15)
                    cl = [float(x[4]) for x in k]
                    e9 = sum(cl[-9:])/9
                    e15 = sum(cl[-15:])/15
                    
                    side = None
                    # ENTRADA DIRECTA POR CRUCE SIMPLE
                    if cl[-1] > e9 > e15: side = SIDE_BUY
                    elif cl[-1] < e9 < e15: side = SIDE_SELL
                    
                    if side:
                        monto_fijo = 8.0 # Con 8 USD siempre pasamos el mínimo de 5 de Binance
                        cant = round((monto_fijo * 5) / cl[-1], 0 if 'PEPE' in m else 2)
                        
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side=side, type=ORDER_TYPE_MARKET, quantity=cant)
                        contador_ops += 1
                        print(f"🎯 ¡DISPARO DIRECTO EN {m}! OPERACIÓN #{contador_ops}")
                        time.sleep(5); break # Pausa mínima para no repetir orden

            print(f"💰 OPS HOY: {contador_ops} | ACTIVAS: {len(reales)} | BUSCANDO...")

        except Exception as e: time.sleep(5)
        time.sleep(5) # ESCANEO DE MERCADO CADA 5 SEGUNDOS

if __name__ == "__main__":
    bot_quantum_v16_7()
