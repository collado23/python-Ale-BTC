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
    server = HTTPServer(('0.0.0.0', int(os.getenv("PORT", 8080))), HealthCheck)
    server.serve_forever()

# --- MEMORIA DE TRAILING ---
max_rois = {}

def bot_railway():
    # Iniciar servidor de salud en segundo plano
    threading.Thread(target=run_health_server, daemon=True).start()

    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    comision, descanso, palanca, stop_loss = 0.001, 30, 5, -4.0
    monedas = ['DOGEUSDC', 'SOLUSDC', 'XRPUSDC', 'ETHUSDC']

    print("🚀 ALE IA QUANTUM DESPLEGADO EN RAILWAY")

    while True:
        try:
            acc = c.futures_account()
            disponible = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            
            if disponible >= 100: max_ops = 10
            elif disponible >= 60: max_ops = 6
            else: max_ops = 2

            pos = c.futures_position_information()
            activas = [p for p in pos if float(p.get('positionAmt', 0)) != 0]

            # Imprimimos bloque de estado (Sin 'clear' para evitar el error TERM)
            print("\n" + "="*60)
            print(f"💰 SALDO: {disponible:.2f} USDC | OPS: {len(activas)}/{max_ops} | SL: {stop_loss}%")
            print("-" * 60)
            print(f"{'MONEDA':<10} | {'ROI %':<8} | {'MAX %':<8} | {'PISO %':<8} | {'ESTADO'}")

            for activa in activas:
                sym = activa['symbol']
                q, side, entry = abs(float(activa['positionAmt'])), ('LONG' if float(activa['positionAmt']) > 0 else 'SHORT'), float(activa['entryPrice'])
                m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
                
                roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100

                if sym not in max_rois: max_rois[sym] = roi_pct
                if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct

                piso = max_rois[sym] - 0.3 if max_rois[sym] >= 2.3 else -99.0
                estado = "🔥 TRAILING" if max_rois[sym] >= 2.3 else "⚡ VIGILANDO"

                print(f"{sym:<10} | {roi_pct:>7.2f}% | {max_rois[sym]:>7.2f}% | {piso:>7.2f}% | {estado}")

                if (max_rois[sym] >= 2.3 and roi_pct <= piso) or (roi_pct <= stop_loss):
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                    print(f"✅ CIERRE EN {sym} | ROI: {roi_pct:.2f}%")
                    if sym in max_rois: del max_rois[sym]
                    time.sleep(descanso)

            # BUSCADOR
            if len(activas) < max_ops:
                for m in monedas:
                    if any(a['symbol'] == m for a in activas): continue
                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    if (cl[-1] > e9 > e27) or (cl[-1] < e9 < e27):
                        side_in = SIDE_BUY if cl[-1] > e9 else SIDE_SELL
                        c.futures_change_leverage(symbol=m, leverage=palanca)
                        cant = round(((disponible * 0.20) * palanca) / cl[-1], 1 if m != 'DOGEUSDC' else 0)
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"🎯 ENTRADA EN {m} ({side_in})")
                            break

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)
        time.sleep(15) # Más lento para no saturar los logs de Railway

if __name__ == "__main__":
    bot_railway()
