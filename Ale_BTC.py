import os, time, threading
from binance.client import Client
from binance.enums import *

# Memoria de seguridad
vigilantes_activos = set()

def vigilante_bunker(c, sym, side, q, entry, palanca, comision, stop_loss):
    global vigilantes_activos
    vigilantes_activos.add(sym)
    pico = 0.0
    gatillo_trailing = 1.20 
    margen_pegado = 0.05
    
    print(f"🛡️ RECONECTADO: {sym} | Entrada: {entry}")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            # Cálculo de ROI
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # ESTO ES LO QUE VERÁS EN LOS LOGS
            print(f"🔹 {sym} | ROI: {roi:.2f}% | MAX: {pico:.2f}%")

            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ {sym} CERRADO FINAL | ROI: {roi:.2f}%")
                break 
            
            time.sleep(2) # Pausa para no saturar los logs
        except Exception as e:
            time.sleep(5)
    
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_quantum_v14_railway():
    # Intenta leer de todas las formas posibles las keys de Railway
    api_key = os.getenv("API_KEY") or os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("API_SECRET") or os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ ERROR: No se encuentran las API KEYS en las variables de Railway.")
        return

    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    monedas_radar = ['SOLUSDC', 'PEPEUSDC', 'DOGEUSDC', 'ADAUSDC']
    palanca, stop_loss = 5, -4.0
    max_ops = 2 

    print("🚀 BOT INICIADO - BUSCANDO POSICIONES ABIERTAS...")

    while True:
        try:
            # 1. Forzar lectura de posiciones desde Binance
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            # 2. Activar vigilantes para lo que ya esté abierto (DOGE/XRP)
            for r in reales:
                s = r['symbol']
                if s not in vigilantes_activos:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    q, ent = abs(float(r['positionAmt'])), float(r['entryPrice'])
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
                        print(f"\n🎯 DISPARO NUEVO EN {m}")
                        time.sleep(10)
                        break

        except Exception as e:
            print(f"⚠️ Error de conexión: {e}")
            time.sleep(10)
        
        print(f"💰 DISP: {disp:.2f} USDC | ACTIVAS: {len(simbolos_reales)}/2", end='\r')
        time.sleep(5)

if __name__ == "__main__":
    bot_quantum_v14_railway()
