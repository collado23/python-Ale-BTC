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

def bot_quantum_monedas_baratas():
    threading.Thread(target=run_health_server, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca = 5
    # LAS 4 MONEDAS MÁS BARATAS (BAJO PRECIO UNITARIO)
    monedas = ['DOGEUSDC', 'ADAUSDC', 'XRPUSDC', 'TRXUSDC']
    comision, descanso_seg, stop_loss = 0.001, 30, -4.0

    print("🚀 ALE IA QUANTUM - MODO MONEDAS BARATAS (TRX AÑADIDA)")

    while True:
        try:
            acc = c.futures_account()
            disponible = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            total_wallet = float(acc['totalWalletBalance'])
            
            # REGLA DE ESCALADA 60/100
            if disponible >= 100: max_ops = 10
            elif disponible >= 60: max_ops = 6
            else: max_ops = 2

            pos = c.futures_position_information()
            activas_info = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            n_activas = len(activas_info)

            # --- DASHBOARD INTEGRAL ---
            print("\n" + "💰" * 15)
            print(f"BILLETERA TOTAL: {total_wallet:.4f} USDC")
            print(f"SALDO DISPONIBLE: {disponible:.4f} USDC")
            print(f"OPERACIONES: {n_activas} de {max_ops}")
            print("-" * 40)

            cierre_detectado = False

            if n_activas > 0:
                print(f"{'MONEDA':<10} | {'CAPITAL':<8} | {'ROI%':<8} | {'PISO%'}")
                for activa in activas_info:
                    sym = activa['symbol']
                    q = abs(float(activa['positionAmt']))
                    side = 'LONG' if float(activa['positionAmt']) > 0 else 'SHORT'
                    entry = float(activa['entryPrice'])
                    m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
                    
                    nocional = q * m_p
                    capital_usado = nocional / palanca
                    roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100
                    
                    if sym not in max_rois: max_rois[sym] = roi_pct
                    if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct
                    
                    # Trailing Stop arranca en 1.05%
                    piso = max_rois[sym] - 0.3 if max_rois[sym] >= 1.05 else -99.0

                    print(f"{sym:<10} | {capital_usado:>7.2f}  | {roi_pct:>7.2f}% | {piso:>7.2f}%")

                    # LÓGICA DE CIERRE
                    if (max_rois[sym] >= 1.05 and roi_pct <= piso) or (roi_pct <= stop_loss):
                        c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                        print(f"\n✅ CIERRE EN {sym} | ROI: {roi_pct:.2f}%")
                        if sym in max_rois: del max_rois[sym]
                        
                        for i in range(descanso_seg, 0, -1):
                            print(f"⏳ DESCANSO OBLIGATORIO: {i}s...", end='\r')
                            time.sleep(1)
                        cierre_detectado = True
                        break
                
                if cierre_detectado: continue

            else:
                # RADAR SECUENCIAL (Busca la siguiente barata)
                print(f"📡 RADAR BUSCANDO EN: {monedas}...", end='\r')
                for m in monedas:
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    p_act = cl[-1]

                    if (p_act > e9 > e27) or (p_act < e9 < e27):
                        side_in = SIDE_BUY if p_act > e9 else SIDE_SELL
                        
                        # Usar 90% del capital si el saldo es bajo (< 5 USDC)
                        monto_op = disponible * 0.90 if (disponible * 0.20 * palanca) < 5.1 else disponible * 0.20
                        
                        # Ajuste de decimales según moneda
                        decs = 0 if m in ['DOGEUSDC', 'TRXUSDC'] else (1 if m == 'ADAUSDC' else 1)
                        cant = round((monto_op * palanca) / p_act, decs)
                        
                        if (cant * p_act) >= 5.0:
                            c.futures_change_leverage(symbol=m, leverage=palanca)
                            c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"\n🎯 ENGANCHE EN {m} | CAPITAL: {monto_op:.2f} USDC")
                            break

        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            time.sleep(5)
        
        time.sleep(2)

if __name__ == "__main__":
    bot_quantum_monedas_baratas()
