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

def bot_quantum_secuencial():
    threading.Thread(target=run_health_server, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca, monedas = 5, ['DOGEUSDC', 'SOLUSDC', 'XRPUSDC', 'ETHUSDC']
    comision, descanso_seg, stop_loss = 0.001, 30, -4.0 #

    print("🚀 ALE IA QUANTUM - MODO RADAR SECUENCIAL ACTIVADO")

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

            # --- DASHBOARD ---
            print("\n" + "="*80)
            print(f"💰 SALDO: {disponible:.2f} USDC | OPS: {n_activas}/{max_ops}")
            
            # --- 1. GESTIÓN DE POSICIONES EXISTENTES ---
            cierre_realizado = False
            for activa in activas_info:
                sym = activa['symbol']
                q, side, entry = abs(float(activa['positionAmt'])), ('LONG' if float(activa['positionAmt']) > 0 else 'SHORT'), float(activa['entryPrice'])
                m_p = float(c.futures_mark_price(symbol=sym)['markPrice'])
                
                roi_pct = ((((m_p - entry)/entry if side=="LONG" else (entry - m_p)/entry) * palanca) - comision) * 100
                if sym not in max_rois: max_rois[sym] = roi_pct
                if roi_pct > max_rois[sym]: max_rois[sym] = roi_pct
                
                piso = max_rois[sym] - 0.3 if max_rois[sym] >= 2.3 else -99.0
                print(f"📈 {sym} | ROI: {roi_pct:.2f}% | MAX: {max_rois[sym]:.2f}% | PISO: {piso:.2f}%")

                # CIERRE (TRAILING 2.3/0.3 O STOP LOSS -4%)
                if (max_rois[sym] >= 2.3 and roi_pct <= piso) or (roi_pct <= stop_loss):
                    c.futures_create_order(symbol=sym, side=SIDE_SELL if side=="LONG" else SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=q)
                    print(f"\n✅ POSICIÓN CERRADA. ENTRANDO EN DESCANSO DE {descanso_seg}S...")
                    if sym in max_rois: del max_rois[sym]
                    cierre_realizado = True
                    break 

            # --- 2. EL FRENO DE MANO TRAS CIERRE ---
            if cierre_realizado:
                for i in range(descanso_seg, 0, -1):
                    print(f"⏳ DESCANSO POST-CIERRE: Quedan {i}s para reactivar radar...", end='\r')
                    time.sleep(1)
                print("\n📡 RADAR RE-ACTIVADO.")
                continue

            # --- 3. BUSCADOR CON FILTRO SECUENCIAL ---
            # Si ya tenemos el máximo de operaciones permitidas, no busca.
            # Pero la clave aquí es: SI HAY UNA OPERACIÓN CORRIENDO, NO BUSCAMOS OTRA HASTA QUE TERMINE.
            if n_activas < max_ops:
                # Si quieres que abra una por una estrictamente, habilitamos el radar solo si no hay nada abierto:
                # Si prefieres que pueda tener varias pero que las abra con 30s de diferencia, usamos esto:
                
                radar_encendido = True
                for m in monedas:
                    if any(a['symbol'] == m for a in activas_info): continue
                    
                    # SI YA SE ABRIÓ UNA MONEDA EN ESTE CICLO, EL RADAR SE APAGA
                    if not radar_encendido: break

                    k = c.futures_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if (cl[-1] > e9 > e27) or (cl[-1] < e9 < e27): #
                        side_in = SIDE_BUY if cl[-1] > e9 else SIDE_SELL
                        
                        monto_op = disponible * 0.20 #
                        if (monto_op * palanca) < 5.1: monto_op = disponible * 0.90 #
                        
                        cant = round((monto_op * palanca) / cl[-1], 1 if m != 'DOGEUSDC' else 0)
                        if (cant * cl[-1]) >= 5.0:
                            c.futures_change_leverage(symbol=m, leverage=palanca)
                            c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"\n🎯 MONEDA ENGANCHADA: {m}. APAGANDO RADAR POR SEGURIDAD...")
                            
                            # AQUÍ ESTÁ TU CLAVE: En cuanto engancha una, activa el descanso antes de permitir buscar la otra
                            radar_encendido = False 
                            for i in range(descanso_seg, 0, -1):
                                print(f"⏳ PAUSA DE ENGANCHE: Esperando {i}s para buscar la siguiente moneda...", end='\r')
                                time.sleep(1)
                            break 

        except Exception as e:
            print(f"\n⚠️ Reintentando... {e}")
            time.sleep(10)
        time.sleep(10)

if __name__ == "__main__":
    bot_quantum_secuencial()
