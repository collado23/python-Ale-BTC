import os, time, threading
from binance.client import Client 
from binance.enums import *

# Diccionario de protección para que no se crucen los cables
vigilantes_activos = set()

def vigilante_bunker(c, sym, side, q, entry, palanca, comision, stop_loss):
    global vigilantes_activos
    vigilantes_activos.add(sym)
    pico = 0.0
    gatillo_trailing = 1.20 
    margen_pegado = 0.05

    print(f"🛡️ [BUNKER] Protegiendo {sym} | Entrada: {entry}")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            # Cálculo de ROI Real
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # ÚNICOS GATILLOS DE CIERRE: 1.20% (Trailing) o -4.0% (SL)
            meta_alcanzada = (pico >= gatillo_trailing and roi <= piso)
            stop_loss_tocado = (roi <= stop_loss)

            if meta_alcanzada or stop_loss_tocado:
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ {sym} CERRADO | ROI: {roi:.2f}% | MOTIVO: {'META' if meta_alcanzada else 'STOP LOSS'}")
                break 
            
            time.sleep(0.4) 
        except Exception as e:
            time.sleep(1)
    
    if sym in vigilantes_activos:
        vigilantes_activos.remove(sym)

def bot_quantum_v14_bunker():
    api_key = os.getenv("API_KEY") or os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("API_SECRET") or os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    # Monedas rápidas y baratas como pediste
    monedas = ['SOLUSDC', 'PEPEUSDC', 'DOGEUSDC', 'ADAUSDC']
    palanca, stop_loss = 5, -4.0
    max_ops = 2 

    print("🚀 V14 BUNKER ACTIVADA | CERO CIERRES PREMATUROS | DOBLE OP")

    while True:
        try:
            # 1. Ver qué hay abierto REALMENTE en Binance
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            # 2. Sincronizar Vigilantes (si cerraste algo a mano, se limpia aquí)
            for s in list(vigilantes_activos):
                if s not in simbolos_reales:
                    vigilantes_activos.remove(s)

            # 3. Lanzar Vigilante si hay una posición huérfana
            for r in reales:
                s = r['symbol']
                if s not in vigilantes_activos:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    q, ent = abs(float(r['positionAmt'])), float(r['entryPrice'])
                    threading.Thread(target=vigilante_bunker, args=(c, s, side_in, q, ent, palanca, 0.001, stop_loss), daemon=True).start()

            # 4. Dashboard simplificado
            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            print(f"💰 DISP: {disp:.2f} USDC | ACTIVAS: {len(simbolos_reales)}/{max_ops}", end='\r')

            # 5. Radar de Apertura (SOLO ABRE, NO TIENE PERMISO DE CIERRE)
            if len(simbolos_reales) < max_ops:
                for m in monedas:
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
                        print(f"\n🎯 DISPARO EN {m} | ESPERANDO CONFIRMACIÓN...")
                        time.sleep(10) # Pausa bunker: evita el bucle de apertura múltiple
                        break

        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            time.sleep(5)
        time.sleep(2)

if __name__ == "__main__":
    bot_quantum_v14_bunker()
