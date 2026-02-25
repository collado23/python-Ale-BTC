import os, time, threading
from binance.client import Client 
from binance.enums import *

ops_activas = {} 

def vigilante_blindado(c, sym, side, q, entry, palanca, comision, stop_loss):
    global ops_activas
    pico = 0.0
    gatillo_trailing = 1.20 
    margen_pegado = 0.15 

    while sym in ops_activas:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            if side == "LONG":
                diff = m_p - entry
            else:
                diff = entry - m_p
            
            roi = ((diff / entry) * palanca * 100) - (comision * 100)
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else stop_loss
            
            ops_activas[sym].update({"roi": roi, "pico": pico, "piso": piso})

            if (pico >= gatillo_trailing and roi <= (pico - margen_pegado)) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ {sym} CERRADO | ROI: {roi:.2f}%")
                if sym in ops_activas: del ops_activas[sym]
                break 
            time.sleep(0.5)
        except:
            time.sleep(1)

def bot_quantum_v13_final():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    monedas = ['SOLUSDC', 'PEPEUSDC', 'DOGEUSDC', 'ADAUSDC']
    palanca, stop_loss = 5, -4.0
    max_ops = 2 

    print(f"🚀 V13 CON RADAR DE TENDENCIA | 2 OPS")

    while True:
        try:
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            for s in list(ops_activas.keys()):
                if s not in simbolos_reales: del ops_activas[s]

            acc = c.futures_account()
            total_w = float(next((b['walletBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            print(f"\n💰 WALLET: {total_w:.2f} | ACTIVAS: {len(reales)}/2")
            
            for r in reales:
                s = r['symbol']
                if s not in ops_activas:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    ops_activas[s] = {"roi": 0, "pico": 0, "piso": -99}
                    threading.Thread(target=vigilante_blindado, args=(c, s, side_in, abs(float(r['positionAmt'])), float(r['entryPrice']), palanca, 0.001, stop_loss), daemon=True).start()
                
                inf = ops_activas.get(s, {})
                print(f"🔹 {s} | ROI: {inf.get('roi',0):.2f}% | MAX: {inf.get('pico',0):.2f}%")

            # RADAR DE TENDENCIA
            if len(reales) < max_ops:
                for m in monedas:
                    if m in simbolos_reales: continue
                    
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    # AQUÍ ESTÁ LO QUE ME PEDÍAS: Visualizar la tendencia
                    if e27 > e27_ant:
                        tendencia = "📈 SUBIENDO"
                    elif e27 < e27_ant:
                        tendencia = "📉 BAJANDO"
                    else:
                        tendencia = "↔️ EN RANGO"
                    
                    print(f"🔍 ESCANEANDO {m}: {tendencia} (EMA27: {e27:.4f})")
                    
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant):
                        side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant):
                        side_order = SIDE_SELL
                    else:
                        continue

                    monto = total_w * 0.45 
                    decs = 0 if 'PEPE' in m or 'DOGE' in m else 1
                    cant = round((monto * palanca) / cl[-1], decs)
                    
                    if disp >= monto:
                        c.futures_change_leverage(symbol=m, leverage=palanca)
                        c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"🎯 ENTRADA CONFIRMADA EN {m} POR TENDENCIA")
                        time.sleep(5); break

        except:
            time.sleep(2)
        time.sleep(5)

if __name__ == "__main__":
    bot_quantum_v13_final()
