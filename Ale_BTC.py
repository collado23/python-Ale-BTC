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

def bot_quantum_multi_corregido():
    threading.Thread(target=run_health_server, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca, monedas = 5, ['DOGEUSDC', 'SOLUSDC', 'XRPUSDC', 'ETHUSDC']
    comision, descanso, stop_loss = 0.001, 30, -4.0 #

    print("🚀 ALE IA QUANTUM: MODO MULTI-MONEDA ACTIVADO")

    while True:
        try:
            acc = c.futures_account()
            disponible = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            
            # REGLA DE ESCALADA: 60 -> 6 ops / 100 -> 10 ops
            if disponible >= 100: max_ops = 10
            elif disponible >= 60: max_ops = 6
            else: max_ops = 2

            pos = c.futures_position_information()
            activas = [p for p in pos if float(p.get('positionAmt', 0)) != 0]

            print(f"\n💰 SALDO: {disponible:.2f} | ACTIVAS: {len(activas)}/{max_ops}")

            # --- 1. GESTIÓN DE CIERRES (TRAILING 2.3/0.3 Y SL 4%) ---
            for activa in activas:
                sym = activa['symbol']
                q, side, entry = abs(float(activa['positionAmt'])), ('LONG' if float(activa['positionAmt']) > 0 else 'SHORT'), float(activa['entryPrice'])
                m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
                roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100 #

                if sym not in max_rois: max_rois[sym] = roi_pct
                if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct
                
                piso = max_rois[sym] - 0.3 if max_rois[sym] >= 2.3 else -99.0 #

                if (max_rois[sym] >= 2.3 and roi_pct <= piso) or (roi_pct <= stop_loss): #
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                    print(f"✅ CIERRE {sym} | ROI: {roi_pct:.2f}%")
                    if sym in max_rois: del max_rois[sym]
                    time.sleep(descanso) #

            # --- 2. BUSCADOR MULTI-MONEDA (ENGANCHE) ---
            # Recorremos la lista y abrimos todas las que den señal hasta el límite max_ops
            for m in monedas:
                if len(activas) >= max_ops: break # Detener si ya llenamos los cupos
                if any(a['symbol'] == m for a in activas): continue # No repetir moneda

                k = c.futures_klines(symbol=m, interval='1m', limit=30)
                cl = [float(x[4]) for x in k]
                e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27 #
                p_act = cl[-1]

                if (p_act > e9 > e27) or (p_act < e9 < e27): #
                    side_in = SIDE_BUY if p_act > e9 else SIDE_SELL
                    
                    # CORRECCIÓN DE MÍNIMO 5 USDC (Nocional)
                    monto_op = disponible * 0.20 #
                    if (monto_op * palanca) < 5.1: monto_op = disponible * 0.95 # Para saldos pequeños
                    
                    cant = round((monto_op * palanca) / p_act, 1 if m != 'DOGEUSDC' else 0)

                    if (cant * p_act) >= 5.0: # Validar mínimo de Binance antes de enviar
                        c.futures_change_leverage(symbol=m, leverage=palanca) #
                        c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"🎯 ENTRADA MULTI: {m} | CANT: {cant}")
                        # Añadimos a la lista local para que el bucle sepa que ya hay una más
                        activas.append({'symbol': m}) 

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)
        time.sleep(15)

if __name__ == "__main__":
    bot_quantum_multi_corregido()
