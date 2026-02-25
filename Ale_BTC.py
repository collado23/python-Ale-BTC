import os, time, threading
from binance.client import Client
from binance.enums import *

# Diccionario de protección
vigilantes_activos = set()

def vigilante_bunker(c, sym, side, q, entry, palanca, comision, stop_loss):
    global vigilantes_activos
    vigilantes_activos.add(sym)
    pico = 0.0
    gatillo_trailing = 1.20 
    margen_pegado = 0.05
    
    # El ROI inicial se calcula apenas arranca para no empezar en 0
    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # Dashboard en consola
            print(f"🔹 {sym} | ROI: {roi:.2f}% | MAX: {pico:.2f}%", end='\r')

            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ {sym} CERRADO FINAL | ROI: {roi:.2f}%")
                break 
            
            time.sleep(0.5) 
        except:
            time.sleep(1)
    
    if sym in vigilantes_activos:
        vigilantes_activos.remove(sym)

def bot_quantum_v14_recuperacion():
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    monedas_radar = ['SOLUSDC', 'PEPEUSDC', 'DOGEUSDC', 'ADAUSDC']
    palanca, stop_loss = 5, -4.0
    max_ops = 2 

    print("🚀 V14 BUNKER | RECUPERANDO OPERACIONES ABIERTAS...")

    while True:
        try:
            # 1. Mirar qué hay abierto REALMENTE en Binance
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            # 2. Sincronizar Vigilantes (esto hará que aparezca el ROI de lo que ya tenías)
            for r in reales:
                s = r['symbol']
                if s not in vigilantes_activos:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    q, ent = abs(float(r['positionAmt'])), float(r['entryPrice'])
                    # Lanzamos el vigilante para la moneda que ya estaba abierta
                    threading.Thread(target=vigilante_bunker, args=(c, s, side_in, q, ent, palanca, 0.001, stop_loss), daemon=True).start()

            # 3. Datos de cuenta
            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            # 4. Radar (Solo si hay lugar)
            if len(simbolos_reales) < max_ops:
                for m in monedas_radar:
                    if m in simbolos_reales: continue
                    
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant): side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant): side_order = SIDE_SELL
                    else: continue

                    monto = disp * 0.45 
                    decs = 0 if m in ['PEPEUSDC', 'DOGEUSDC'] else 1
                    cant = round((monto * palanca) / cl[-1], decs)
                    
                    if (cant * cl[-1]) >= 5.1:
                        c.futures_change_leverage(symbol=m, leverage=palanca)
                        c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"\n🎯 NUEVA ENTRADA EN {m}")
                        time.sleep(10)
                        break

        except Exception as e:
            print(f"\n⚠️ Reintentando... {e}")
            time.sleep(5)
        time.sleep(5)

if __name__ == "__main__":
    bot_quantum_v14_recuperacion()
