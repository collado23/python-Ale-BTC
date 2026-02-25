import os, time, threading
from binance.client import Client
from binance.enums import *

# Memoria de protección contra bucles 
vigilantes_vivos = set()

def vigilante_bunker(c, sym, side, q, entry, palanca, comision, stop_loss):
    global vigilantes_vivos
    vigilantes_vivos.add(sym)
    pico = 0.0
    gatillo_trailing = 1.20 
    margen_pegado = 0.05

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['mark_price'] if 'mark_price' in res else res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # ÚNICOS GATILLOS DE CIERRE: META O STOP LOSS
            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ {sym} CERRADO | ROI: {roi:.2f}%")
                break 
            
            time.sleep(0.5)
        except:
            time.sleep(1)
    
    if sym in vigilantes_vivos: vigilantes_vivos.remove(sym)

def bot_quantum_v14_bunker():
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    # Monedas rápidas como pediste
    monedas = ['SOLUSDC', 'PEPEUSDC', 'DOGEUSDC', 'ADAUSDC']
    palanca, stop_loss = 5, -4.0
    max_ops = 2 

    print("🚀 V14 BUNKER | PROTECCIÓN CONTRA BUCLES | DOBLE OP")

    while True:
        try:
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            # Limpiar vigilantes que ya no tienen posición real
            for s in list(vigilantes_vivos):
                if s not in simbolos_reales: vigilantes_vivos.remove(s)

            # Lanzar vigilantes si falta alguno
            for r in reales:
                s = r['symbol']
                if s not in vigilantes_vivos:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    threading.Thread(target=vigilante_bunker, args=(c, s, side_in, abs(float(r['positionAmt'])), float(r['entryPrice']), palanca, 0.001, stop_loss), daemon=True).start()

            # Lógica de Radar: SOLO ABRE
            if len(reales) < max_ops:
                for m in monedas:
                    if m in simbolos_reales: continue
                    
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
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
                        print(f"🎯 DISPARO EN {m}")
                        time.sleep(10) # Pausa de seguridad para que Binance procese
                        break

        except Exception as e:
            time.sleep(2)
        time.sleep(2)

if __name__ == "__main__":
    bot_quantum_v14_bunker()
