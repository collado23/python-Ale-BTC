import os, time, threading
from binance.client import Client
from binance.enums import *
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- SERVIDOR DE SALUD ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

def run_health_server():
    try: HTTPServer(('0.0.0.0', int(os.getenv("PORT", 8080))), HealthCheck).serve_forever()
    except: pass

max_rois = {}

def bot_quantum_antibucle():
    threading.Thread(target=run_health_server, daemon=True).start()
    c = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca, monedas = 5, ['DOGEUSDC', 'ADAUSDC', 'XRPUSDC', 'TRXUSDC']
    comision, descanso_corto, stop_loss = 0.001, 30, -4.0

    print("🚀 ALE IA QUANTUM - MODO ANTIBUCLE ACTIVADO")

    while True:
        try:
            acc = c.futures_account()
            disponible = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            total_wallet = float(acc['totalWalletBalance'])
            
            pos = c.futures_position_information()
            activas_info = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            n_activas = len(activas_info)

            # --- DASHBOARD ---
            print(f"\n💰 TOTAL: {total_wallet:.4f} | DISP: {disponible:.4f} | OPS: {n_activas}/2")

            if n_activas > 0:
                for activa in activas_info:
                    sym = activa['symbol']
                    q, entry = abs(float(activa['positionAmt'])), float(activa['entryPrice'])
                    side = 'LONG' if float(activa['positionAmt']) > 0 else 'SHORT'
                    m_p = float(c.futures_mark_price(symbol=sym)['mark_price'])
                    
                    roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100
                    if sym not in max_rois: max_rois[sym] = roi_pct
                    if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct
                    
                    piso = max_rois[sym] - 0.3 if max_rois[sym] >= 1.05 else -99.0
                    print(f"📈 {sym} | ROI: {roi_pct:.2f}% | MAX: {max_rois[sym]:.2f}%")

                    if (max_rois[sym] >= 1.05 and roi_pct <= piso) or (roi_pct <= stop_loss):
                        c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                        print(f"✅ CIERRE EN {sym}")
                        if sym in max_rois: del max_rois[sym]
                        
                        # Si cerramos con pérdida o ROI bajo, damos descanso largo para romper el bucle
                        descanso = 300 if roi_pct < 0.5 else descanso_corto
                        for i in range(descanso, 0, -1):
                            print(f"⏳ FILTRO ANTIBUCLE: Esperando {i}s...", end='\r'); time.sleep(1)
                        break

            else:
                for m in monedas:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    # FILTRO DE SEPARACIÓN (Evita el enredo de líneas)
                    separacion = abs(e9 - e27) / e27 * 100
                    
                    if separacion > 0.05: # Solo entra si hay una tendencia clara
                        if (cl[-1] > e9 > e27) or (cl[-1] < e9 < e27):
                            side_in = SIDE_BUY if cl[-1] > e9 else SIDE_SELL
                            monto_op = disponible * 0.90 if (disponible * palanca) < 5.1 else disponible * 0.20
                            cant = round((monto_op * palanca) / cl[-1], 0 if m in ['DOGEUSDC', 'TRXUSDC'] else 1)
                            
                            if (cant * cl[-1]) >= 5.0:
                                c.futures_change_leverage(symbol=m, leverage=palanca)
                                c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                                print(f"🎯 ENTRADA EN {m} | SEPARACIÓN: {separacion:.4f}%")
                                break

        except Exception as e:
            print(f"⚠️ Error: {e}"); time.sleep(10)
        time.sleep(2)
