import os, time, threading
from binance.client import Client
from binance.enums import *

# Memoria para el Dashboard Multi-Operación
ops_activas = {} # Estructura: { symbol: {info} }

def vigilante_individual(c, sym, side, q, entry, palanca, comision, stop_loss):
    global ops_activas
    pico = 0.0
    gatillo_trailing = 1.20 
    margen_pegado = 0.05

    while sym in ops_activas:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0
            
            # Actualizar datos para el Dashboard
            if sym in ops_activas:
                ops_activas[sym].update({"roi": roi, "pico": pico, "piso": piso})

            # CIERRE POR META O STOP LOSS
            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ CIERRE EN {sym}: {roi:.2f}%")
                if sym in ops_activas: del ops_activas[sym]
                break 
            
            time.sleep(0.1) # Reacción ultra rápida
        except:
            time.sleep(0.5)

def bot_quantum_v10_doble_op():
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("API_SECRET")
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    monedas = ['DOGEUSDC', 'ADAUSDC', 'XRPUSDC', 'TRXUSDC']
    palanca, stop_loss = 5, -4.0
    max_ops = 2 

    print(f"🚀 ALE IA QUANTUM V10 | DOBLE OPERACIÓN (90% TOTAL)")

    while True:
        try:
            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            # Revisar posiciones reales
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            
            # Limpiar memoria de ops cerradas manualmente si las hubiera
            simbolos_reales = [r['symbol'] for r in reales]
            for s in list(ops_activas.keys()):
                if s not in simbolos_reales: del ops_activas[s]

            # --- DASHBOARD ---
            print("\n" + "💎" * 15)
            print(f"💰 SALDO DISP: {disp:.2f} USDC | ACTIVAS: {len(reales)}/{max_ops}")
            
            for r in reales:
                s = r['symbol']
                if s not in ops_activas:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    q, ent = abs(float(r['positionAmt'])), float(r['entryPrice'])
                    ops_activas[s] = {"roi": 0, "pico": 0, "piso": -99, "side": side_in}
                    threading.Thread(target=vigilante_individual, args=(c, s, side_in, q, ent, palanca, 0.001, stop_loss), daemon=True).start()
                
                info = ops_activas.get(s, {})
                print(f"🔥 {s} ({info.get('side','?')}) | ROI: {info.get('roi',0):.2f}% | MAX: {info.get('pico',0):.2f}%")

            # --- LÓGICA DE ENTRADA ---
            if len(reales) < max_ops:
                print(f"📡 RADAR BUSCANDO HUECO... {(max_ops - len(reales))} DISPONIBLE", end='\r')
                for m in monedas:
                    if any(m == r['symbol'] for r in reales): continue
                    
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant): side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant): side_order = SIDE_SELL
                    else: continue

                    # 45% del capital por operación para poder abrir dos
                    monto = disp * 0.45 
                    decs = 0 if m in ['DOGEUSDC', 'TRXUSDC'] else 1
                    cant = round((monto * palanca) / cl[-1], decs)
                    
                    if (cant * cl[-1]) >= 5.0:
                        c.futures_change_leverage(symbol=m, leverage=palanca)
                        c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"\n🎯 DISPARO EN {m}!")
                        time.sleep(5)
                        break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(2)
        time.sleep(1)

if __name__ == "__main__":
    bot_quantum_v10_doble_op()
