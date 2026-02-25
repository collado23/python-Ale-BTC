import os, time, threading, math
from binance.client import Client 
from binance.enums import *

# Memoria de operaciones y bloqueo temporal
ops_activas = {} 
bloqueo_enfriamiento = {} 

def vigilante_blindado(c, sym, side, q, entry, palanca, comision, stop_loss):
    global ops_activas, bloqueo_enfriamiento
    pico = 0.0
    gatillo_trailing = 1.20 
    margen_pegado = 0.15 

    while sym in ops_activas:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca * 100) - (comision * 100)
            
            if roi > pico: pico = roi
            
            # CIERRE (TRAILING O STOP LOSS)
            if (pico >= gatillo_trailing and roi <= (pico - margen_pegado)) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ CIERRE: {sym} | ROI FINAL: {roi:.2f}%")
                bloqueo_enfriamiento[sym] = time.time()
                if sym in ops_activas: del ops_activas[sym]
                break 
            
            ops_activas[sym].update({"roi": roi, "pico": pico})
            time.sleep(1)
        except:
            time.sleep(2)

def bot_quantum_v13_final():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    monedas = ['SOLUSDC', 'PEPEUSDC', 'DOGEUSDC', 'ADAUSDC']
    palanca, stop_loss = 5, -4.0
    max_ops = 2 

    print(f"🚀 V13 TOTAL BLOCK | RADAR DE INCLINACIÓN ACTIVADO")

    while True:
        try:
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            # Limpiar memoria interna
            for s in list(ops_activas.keys()):
                if s not in simbolos_reales: del ops_activas[s]

            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            print(f"\n💰 DISP: {disp:.2f} | ACTIVAS: {len(reales)}/2")
            
            # ENGANCHE DE ABIERTAS
            for r in reales:
                s = r['symbol']
                if s not in ops_activas:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    ops_activas[s] = {"roi": 0, "pico": 0}
                    threading.Thread(target=vigilante_blindado, args=(c, s, side_in, abs(float(r['positionAmt'])), float(r['entryPrice']), palanca, 0.001, stop_loss), daemon=True).start()
                    print(f"🔎 ENGANCHADO: {s}")

            # RADAR DE SEÑAL Y TENDENCIA
            if len(reales) < max_ops:
                for m in monedas:
                    if m in simbolos_reales: continue
                    if m in bloqueo_enfriamiento and (time.time() - bloqueo_enfriamiento[m] < 300): continue

                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    
                    e9 = sum(cl[-9:])/9
                    e27 = sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27 # Hace 2 velas para ver la inclinación real

                    # DETERMINAR EL "PIQUITO" (Inclinación)
                    if e27 > e27_ant:
                        piquito = "⤴️ PIQUITO ARRIBA (SUBIENDO)"
                    elif e27 < e27_ant:
                        piquito = "⤵️ PIQUITO ABAJO (BAJANDO)"
                    else:
                        piquito = "↔️ PLANO"

                    print(f"📊 {m} | {piquito} | E9: {e9:.4f} E27: {e27:.4f}")

                    # LÓGICA DE ENTRADA CON CONFIRMACIÓN DE PIQUITO
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant):
                        side_order = SIDE_BUY
                        motivo = "LONG CONFIRMADO"
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant):
                        side_order = SIDE_SELL
                        motivo = "SHORT CONFIRMADO"
                    else:
                        continue

                    # MONTO FIJO PARA 2 OPS
                    monto_fijo = 4.20 
                    if disp >= monto_fijo:
                        decs = 0 if 'PEPE' in m or 'DOGE' in m else 2
                        cant = math.floor((monto_fijo * palanca / cl[-1]) * (10**decs)) / (10**decs)
                        
                        if cant > 0:
                            c.futures_change_leverage(symbol=m, leverage=palanca)
                            c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"🎯 {motivo} EN {m} | {monto_fijo} USDC")
                            time.sleep(5); break
        except Exception as e:
            time.sleep(5)
        time.sleep(10)

if __name__ == "__main__":
    bot_quantum_v13_final()
