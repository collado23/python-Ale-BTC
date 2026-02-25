import os, time, threading
from binance.client import Client 
from binance.enums import *

# Diccionario para evitar lanzar múltiples vigilantes sobre la misma moneda
vigilantes_vivos = set()

def vigilante_bunker(c, sym, side, q, entry, palanca, comision, stop_loss):
    global vigilantes_vivos
    vigilantes_vivos.add(sym)
    pico = 0.0
    gatillo_trailing = 1.20 
    margen_pegado = 0.05

    print(f"🛡️ VIGILANTE INICIADO: {sym} | ENTRADA: {entry}")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # ÚNICOS GATILLOS DE CIERRE: META O STOP LOSS
            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ CIERRE ESTRATÉGICO EN {sym} | ROI final: {roi:.2f}%")
                break 
            
            time.sleep(0.5) # Un poco más lento para no saturar la API
        except Exception as e:
            print(f"⚠️ Error en vigilante {sym}: {e}")
            time.sleep(2)
    
    vigilantes_vivos.remove(sym)

def bot_quantum_v14_bunker():
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("API_SECRET")
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    monedas = ['SOLUSDC', 'PEPEUSDC', 'DOGEUSDC', 'ADAUSDC']
    palanca, stop_loss = 5, -4.0
    max_ops = 2 

    print("🚀 ALE IA QUANTUM V14 - MODO BUNKER ACTIVO")

    while True:
        try:
            # 1. Consultar posiciones reales en Binance
            pos = c.futures_position_information()
            activas_reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [p['symbol'] for p in activas_reales]

            # 2. Lanzar vigilantes si hay posiciones pero no tienen hilo activo
            for p in activas_reales:
                s = p['symbol']
                if s not in vigilantes_vivos:
                    side_in = "LONG" if float(p['positionAmt']) > 0 else "SHORT"
                    q, ent = abs(float(p['positionAmt'])), float(p['entryPrice'])
                    threading.Thread(target=vigilante_bunker, args=(c, s, side_in, q, ent, palanca, 0.001, stop_loss), daemon=True).start()

            # 3. Radar de búsqueda (Solo si hay lugar)
            if len(simbolos_reales) < max_ops:
                for m in monedas:
                    if m in simbolos_reales: continue
                    
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    # DISPARO
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant): side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant): side_order = SIDE_SELL
                    else: continue

                    acc = c.futures_account()
                    disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
                    
                    monto = disp * 0.45 
                    decs = 0 if m in ['PEPEUSDC', 'DOGEUSDC'] else 1
                    cant = round((monto * palanca) / cl[-1], decs)
                    
                    if (cant * cl[-1]) >= 5.1:
                        c.futures_change_leverage(symbol=m, leverage=palanca)
                        c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"🎯 DISPARO EN {m} | Capital usado: {monto:.2f} USDC")
                        time.sleep(10) # Espera larga para que Binance registre la orden antes de volver a escanear
                        break

        except Exception as e:
            print(f"⚠️ Error Principal: {e}")
            time.sleep(5)
        
        print(f"📡 Radar: {len(simbolos_reales)}/{max_ops} posiciones | Disp: {disp:.2f} USDC", end='\r')
        time.sleep(3)

if __name__ == "__main__":
    bot_quantum_v14_bunker()
