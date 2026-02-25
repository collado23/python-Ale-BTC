import os, time, threading
from binance.client import Client
from binance.enums import *

# Memoria de seguridad para que no se dupliquen procesos
vigilantes_activos = set()

def vigilante_bunker(c, sym, side, q, entry, palanca, comision, stop_loss):
    global vigilantes_activos
    vigilantes_activos.add(sym)
    pico = 0.0
    gatillo_trailing = 1.20 
    margen_pegado = 0.05
    
    print(f"🛡️ VIGILANTE RECONECTADO: {sym} | Entrada: {entry}")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            # ROI calculado con el precio de entrada real de Binance
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # Dashboard en tiempo real en los logs
            print(f"🔹 {sym} | ROI: {roi:.2f}% | MAX: {pico:.2f}% | PISO: {piso:.2f}%")

            # GATILLOS DE CIERRE
            meta_alcanzada = (pico >= gatillo_trailing and roi <= piso)
            stop_loss_tocado = (roi <= stop_loss)

            if meta_alcanzada or stop_loss_tocado:
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ {sym} CERRADO | ROI FINAL: {roi:.2f}%")
                break 
            
            time.sleep(1) # Un poco de calma para no saturar
        except Exception as e:
            time.sleep(2)
    
    if sym in vigilantes_activos:
        vigilantes_activos.remove(sym)

def bot_quantum_v14_recuperacion():
    # Usar las variables de entorno de Railway
    api_key = os.getenv("API_KEY") or os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("API_SECRET") or os.getenv("BINANCE_API_SECRET")
    
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    # Lista de radar con SOL y PEPE incluidas
    monedas_radar = ['SOLUSDC', 'PEPEUSDC', 'DOGEUSDC', 'ADAUSDC']
    palanca, stop_loss = 5, -4.0
    max_ops = 2 

    print("🚀 MODO RECUPERACIÓN: Sincronizando con Binance...")

    while True:
        try:
            # 1. Consultar posiciones actuales en la billetera
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            # 2. Reconectar el Vigilante a las monedas que ya están abiertas
            for r in reales:
                s = r['symbol']
                if s not in vigilantes_activos:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    q, ent = abs(float(r['positionAmt'])), float(r['entryPrice'])
                    # Lanzamos el proceso para que aparezca el ROI
                    threading.Thread(target=vigilante_bunker, args=(c, s, side_in, q, ent, palanca, 0.001, stop_loss), daemon=True).start()

            # 3. Datos de cuenta para el Radar
            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            # 4. Radar: Solo busca si hay hueco libre
            if len(simbolos_reales) < max_ops:
                print(f"📡 RADAR BUSCANDO... (Espacios libres: {max_ops - len(simbolos_reales)})", end='\r')
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
                        print(f"\n🎯 DISPARO EN {m} | Capital: {monto:.2f} USDC")
                        time.sleep(10) # Pausa bunker
                        break

        except Exception as e:
            time.sleep(5)
        time.sleep(5)

if __name__ == "__main__":
    bot_quantum_v14_recuperacion()
