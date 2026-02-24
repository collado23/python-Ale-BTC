import os, time, threading
from binance.client import Client
from binance.enums import *

# Memoria de picos para el Trailing
picos_maximos = {}

def vigilante_ultra_pegado(c, sym, side, q, entry, palanca, comision, stop_loss): 
    global picos_maximos
    picos_maximos[sym] = 0.0
    margen_trailing = 0.05 
    gatillo_activacion = 1.05

    print(f"⚡ VIGILANTE ACTIVADO: {sym}")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > picos_maximos[sym]:
                picos_maximos[sym] = roi
            
            piso = picos_maximos[sym] - margen_trailing if picos_maximos[sym] >= gatillo_activacion else -99.0

            # GATILLO INSTANTÁNEO
            if (picos_maximos[sym] >= gatillo_activacion and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"\n🚀 CIERRE QUIRÚRGICO EN {sym} | ROI FINAL: {roi:.2f}%")
                if sym in picos_maximos: del picos_maximos[sym]
                break 
            
            time.sleep(0.1) # Revisa 10 veces por segundo
        except Exception as e:
            print(f"⚠️ Error en vigilante {sym}: {e}")
            break

def bot_quantum_flash_v3():
    # Intentamos leer las llaves con ambos nombres posibles
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ ERROR: No se encuentran las API KEYS. Revisa la pestaña 'Variables' en Railway.")
        return

    try:
        c = Client(api_key, api_secret)
        c.API_URL = 'https://fapi.binance.com/fapi/v1'
        print("✅ CONEXIÓN EXITOSA CON BINANCE")
    except Exception as e:
        print(f"❌ FALLO DE AUTENTICACIÓN: {e}")
        return

    palanca, monedas = 5, ['DOGEUSDC', 'ADAUSDC', 'XRPUSDC', 'TRXUSDC']
    comision, stop_loss = 0.001, -3.0 

    print("🚀 ALE IA QUANTUM - ESCANEANDO MONEDAS BARATAS...")

    while True:
        try:
            # Revisamos saldo y posiciones actuales
            acc = c.futures_account()
            disp = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            pos = c.futures_position_information()
            activas = [p for p in pos if float(p.get('positionAmt', 0)) != 0]

            if len(activas) == 0:
                print(f"📡 Radar: OK | Saldo: {disp:.2f} USDC", end='\r')
                for m in monedas:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if (cl[-1] > e9 > e27) or (cl[-1] < e9 < e27):
                        side_in = SIDE_BUY if cl[-1] > e9 else SIDE_SELL
                        # Uso del 90% para capitales bajos (Interest Compuesto)
                        monto = disp * 0.90 if (disp * palanca) < 5.1 else disp * 0.20
                        
                        # Ajuste de decimales según moneda
                        decs = 0 if m in ['DOGEUSDC', 'TRXUSDC'] else 1
                        cant = round((monto * palanca) / cl[-1], decs)
                        
                        if (cant * cl[-1]) >= 5.0:
                            c.futures_change_leverage(symbol=m, leverage=palanca)
                            c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"\n🎯 ENGANCHE: {m} ({side_in}) | Iniciando vigilancia...")
                            
                            # Lanzamos el vigilante ultra rápido en su propio hilo
                            threading.Thread(target=vigilante_ultra_pegado, 
                                             args=(c, m, ("LONG" if side_in==SIDE_BUY else "SHORT"), cant, cl[-1], palanca, comision, stop_loss),
                                             daemon=True).start()
                            
                            time.sleep(30) # Descanso post-apertura
                            break
            else:
                # Si ya hay una operación enganchada, el vigilante ya está corriendo.
                # Aquí solo mostramos un aviso simple para saber que está vivo.
                for a in activas:
                    print(f"👀 Vigilando {a['symbol']}...", end='\r')
                time.sleep(2)

        except Exception as e:
            print(f"\n⚠️ Error en motor: {e}")
            time.sleep(10)
        
        time.sleep(2)

if __name__ == "__main__":
    bot_quantum_flash_v3()
