import os, time, threading
from binance.client import Client
from binance.enums import *

# === VARIABLES GLOBALES DE CONTROL ===
vigilantes_activos = set()
ultimo_cierre_tiempo = 0
contador_operaciones = 0

def vigilante_bunker(c, sym, side, q, entry, palanca, comision, stop_loss):
    global vigilantes_activos, ultimo_cierre_tiempo
    vigilantes_activos.add(sym)
    pico = 0.0
    gatillo_trailing, margen_pegado = 2.50, 0.15 
    
    print(f"🛡️ [VIGILANTE] {sym} PROTEGIENDO. Entrada: {entry}")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['mark_price'] if 'mark_price' in res else res['markPrice'])
            
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # ROI visible línea por línea para que no se pierda nada
            print(f"📊 {sym} -> ROI: {roi:.2f}% | MAX: {pico:.2f}% | PISO: {piso:.2f}%")

            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"✅ CIERRE SEGURO {sym} | ROI FINAL: {roi:.2f}%")
                ultimo_cierre_tiempo = time.time()
                break 
            
            time.sleep(6) 
        except Exception as e:
            print(f"⚠️ Error en vigilante {sym}: {e}")
            time.sleep(10)
    
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_quantum_v14_final():
    global contador_operaciones
    # Inicialización blindada (Previene el error de tus fotos)
    disp = 0.0
    simbolos_reales = []
    total_wallet = 0.0
    
    # 1. CARGA DE SEGURIDAD DE KEYS
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ ERROR CRÍTICO: Las API Keys desaparecieron de Railway. Verificá 'Variables'.")
        return

    try:
        c = Client(api_key, api_secret)
        c.API_URL = 'https://fapi.binance.com/fapi/v1'
    except:
        print("❌ ERROR: No se pudo conectar a Binance. Revisá tus Keys.")
        return

    monedas_radar = ['SOLUSDC', '1000PEPEUSDC']
    palanca, stop_loss = 5, -7.0

    print("🚀 V14.7 INICIADA | MODO ESCALABLE | ANTIFRENO")

    while True:
        try:
            # 2. LECTURA DE CUENTA (Primero para evitar errores de impresión)
            acc = c.futures_account()
            for b in acc['assets']:
                if b['asset'] == 'USDC':
                    disp = float(b['availableBalance'])
                    total_wallet = float(b['walletBalance'])

            # 3. AUTO-ESCALA SEGÚN TU PLAN
            # 10$ -> 2 ops | 60$ -> 6 ops | 100$ -> 10 ops
            max_ops = 2
            if total_wallet >= 100: max_ops = 10
            elif total_wallet >= 60: max_ops = 6
            
            # 4. SINCRONIZACIÓN DE POSICIONES
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            for r in reales:
                s = r['symbol']
                if s not in vigilantes_activos:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    threading.Thread(target=vigilante_bunker, args=(c, s, side_in, abs(float(r['positionAmt'])), float(r['entryPrice']), palanca, 0.001, stop_loss), daemon=True).start()

            # 5. RADAR (Solo si hay espacio y pasaron 5 min del último cierre)
            if len(simbolos_reales) < max_ops and (time.time() - ultimo_cierre_tiempo > 300):
                for m in monedas_radar:
                    if m in simbolos_reales: continue
                    
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant): side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant): side_order = SIDE_SELL
                    else: continue

                    # Gestión de capital (Interés compuesto suave)
                    monto_in = disp * 0.45 if total_wallet < 50 else disp * 0.20
                    # Ajuste de precisión para SOL (2 decimales) y PEPE (0 decimales)
                    decs = 0 if 'PEPE' in m else 2
                    cant = round((monto_in * palanca) / cl[-1], decs)
                    
                    if (cant * cl[-1]) >= 5.1:
                        c.futures_change_leverage(symbol=m, leverage=palanca)
                        c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                        contador_operaciones += 1
                        print(f"🎯 ENTRADA #{contador_operaciones} EN {m}")
                        time.sleep(10)
                        break

            print(f"💰 BILLETERA: {total_wallet:.2f} USDC | DISP: {disp:.2f} | ACTIVAS: {len(simbolos_reales)}/{max_ops} | TOTAL OPS: {contador_operaciones}")

        except Exception as e:
            print(f"⚠️ Reintentando conexión... Esperando 15s. ({e})")
            time.sleep(15)
        
        time.sleep(20)

if __name__ == "__main__":
    bot_quantum_v14_final()
