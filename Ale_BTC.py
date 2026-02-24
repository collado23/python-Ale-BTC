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

# Memoria de Trailing y Control de Tiempo
max_rois = {}
ultimo_cierre_global = 0 

def bot_quantum_final_v2():
    global ultimo_cierre_global
    threading.Thread(target=run_health_server, daemon=True).start()
    
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca = 5 
    monedas = ['DOGEUSDC', 'SOLUSDC', 'XRPUSDC', 'ETHUSDC']
    comision, descanso, stop_loss = 0.001, 30, -4.0

    print("🚀 ALE IA QUANTUM - SISTEMA DE BLOQUEO 30S ACTIVADO")

    while True:
        try:
            # --- 1. VERIFICACIÓN DE DESCANSO OBLIGATORIO ---
            segundos_pasados = time.time() - ultimo_cierre_global
            if segundos_pasados < descanso:
                quedan = int(descanso - segundos_pasados)
                print(f"⏳ DESCANSO ACTIVO: Esperando {quedan}s para nueva operación...", end='\r')
                time.sleep(1)
                continue

            acc = c.futures_account()
            disponible = next((float(b['availableBalance']) for b in acc['assets'] if b['asset'] == 'USDC'), 0.0)
            
            # REGLA DE ESCALADA 60/100
            if disponible >= 100: max_ops = 10
            elif disponible >= 60: max_ops = 6
            else: max_ops = 2

            pos = c.futures_position_information()
            activas_info = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            n_activas = len(activas_info)

            # --- DASHBOARD EN PANTALLA ---
            print("\n" + "="*85)
            print(f"💰 SALDO: {disponible:.2f} USDC | OPS: {n_activas}/{max_ops} | SL: {stop_loss}%")
            print("-" * 85)
            print(f"{'MONEDA':<10} | {'PRECIO':<10} | {'ROI %':<8} | {'MAX %':<8} | {'PISO %':<8} | {'ESTADO'}")
            print("-" * 85)

            # --- 2. GESTIÓN DE POSICIONES ABIERTAS ---
            cierre_realizado = False
            for activa in activas_info:
                sym = activa['symbol']
                q, side, entry = abs(float(activa['positionAmt'])), ('LONG' if float(activa['positionAmt']) > 0 else 'SHORT'), float(activa['entryPrice'])
                
                # Obtener precio marcado
                m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
                
                # ROI Neto (Fórmula Quantum)
                roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100

                if sym not in max_rois: max_rois[sym] = roi_pct
                if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct
                
                piso = max_rois[sym] - 0.3 if max_rois[sym] >= 2.3 else -99.0
                estado = "🔥 TRAILING" if max_rois[sym] >= 2.3 else "⚡ VIGILANDO"

                print(f"{sym:<10} | {m_p:<10.4f} | {roi_pct:>7.2f}% | {max_rois[sym]:>7.2f}% | {piso:>7.2f}% | {estado}")

                # Lógica de Cierre
                if (max_rois[sym] >= 2.3 and roi_pct <= piso) or (roi_pct <= stop_loss):
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                    print(f"\n✅ CIERRE EN {sym} | ROI: {roi_pct:.2f}% | ACTIVANDO BLOQUEO 30S")
                    if sym in max_rois: del max_rois[sym]
                    ultimo_cierre_global = time.time() # Bloquea todo el bot
                    cierre_realizado = True
                    break # Salir del bucle de posiciones para entrar en descanso

            if cierre_realizado: continue # Reinicia el ciclo para aplicar el bloqueo

            # --- 3. BUSCADOR DE ENTRADAS (Solo si no hay bloqueo) ---
            if n_activas < max_ops:
                for m in monedas:
                    if any(a['symbol'] == m for a in activas_info): continue

                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    p_act = cl[-1]

                    # Señal de Enganche (9 y 27)
                    if (p_act > e9 > e27) or (p_act < e9 < e27):
                        side_in = SIDE_BUY if p_act > e9 else SIDE_SELL
                        
                        # Ajuste de Mínimo Nocional 5 USDC para tu saldo actual
                        monto_op = disponible * 0.20
                        if (monto_op * palanca) < 5.1: monto_op = disponible * 0.90 
                        
                        cant = round((monto_op * palanca) / p_act, 1 if m != 'DOGEUSDC' else 0)

                        if (cant * p_act) >= 5.0:
                            c.futures_change_leverage(symbol=m, leverage=palanca)
                            c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"\n🎯 ENGANCHE MULTIPLE: {m} | LADO: {side_in}")
                            n_activas += 1

        except Exception as e:
            print(f"\n⚠️ Error en ciclo: {e}")
            time.sleep(5)
        
        time.sleep(10) # Frecuencia de actualización de pantalla

if __name__ == "__main__":
    bot_quantum_final_v2()
