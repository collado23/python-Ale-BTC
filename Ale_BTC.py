import os, time, threading, math
from binance.client import Client
from binance.enums import *

# Memoria de operaciones y bloqueo temporal 
ops_activas = {} 
bloqueo_enfriamiento = {} 

def vigilante_blindado(c, sym, side, q, entry, palanca, comision, stop_loss):
    global ops_activas, bloqueo_enfriamiento
    objetivo_profit = 1.20 # CIERRE FIJO EN 1.2%

    print(f"🎯 VIGILANTE CONFIGURADO A CIERRE FIJO 1.2% EN: {sym}")

    while sym in ops_activas:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            # ROI Real
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca * 100) - (comision * 100)
            
            # LÓGICA DE CIERRE DIRECTO
            if (roi >= objetivo_profit) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                
                estado = "PROFIT 🎯" if roi >= objetivo_profit else "STOP LOSS 🛑"
                print(f"\n✅ CIERRE EJECUTADO ({estado}): {sym} | ROI: {roi:.2f}%")
                
                if sym in ops_activas: del ops_activas[sym]
                bloqueo_enfriamiento[sym] = time.time()
                break 
            
            if sym in ops_activas:
                ops_activas[sym].update({"roi": roi})
            
            time.sleep(0.1) # Máxima frecuencia de monitoreo
        except:
            time.sleep(0.5)

def bot_quantum_v13_final():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    monedas = ['SOLUSDC', 'PEPEUSDC', 'DOGEUSDC', 'ADAUSDC']
    palanca, stop_loss = 5, -4.0 # x5 palanca como acordamos
    max_ops = 2 

    print(f"🚀 V13 TOTAL BLOCK | OBJETIVO FIJO 1.2% | CAPITAL PROTEGIDO")

    while True:
        try:
            # 1. ENGANCHE DE POSICIONES
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            for s in list(ops_activas.keys()):
                if s not in simbolos_reales: del ops_activas[s]

            for r in reales:
                s = r['symbol']
                if s not in ops_activas:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    ops_activas[s] = {"roi": 0}
                    threading.Thread(target=vigilante_blindado, args=(c, s, side_in, abs(float(r['positionAmt'])), float(r['entryPrice']), palanca, 0.001, stop_loss), daemon=True).start()

            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            print(f"\n💰 DISP: {disp:.2f} | ACTIVAS: {len(reales)}/2")

            # 2. RADAR DE ENTRADA CON TRIPLE FILTRO (PIQUITO)
            if len(reales) < max_ops and disp > 4.50:
                for m in monedas:
                    if m in simbolos_reales: continue
                    if m in bloqueo_enfriamiento and (time.time() - bloqueo_enfriamiento[m] < 300): continue

                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27

                    # Tendencia confirmada por precio y medias
                    es_long = (cl[-1] > e9) and (e9 > e27) and (e27 > e27_ant)
                    es_short = (cl[-1] < e9) and (e9 < e27) and (e27 < e27_ant)

                    if es_long or es_short:
                        side_order = SIDE_BUY if es_long else SIDE_SELL
                        monto_fijo = 4.10 # Para que siempre entren las 2 con tus 9.74
                        decs = 0 if 'PEPE' in m or 'DOGE' in m else 2
                        cant = math.floor((monto_fijo * palanca / cl[-1]) * (10**decs)) / (10**decs)
                        
                        if cant > 0:
                            c.futures_change_leverage(symbol=m, leverage=palanca)
                            c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"🎯 DISPARO EN {m} | BUSCANDO 1.2%")
                            time.sleep(5); break
        except Exception as e:
            time.sleep(5)
        time.sleep(8)

if __name__ == "__main__":
    bot_quantum_v13_final()
