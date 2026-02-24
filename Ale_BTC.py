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

# Memoria global
max_rois = {}
lock = threading.Lock()

def vigilante_ultra_rapido(client, symbol, side, entry_price, quantity, palanca, comision, stop_loss):
    """Este motor solo mira el precio y cierra lo más rápido posible"""
    print(f"👀 VIGILANTE ACTIVADO PARA {symbol}")
    max_roi = -99.0
    
    while True:
        try:
            # Pedir precio actual (Mark Price es más estable para futuros)
            res = client.futures_mark_price(symbol=symbol)
            m_p = float(res['markPrice'])
            
            # Cálculo de ROI Neto
            diff = (m_p - entry_price) if side == "LONG" else (entry_price - m_p)
            roi_pct = ((diff / entry_price) * palanca - comision) * 100
            
            if roi_pct > max_roi:
                max_roi = roi_pct
            
            piso = max_roi - 0.3 if max_roi >= 2.3 else -99.0
            
            # GATILLO INSTANTÁNEO
            if (max_roi >= 2.3 and roi_pct <= piso) or (roi_pct <= stop_loss):
                client.futures_create_order(
                    symbol=symbol,
                    side=SIDE_SELL if side == "LONG" else SIDE_BUY,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity
                )
                print(f"⚡ CIERRE FLASH {symbol} | ROI: {roi_pct:.2f}% | MAX: {max_roi:.2f}%")
                break # Termina el hilo de vigilancia
                
            time.sleep(0.5) # Mira el precio 2 veces por segundo (muy rápido)
        except Exception as e:
            print(f"⚠️ Error en vigilante {symbol}: {e}")
            break

def bot_quantum_ultra_velocidad():
    threading.Thread(target=run_health_server, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    c.API_URL = 'https://fapi.binance.com/fapi/v1'
    
    palanca, monedas = 5, ['DOGEUSDC', 'SOLUSDC', 'XRPUSDC', 'ETHUSDC']
    comision, descanso_seg, stop_loss = 0.001, 30, -4.0

    print("🚀 ALE IA QUANTUM - MOTOR DE ALTA VELOCIDAD")

    while True:
        try:
            acc = c.futures_account()
            disponible = float(next((b['availableBalance'] for b in acc['assets'] if b['asset'] == 'USDC'), 0.0))
            
            # Verificar posiciones actuales
            pos = c.futures_position_information()
            activas = [p for p in pos if float(p.get('positionAmt', 0)) != 0]
            
            # LÓGICA SECUENCIAL: Si hay una operación, el buscador se apaga
            if len(activas) > 0:
                print(f"⏳ Operación en curso... Radar apagado.", end='\r')
                time.sleep(5)
                continue

            # Si llegamos aquí, no hay operaciones: REVISAR DESCANSO DE 30S
            # (El código anterior ya hizo el sleep al cerrar, así que buscamos)
            
            for m in monedas:
                k = c.futures_klines(symbol=m, interval='1m', limit=30)
                cl = [float(x[4]) for x in k]
                e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                p_act = cl[-1]

                if (p_act > e9 > e27) or (p_act < e9 < e27):
                    side_in = SIDE_BUY if p_act > e9 else SIDE_SELL
                    
                    # Cálculo de cantidad para 5 USDC mínimo
                    monto_op = disponible * 0.90 if (disponible * 0.20 * palanca) < 5.1 else disponible * 0.20
                    cant = round((monto_op * palanca) / p_act, 1 if m != 'DOGEUSDC' else 0)
                    
                    if (cant * p_act) >= 5.0:
                        c.futures_change_leverage(symbol=m, leverage=palanca)
                        order = c.futures_create_order(symbol=m, side=side_in, type=ORDER_TYPE_MARKET, quantity=cant)
                        print(f"\n🎯 ENGANCHE: {m} | Iniciando vigilancia ultra-rápida...")
                        
                        # LANZAR VIGILANTE EN HILO APARTE
                        threading.Thread(
                            target=vigilante_ultra_rapido,
                            args=(c, m, ("LONG" if side_in==SIDE_BUY else "SHORT"), p_act, cant, palanca, comision, stop_loss),
                            daemon=True
                        ).start()
                        
                        # Esperar a que la operación termine antes de buscar otra
                        # Monitoreamos hasta que len(activas) sea 0 de nuevo
                        while True:
                            check = c.futures_position_information()
                            if not any(float(p.get('positionAmt', 0)) != 0 for p in check):
                                print(f"\n✅ Operación terminada. Iniciando descanso de {descanso_seg}s...")
                                for i in range(descanso_seg, 0, -1):
                                    print(f"⏳ Descanso: {i}s...", end='\r')
                                    time.sleep(1)
                                break
                            time.sleep(2)
                        break # Salir del buscador de monedas

        except Exception as e:
            print(f"⚠️ Error en motor principal: {e}")
            time.sleep(5)

if __name__ == "__main__":
    bot_quantum_ultra_velocidad()
