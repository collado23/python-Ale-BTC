import os, time, threading
from binance.client import Client
from binance.enums import *
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- SERVIDOR DE SALUD PARA RAILWAY ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

def run_health_server():
    try: HTTPServer(('0.0.0.0', int(os.getenv("PORT", 8080))), HealthCheck).serve_forever() 
    except: pass

max_rois = {}

def bot_quantum_v3_bloqueo_total():
    threading.Thread(target=run_health_server, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca, monedas = 5, ['DOGEUSDC', 'SOLUSDC', 'XRPUSDC', 'ETHUSDC']
    comision, descanso_seg, stop_loss = 0.001, 30, -4.0

    print("🚀 ALE IA QUANTUM - SISTEMA DE BLOQUEO TOTAL ACTIVADO")

    while True:
        try:
            acc = c.futures_account()
            disponible = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            
            # REGLA DE ESCALADA
            if disponible >= 100: max_ops = 10
            elif disponible >= 60: max_ops = 6
            else: max_ops = 2

            pos = c.futures_position_information()
            activas_info = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            n_activas = len(activas_info)

            # --- PANTALLA ---
            print("\n" + "="*80)
            print(f"💰 SALDO: {disponible:.2f} USDC | OPS: {n_activas}/{max_ops} | SL: {stop_loss}%")
            print("-" * 80)
            print(f"{'MONEDA':<10} | {'PRECIO':<10} | {'ROI %':<8} | {'MAX %':<8} | {'PISO %':<8}")

            # --- 1. GESTIÓN DE POSICIONES ---
            for activa in activas_info:
                sym = activa['symbol']
                q, side, entry = abs(float(activa['positionAmt'])), ('LONG' if float(activa['positionAmt']) > 0 else 'SHORT'), float(activa['entryPrice'])
                m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
                
                roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100

                if sym not in max_rois: max_rois[sym] = roi_pct
                if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct
                
                piso = max_rois[sym] - 0.3 if max_rois[sym] >= 2.3 else -99.0
                print(f"{sym:<10} | {m_p:<10.4f} | {roi_pct:>7.2f}% | {max_rois[sym]:>7.2f}% | {piso:>7.2f}%")

                # SI TOCA CIERRE (TRAILING O STOP LOSS)
                if (max_rois[sym] >= 2.3 and roi_pct <= piso) or (roi_pct <= stop_loss):
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                    
                    print(f"\n🛑 CIERRE DETECTADO EN {sym}. INICIANDO BLOQUEO TOTAL DE {descanso_seg}S...")
                    if sym in max_rois: del max_rois[sym]
                    
                    # EL SECRETO: Un sleep real que detiene TODO el programa
                    for i in range(descanso_seg, 0, -1):
                        print(f"⏳ MOTOR CONGELADO: Reiniciando en {i}s...", end='\r')
                        time.sleep(1)
                    print("\n✅ MOTOR REINICIADO. BUSCANDO NUEVAS SEÑALES...")
                    break # Rompe el ciclo de posiciones para re-escanear todo desde cero

            # --- 2. BUSCADOR DE ENTRADAS ---
            if n_activas < max_ops:
                for m in monedas:
                    if any(a['symbol'] == m for a in activas_info): continue

                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if (cl[-1] > e9 > e27) or (cl[-1] < e9 < e27):
                        side_in = SIDE_BUY if cl[-1] > e9 else SIDE_SELL
                        
                        # Ajuste Nocional para saldo bajo (0.88 USDC)
                        monto_op = disponible * 0.20
                        if (monto_op * palanca) < 5.1: monto_op = disponible * 0.90
                        
                        cant = round((monto_op * palanca) / cl[-1], 1 if m != 'DOGEUSDC' else 0)

                        if (cant * cl[-1]) >= 5.0:
                            c.futures_change_leverage(symbol=m, leverage=palanca)
                            c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"🎯 ENGANCHE: {m} | LADO: {side_in}")
                            n_activas += 1

        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            time.sleep(5)
        
        time.sleep(10)

if __name__ == "__main__":
    bot_quantum_v3_bloqueo_total()
