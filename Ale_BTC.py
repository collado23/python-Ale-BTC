import os, time, threading
from binance.client import Client
from binance.enums import *

# Variables globales para el Dashboard
info_op = {"activo": False, "sym": "", "side": "", "roi": 0.0, "pico": 0.0, "piso": 0.0, "capital": 0.0, "entrada": 0.0}

def vigilante_ultra_rapido(c, sym, side, q, entry, palanca, comision, stop_loss):
    global info_op
    info_op["activo"] = True
    info_op["sym"] = sym
    info_op["side"] = "COMPRA (LONG)" if side == "LONG" else "VENTA (SHORT)"
    info_op["entrada"] = entry
    info_op["pico"] = 0.0
    
    while info_op["activo"]:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > info_op["pico"]:
                info_op["pico"] = roi
            
            # Margen de 0.05% desde el gatillo 1.05%
            info_op["roi"] = roi
            info_op["piso"] = info_op["pico"] - 0.05 if info_op["pico"] >= 1.05 else -99.0

            # CIERRE INSTANTÁNEO
            if (info_op["pico"] >= 1.05 and roi <= info_op["piso"]) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n✅ CIERRE EJECUTADO EN {sym} A {roi:.2f}%")
                info_op["activo"] = False
                break 
            
            time.sleep(0.1) 
        except:
            info_op["activo"] = False
            break

def bot_quantum_v4_inclination():
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("API_SECRET")
    
    c = Client(api_key, api_secret)
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca, monedas = 5, ['DOGEUSDC', 'ADAUSDC', 'XRPUSDC', 'TRXUSDC']
    comision, stop_loss = 0.001, -3.0

    print("🚀 ALE IA QUANTUM - MODO CIRUGÍA CON FILTRO DE TENDENCIA")

    while True:
        try:
            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            pos = c.futures_position_information()
            activas = [p for p in pos if float(p.get('positionAmt', 0)) != 0]

            if len(activas) > 0:
                # --- DASHBOARD DE OPERACIÓN ACTIVA ---
                for a in activas:
                    sym = a['symbol']
                    q = abs(float(a['positionAmt']))
                    if not info_op["activo"]:
                        side_in = "LONG" if float(a['positionAmt']) > 0 else "SHORT"
                        info_op["capital"] = (q * float(a['entryPrice'])) / palanca
                        threading.Thread(target=vigilante_ultra_rapido, 
                                         args=(c, sym, side_in, q, float(a['entryPrice']), palanca, comision, stop_loss),
                                         daemon=True).start()
                
                print("\n" + "📊" * 15)
                print(f"💰 DISPONIBLE: {disp:.2f} USDC")
                print(f"🔥 MONEDA: {info_op['sym']} | {info_op['side']}")
                print(f"💵 CAPITAL: {info_op['capital']:.2f} USDC | ENTRADA: {info_op['entrada']:.5f}")
                print(f"📈 ROI ACTUAL: {info_op['roi']:.2f}%")
                print(f"🔝 MÁXIMO: {info_op['pico']:.2f}% | PISO CIERRE: {info_op['piso']:.2f}%")
                print("-" * 30)

            else:
                # --- RADAR CON FILTRO DE INCLINACIÓN ---
                print(f"📡 RADAR BUSCANDO TENDENCIA... | SALDO: {disp:.2f}", end='\r')
                for m in monedas:
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    
                    # Cálculo de medias actuales
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    # Cálculo de la media 27 de hace 2 minutos para ver la dirección
                    e27_anterior = sum(cl[-29:-2])/27
                    
                    # FILTRO: Para comprar, la media amarilla (27) debe estar apuntando hacia arriba
                    tendencia_sube = e27 > e27_anterior
                    # FILTRO: Para vender, la media amarilla (27) debe estar apuntando hacia abajo
                    tendencia_baja = e27 < e27_anterior

                    # Lógica de entrada
                    if (cl[-1] > e9 > e27) and tendencia_sube:
                        side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and tendencia_baja:
                        side_order = SIDE_SELL
                    else:
                        continue # Si no hay tendencia clara, saltamos a la siguiente moneda

                    # Gestión de capital (Interés compuesto 90% para cuentas pequeñas)
                    monto = disp * 0.90 if (disp * palanca) < 5.1 else disp * 0.20
                    cant = round((monto * palanca) / cl[-1], 0 if m in ['DOGEUSDC', 'TRXUSDC'] else 1)
                    
                    if (cant * cl[-1]) >= 5.0:
                        c.futures_change_leverage(symbol=m, leverage=palanca)
                        c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"\n🎯 ENGANCHE: {m} | DIRECCIÓN: {side_order}")
                        time.sleep(5)
                        break

        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            time.sleep(5)
        
        time.sleep(2)

if __name__ == "__main__":
    bot_quantum_dashboard_final()
