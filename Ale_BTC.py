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

def bot_quantum_visual_realtime():
    threading.Thread(target=run_health_server, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca = 5
    # Cambiamos SOL por ADA (más barata)
    monedas = ['DOGEUSDC', 'ADAUSDC', 'XRPUSDC', 'ETHUSDC']
    comision, descanso_seg, stop_loss = 0.001, 30, -4.0

    print("🚀 ALE IA QUANTUM - MODO VISUAL REAL-TIME")

    while True:
        try:
            acc = c.futures_account()
            disponible = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            # REGLA DE ESCALADA 60/100
            if disponible >= 100: max_ops = 10
            elif disponible >= 60: max_ops = 6
            else: max_ops = 2

            pos = c.futures_position_information()
            activas_info = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            n_activas = len(activas_info)

            # --- MONITOR DE OPERACIÓN EN VIVO ---
            if n_activas > 0:
                print("\n" + "🔍" * 20)
                print(f"💰 SALDO DISPONIBLE: {disponible:.2f} USDC")
                
                cierre_detectado = False
                for activa in activas_info:
                    sym = activa['symbol']
                    q, side, entry = abs(float(activa['positionAmt'])), ('LONG' if float(activa['positionAmt']) > 0 else 'SHORT'), float(activa['entryPrice'])
                    m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
                    
                    # ROI Neto con palanca 5x
                    roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100
                    
                    if sym not in max_rois: max_rois[sym] = roi_pct
                    if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct
                    
                    piso = max_rois[sym] - 0.3 if max_rois[sym] >= 2.3 else -99.0

                    print(f"📈 OPERACIÓN: {sym} | LADO: {side}")
                    print(f"💵 PRECIO ENTRADA: {entry} | ACTUAL: {m_p}")
                    print(f"📊 ROI: {roi_pct:.2f}% | MÁXIMO: {max_rois[sym]:.2f}% | PISO: {piso:.2f}%")
                    print("-" * 40)

                    # GATILLO DE CIERRE INSTANTÁNEO
                    if (max_rois[sym] >= 2.3 and roi_pct <= piso) or (roi_pct <= stop_loss):
                        c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                        print(f"\n✅ CIERRE EJECUTADO EN {sym} | ROI: {roi_pct:.2f}%")
                        if sym in max_rois: del max_rois[sym]
                        
                        # BLOQUEO POST-CIERRE
                        for i in range(descanso_seg, 0, -1):
                            print(f"⏳ DESCANSO OBLIGATORIO: {i}s...", end='\r')
                            time.sleep(1)
                        cierre_detectado = True
                        break
                
                if cierre_detectado: continue
                time.sleep(1) # Actualización rápida cada segundo para que veas los números cambiar

            # --- BUSCADOR (SOLO SI NO HAY NADA ABIERTO) ---
            else:
                print(f"📡 BUSCANDO SEÑAL EN: {monedas}...", end='\r')
                for m in monedas:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    p_act = cl[-1]

                    if (p_act > e9 > e27) or (p_act < e9 < e27):
                        side_in = SIDE_BUY if p_act > e9 else SIDE_SELL
                        
                        # Cantidad ajustada a tu saldo (mínimo nocional 5 USDC)
                        monto_op = disponible * 0.20
                        if (monto_op * palanca) < 5.1: monto_op = disponible * 0.90
                        
                        cant = round((monto_op * palanca) / p_act, 1 if m != 'DOGEUSDC' else 0)
                        
                        if (cant * p_act) >= 5.0:
                            c.futures_change_leverage(symbol=m, leverage=palanca)
                            c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"\n🎯 ENGANCHE: {m} ({side_in})")
                            break # Abre una y pasa a modo visual

        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            time.sleep(5)
        time.sleep(2)

if __name__ == "__main__":
    bot_quantum_visual_realtime()
