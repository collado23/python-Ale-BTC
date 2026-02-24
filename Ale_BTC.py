import os, time
from binance.client import Client
from binance.enums import *

# Memoria para rastrear el ROI más alto por moneda
max_rois = {}

def bot_quantum_final():
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET")) 
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    comision = 0.001 
    descanso = 30
    palanca = 5 
    stop_loss = -4.0  # <--- STOP LOSS AL 4% COMO PEDISTE
    monedas = ['DOGEUSDC', 'SOLUSDC', 'XRPUSDC', 'ETHUSDC'] 

    print("🚀 ALE IA QUANTUM INICIADO | STOP LOSS: 4% | TRAILING: 2.3%")

    while True:
        try:
            acc = c.futures_account()
            disponible = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            
            # REGLA DE ESCALADA 60/100
            if disponible >= 100: max_ops = 10
            elif disponible >= 60: max_ops = 6
            else: max_ops = 2

            pos = c.futures_position_information()
            activas = [p for p in pos if float(p.get('positionAmt', 0)) != 0]

            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"💰 SALDO: {disponible:.2f} USDC | OPS: {len(activas)}/{max_ops} | SL: {stop_loss}%")
            print("-" * 80)
            print(f"{'MONEDA':<10} | {'PRECIO':<10} | {'ROI %':<8} | {'MAX %':<8} | {'PISO %':<8} | {'ESTADO'}")
            print("-" * 80)

            for activa in activas:
                sym = activa['symbol']
                q = abs(float(activa['positionAmt']))
                side = 'LONG' if float(activa['positionAmt']) > 0 else 'SHORT'
                entry = float(activa['entryPrice'])
                
                res = c.futures_mark_price(symbol=sym)
                m_p = float(res['markPrice'])
                
                # ROI Neto (incluye palanca y resta comisión)
                roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100

                # Lógica de Máximos para el Trailing
                if sym not in max_rois: max_rois[sym] = roi_pct
                if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct

                # Cálculo de Trailing Stop (Inicia en 2.3% cada 0.3%)
                piso = -99.0
                estado = "⚡ VIGILANDO"
                if max_rois[sym] >= 2.3:
                    piso = max_rois[sym] - 0.3
                    estado = "🔥 TRAILING"
                elif roi_pct <= stop_loss:
                    estado = "🚨 STOP LOSS"

                print(f"{sym:<10} | {m_p:<10.4f} | {roi_pct:>7.2f}% | {max_rois[sym]:>7.2f}% | {piso:>7.2f}% | {estado}")

                # GATILLOS DE CIERRE
                if (max_rois[sym] >= 2.3 and roi_pct <= piso) or (roi_pct <= stop_loss):
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, 
                                         type=ORDER_TYPE_MARKET, quantity=q)
                    print(f"\n✅ CIERRE EN {sym} ({estado}) | ROI FINAL: {roi_pct:.2f}%")
                    if sym in max_rois: del max_rois[sym]
                    time.sleep(descanso)

            # --- BUSCADOR DE ENTRADAS (20% SALDO) ---
            if len(activas) < max_ops:
                for m in monedas:
                    if any(a['symbol'] == m for a in activas): continue 

                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    p_act = cl[-1]

                    # Cruce de líneas 9 y 27
                    if p_act > e9 > e27: side_in = SIDE_BUY
                    elif p_act < e9 < e27: side_in = SIDE_SELL
                    else: continue

                    c.futures_change_leverage(symbol=m, leverage=palanca)
                    monto_op = (disponible * 0.20) * palanca 
                    cant = round(monto_op / p_act, 1 if m != 'DOGEUSDC' else 0)

                    if cant > 0:
                        c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                        max_rois[m] = 0
                        print(f"\n🎯 NUEVA ENTRADA: {m} | PRECIO: {p_act}")
                        break 

        except Exception as e:
            time.sleep(5)
        
        time.sleep(3)

if __name__ == "__main__":
    bot_quantum_final()
