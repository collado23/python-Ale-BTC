import os, time, threading
from binance.client import Client
from binance.enums import *

# Variables globales blindadas
info_op = {"activo": False, "sym": "", "side": "", "roi": 0.0, "pico": 0.0, "piso": 0.0, "capital": 0.0, "entrada": 0.0}

def vigilante_blindado(c, sym, side, q, entry, palanca, comision, stop_loss):
    global info_op
    info_op["activo"] = True
    info_op["sym"] = sym
    info_op["side"] = "COMPRA (LONG)" if side == "LONG" else "VENTA (SHORT)"
    info_op["entrada"] = entry
    info_op["pico"] = 0.0
    
    # METAS ESTRICTAS
    gatillo_trailing = 1.20 
    margen_pegado = 0.05

    while info_op["activo"]:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > info_op["pico"]:
                info_op["pico"] = roi
            
            info_op["roi"] = roi
            # Solo calcula piso si pasó el 1.20%
            info_op["piso"] = info_op["pico"] - margen_pegado if info_op["pico"] >= gatillo_trailing else -99.0

            # GATILLO DE CIERRE: Solo por Meta o por Stop Loss
            if (info_op["pico"] >= gatillo_trailing and roi <= info_op["piso"]) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ CIERRE EJECUTADO: {roi:.2f}%")
                info_op["activo"] = False
                break 
            
            time.sleep(0.1) 
        except:
            time.sleep(1)

def bot_quantum_v6_blindado():
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("API_SECRET")
    
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca, monedas = 5, ['DOGEUSDC', 'ADAUSDC', 'XRPUSDC', 'TRXUSDC']
    stop_loss = -3.0

    print("🚀 ALE IA QUANTUM - V6 BLINDADA (META 1.20%)")

    while True:
        try:
            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            pos = c.futures_position_information()
            activas = [p for p in pos if float(p.get('positionAmt', 0)) != 0]

            if len(activas) > 0:
                # Si hay operación, SOLO mostramos el Dashboard y dejamos que el vigilante trabaje
                for a in activas:
                    if not info_op["activo"]:
                        sym, q, entry = a['symbol'], abs(float(a['positionAmt'])), float(a['entryPrice'])
                        side_in = "LONG" if float(a['positionAmt']) > 0 else "SHORT"
                        info_op["capital"] = (q * entry) / palanca
                        threading.Thread(target=vigilante_blindado, args=(c, sym, side_in, q, entry, palanca, 0.001, stop_loss), daemon=True).start()
                
                print("\n" + "💎" * 15)
                print(f"💰 DISP: {disp:.2f} USDC | {info_op['side']}")
                print(f"🔥 MONEDA: {info_op['sym']} | ROI: {info_op['roi']:.2f}%")
                print(f"🔝 MAX: {info_op['pico']:.2f}% | PISO: {info_op['piso']:.2f}%")
                print("-" * 30)
                time.sleep(2)

            else:
                # Si no hay operación, limpiamos info y buscamos
                info_op["activo"] = False
                print(f"📡 BUSCANDO SEÑAL... | SALDO: {disp:.2f} USDC", end='\r')
                
                for m in monedas:
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant):
                        side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant):
                        side_order = SIDE_SELL
                    else: continue

                    # Interés compuesto al 90%
                    monto = disp * 0.90
                    decs = 0 if m in ['DOGEUSDC', 'TRXUSDC'] else 1
                    cant = round((monto * palanca) / cl[-1], decs)
                    
                    if (cant * cl[-1]) >= 5.0:
                        c.futures_change_leverage(symbol=m, leverage=palanca)
                        c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"\n🎯 ENTRADA EN {m}!")
                        time.sleep(10)
                        break
        except Exception as e:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot_quantum_v6_blindado()
