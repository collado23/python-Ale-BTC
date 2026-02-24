import os, time, threading
from binance.client import Client
from binance.enums import *
from http.server import BaseHTTPRequestHandler, HTTPServer 

# --- SERVIDOR DE SALUD PARA RAILWAY ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ALE IA QUANTUM VIVE")

def run_health_server():
    try:
        server = HTTPServer(('0.0.0.0', int(os.getenv("PORT", 8080))), HealthCheck)
        server.serve_forever()
    except: pass

max_rois = {}

def bot_quantum_multi():
    threading.Thread(target=run_health_server, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    comision, descanso, palanca, stop_loss = 0.001, 30, 5, -4.0 #
    monedas = ['DOGEUSDC', 'SOLUSDC', 'XRPUSDC', 'ETHUSDC']

    print("🚀 MODO MULTI-OPERACIÓN ACTIVADO (60/100)")

    while True:
        try:
            acc = c.futures_account()
            disponible = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            
            # REGLA DE ESCALADA: Define cuántas balas podemos disparar
            if disponible >= 100: max_ops = 10
            elif disponible >= 60: max_ops = 6
            else: max_ops = 2

            pos = c.futures_position_information()
            activas = [p for p in pos if float(p.get('positionAmt', 0)) != 0]

            print(f"\n💰 SALDO: {disponible:.2f} | OPS: {len(activas)}/{max_ops}")

            # --- GESTIÓN DE SALIDAS (TRAILING Y SL) ---
            for activa in activas:
                sym = activa['symbol']
                q, side, entry = abs(float(activa['positionAmt'])), ('LONG' if float(activa['positionAmt']) > 0 else 'SHORT'), float(activa['entryPrice'])
                m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
                
                roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100

                if sym not in max_rois: max_rois[sym] = roi_pct
                if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct

                piso = max_rois[sym] - 0.3 if max_rois[sym] >= 2.3 else -99.0

                # CIERRE POR TRAILING (2.3/0.3) O STOP LOSS (-4%)
                if (max_rois[sym] >= 2.3 and roi_pct <= piso) or (roi_pct <= stop_loss):
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                    print(f"✅ CERRADA {sym} | ROI: {roi_pct:.2f}%")
                    if sym in max_rois: del max_rois[sym]
                    time.sleep(descanso) #

            # --- BUSCADOR MULTI-MONEDA (Sin el break limitador) ---
            for m in monedas:
                # Si ya llegamos al límite de operaciones (6 o 10), dejamos de buscar
                if len(activas) >= max_ops:
                    break
                
                # No entrar si ya tenemos esta moneda abierta
                if any(a['symbol'] == m for a in activas):
                    continue

                k = c.futures_klines(symbol=m, interval='1m', limit=30)
                cl = [float(x[4]) for x in k]
                e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                p_act = cl[-1]

                # Análisis de líneas 9 y 27
                if (p_act > e9 > e27) or (p_act < e9 < e27):
                    side_in = SIDE_BUY if p_act > e9 else SIDE_SELL
                    
                    c.futures_change_leverage(symbol=m, leverage=palanca) # Siempre 5x
                    
                    # Usamos el 20% del disponible para CADA operación
                    monto_op = (disponible * 0.20) * palanca 
                    cant = round(monto_op / p_act, 1 if m != 'DOGEUSDC' else 0)

                    if cant > 0:
                        c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"🎯 ENTRADA MULTI: {m} | SALDO USADO: 20%")
                        # Actualizamos la cuenta local para que el bucle sepa que ya sumó una
                        activas.append({'symbol': m}) 

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)
        time.sleep(10)

if __name__ == "__main__":
    bot_quantum_multi()
