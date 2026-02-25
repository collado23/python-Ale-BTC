import os, time, threading
from binance.client import Client 
from binance.enums import *

# === CONTROL GLOBAL ===
vigilantes_activos = set()
ultimo_cierre_tiempo = 0
contador_ops = 0

def vigilante_bunker(c, sym, side, q, entry, palanca, comision, stop_loss):
    global vigilantes_activos, ultimo_cierre_tiempo
    vigilantes_activos.add(sym)
    pico = 0.0
    gatillo_trailing, margen_pegado = 2.50, 0.15 
    
    print(f"🛡️ [VIGILANTE] {sym} ACTIVO | Entrada: {entry}")

    while True:
        try:
            res = c.futures_mark_price(symbol=sym)
            m_p = float(res['markPrice'])
            diff = (m_p - entry) if side == "LONG" else (entry - m_p)
            roi = ((diff / entry) * palanca - comision) * 100
            
            if roi > pico: pico = roi
            piso = pico - margen_pegado if pico >= gatillo_trailing else -99.0

            # Línea de ROI fija por fila
            print(f"📊 {sym} -> ROI: {roi:.2f}% | MAX: {pico:.2f}% | PISO: {piso:.2f}%")

            if (pico >= gatillo_trailing and roi <= piso) or (roi <= stop_loss):
                c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                print(f"✅ CIERRE {sym} EJECUTADO | ROI: {roi:.2f}%")
                ultimo_cierre_tiempo = time.time()
                break 
            time.sleep(6) 
        except:
            time.sleep(10)
    if sym in vigilantes_activos: vigilantes_activos.remove(sym)

def bot_quantum_v14_blindado():
    global contador_ops
    # 1. PREVENCIÓN DE ERROR UNBOUND (Foto 09:05)
    disp, total_w, max_ops = 0.0, 0.0, 2
    reales, simbolos_reales = [], []
    
    print("🚀 V14.8 BLINDADA | CARGANDO SISTEMA...")

    while True:
        try:
            # 2. CARGA DINÁMICA DE KEYS (Evita error Foto 09:12)
            api_key = os.getenv("API_KEY")
            api_secret = os.getenv("API_SECRET")
            
            if not api_key or not api_secret:
                print("❌ ERROR: API Keys no detectadas. Verificá 'Variables' en Railway.")
                time.sleep(30)
                continue

            c = Client(api_key, api_secret)
            c.API_URL = 'https://fapi.binance.com/fapi/v1'

            # 3. LECTURA DE BILLETERA
            acc = c.futures_account()
            for b in acc['assets']:
                if b['asset'] == 'USDC':
                    disp = float(b['availableBalance'])
                    total_w = float(b['walletBalance'])

            # 4. ESCALA SEGÚN CAPITAL (Tu meta: 60$ -> 6 ops | 100$ -> 10 ops)
            if total_w >= 100: max_ops = 10
            elif total_w >= 60: max_ops = 6
            else: max_ops = 2
            
            # 5. SINCRONIZACIÓN DE POSICIONES
            pos = c.futures_position_information()
            reales = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            simbolos_reales = [r['symbol'] for r in reales]

            for r in reales:
                s = r['symbol']
                if s not in vigilantes_activos:
                    side_in = "LONG" if float(r['positionAmt']) > 0 else "SHORT"
                    threading.Thread(target=vigilante_bunker, args=(c, s, side_in, abs(float(r['positionAmt'])), float(r['entryPrice']), 5, 0.001, -7.0), daemon=True).start()

            # 6. RADAR (SOL y PEPE únicamente)
            if len(simbolos_reales) < max_ops and (time.time() - ultimo_cierre_tiempo > 300):
                for m in ['SOLUSDC', '1000PEPEUSDC']:
                    if m in simbolos_reales: continue
                    
                    k = c.futures_klines(symbol=m, interval='1m', limit=35)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    e27_ant = sum(cl[-29:-2])/27
                    
                    if (cl[-1] > e9 > e27) and (e27 > e27_ant): s_order = SIDE_BUY
                    elif (cl[-1] < e9 < e27) and (e27 < e27_ant): s_order = SIDE_SELL
                    else: continue

                    monto_in = disp * 0.45 if total_w < 50 else disp * 0.20
                    decs = 0 if 'PEPE' in m else 2
                    cant = round((monto_in * 5) / cl[-1], decs)
                    
                    if (cant * cl[-1]) >= 5.0:
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side=s_order, type=ORDER_TYPE_MARKET, quantity=cant)
                        contador_ops += 1
                        print(f"🎯 DISPARO #{contador_ops} EN {m}")
                        time.sleep(10)
                        break

            print(f"💰 WALLET: {total_w:.2f} | DISP: {disp:.2f} | ACTIVAS: {len(simbolos_reales)}/{max_ops} | OPS HOY: {contador_ops}")

        except Exception as e:
            print(f"⚠️ Error: {e}. Reintentando...")
            time.sleep(20)
        
        time.sleep(15)

if __name__ == "__main__":
    bot_quantum_v14_blindado()
