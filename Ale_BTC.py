import os, time, threading
from binance.client import Client
from binance.enums import *

# === VARIABLES GLOBALES DE CONTROL ===
vigilantes_activos = set()
ultimo_cierre_tiempo = 0
contador_ops = 0 

def vigilante_bunker(c, sym, side, q, entry, palanca, comision):
    global vigilantes_activos, ultimo_cierre_tiempo
    vigilantes_activos.add(sym)
    
    # --- CONFIGURACIÓN SOLICITADA ---
    stop_loss = -4.0        # Corte de pérdida al -4%
    gatillo_trailing = 1.2  # Activa trailing al +1.2%
    margen_pegado = 0.3     # Si cae 0.3% desde el máximo, cierra
    
    pico = 0.0
    print(f"🛡️ [VIGILANTE] {sym} ACTIVO | SL: {stop_loss}% | TRAIL: {gatillo_trailing}%")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            
            # Cálculo de ROI
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            
            # Cálculo del punto de salida dinámica (PISO)
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            print(f"📊 {sym} | ROI: {roi:.2f}% | MAX: {pico:.2f}% | PISO: {piso:.2f}%")

            # LÓGICA DE CIERRE
            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                try:
                    c.futures_create_order(
                        symbol=sym, 
                        side=SIDE_SELL if side=="LONG" else SIDE_BUY, 
                        type=ORDER_TYPE_MARKET, 
                        quantity=q
                    )
                    print(f"✅ CIERRE EJECUTADO EN {sym} | ROI FINAL: {roi:.2f}%")
                    ultimo_cierre_tiempo = time.time()
                    break
                except Exception as e:
                    print(f"⚠️ Error crítico al intentar cerrar {sym}: {e}")
                    time.sleep(5)
            
            time.sleep(7) 
        except Exception as e:
            print(f"⚠️ Error en bucle de vigilancia {sym}: {e}")
            time.sleep(15)
    
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_quantum_v15_6():
    global contador_ops
    print("🚀 ALE IA QUANTUM V15.6 | INICIANDO SISTEMA...")
    print("⚙️ CONFIG: 40% Capital | 2 Monedas | SL -4% | Trail 1.2%")

    while True:
        try:
            # 1. CARGA DE API KEYS
            api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("API_SECRET")
            
            if not api_key or not api_secret:
                print("❌ Esperando API Keys en Railway...")
                time.sleep(30); continue

            c = Client(api_key, api_secret)
            c.API_URL = 'https://fapi.binance.com/fapi/v1'

            # 2. LECTURA DE BILLETERA (USDC)
            acc = c.futures_account()
            disp = 0.0
            total_w = 0.0
            for b in acc['assets']:
                if b['asset'] == 'USDC':
                    disp = float(b['availableBalance'])
                    total_w = float(b['walletBalance'])

            # 3. SINCRONIZACIÓN DE POSICIONES
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            # Lanzar vigilantes para posiciones que no lo tengan
            for r in reales:
                sym = r['symbol']
                if sym not in vigilantes_activos:
                    lado = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    cant = abs(float(r['positionAmt']))
                    precio_ent = float(r['entryPrice'])
                    threading.Thread(
                        target=vigilante_bunker, 
                        args=(c, sym, lado, cant, precio_ent, 5, 0.001), 
                        daemon=True
                    ).start()

            # 4. RADAR DE ENTRADA (SOL y PEPE)
            # Solo entra si hay menos de 2 monedas y pasaron 5 min del último cierre
            if len(simbolos_reales) < 2 and (time.time() - ultimo_cierre_tiempo > 300):
                for m in ['SOLUSDC', '1000PEPEUSDC']:
                    if m in simbolos_reales: continue
                    
                    # Estrategia EMA 9 vs 27
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9 = sum(cl[-9:])/9
                    e27 = sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    side_order = None
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant): side_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant): side_order = SIDE_SELL
                    
                    if side_order:
                        # --- CÁLCULO DEL 40% DEL TOTAL ---
                        # Esto asegura que siempre quede un 20% de margen libre
                        monto_in = total_w * 0.40 
                        
                        # Precisión de decimales
                        decs = 0 if 'PEPE' in m else 2
                        cant = round((monto_in * 5) / cl[-1], decs) # Apalancamiento x5
                        
                        # Verificación de saldo disponible y mínimo de Binance (5 USDC)
                        if disp >= monto_in and (cant * cl[-1]) >= 5.1:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side=side_order, type=ORDER_TYPE_MARKET, quantity=cant)
                            contador_ops += 1
                            print(f"🎯 DISPARO #{contador_ops} EN {m} | Inversión: {monto_in:.2f} USDC")
                            time.sleep(10)
                            break # Sale del for para no abrir las dos al mismo tiempo

            print(f"💰 WALLET: {total_w:.2f} | DISP: {disp:.2f} | ACTIVAS: {len(simbolos_reales)}/2 | OPS HOY: {contador_ops}")

        except Exception as e:
            print(f"⚠️ Error en bot: {e}")
            time.sleep(30)
        
        time.sleep(20)

if __name__ == "__main__":
    bot_quantum_v15_6()
