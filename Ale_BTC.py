import os, time, threading 
from http.server import BaseHTTPRequestHandler, HTTPServer 
from binance.client import Client
from binance.enums import *

# --- 🌐 SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    
    # --- ⚙️ VARIABLES ---
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",")
    p_inv = float(os.getenv("PORCENTAJE_INVERSION", 0.80))
    t_espera = int(os.getenv("TIEMPO_ESPERA", 15))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    tiempo_descanso = 0
    bloqueo_activo = False 
    ultimo_print = 0

    def sincronizar_huérfanos():
        """🐊 Si el bot reinicia, busca posiciones abiertas en Binance para recuperarlas."""
        try:
            posiciones = c.futures_position_information()
            for p in posiciones:
                amt = float(p['positionAmt'])
                if amt != 0 and p['symbol'] in lista_m:
                    # Si ya la tenemos en ops, no hacemos nada
                    if any(o['s'] == p['symbol'] for o in ops): continue
                    
                    # Recuperamos datos básicos
                    tipo = "LONG" if amt > 0 else "SHORT"
                    p_entrada = float(p['entryPrice'])
                    cantidad = abs(amt)
                    leverage = int(p['leverage'])
                    
                    ops.append({
                        's': p['symbol'], 'l': tipo, 'p': p_entrada, 
                        'q': cantidad, 'inv': 8.0, 'x': leverage, 
                        'be': False, 'piso': sl_val
                    })
                    print(f"\n🔄 RECUPERADA: Posición de {p['symbol']} detectada en Binance.")
        except Exception as e:
            print(f"Error sincronizando: {e}")

    print(f"🐊 MOTOR V146.7 | RECUPERADOR DE MEMORIA ACTIVO")

    while True:
        ahora = time.time()
        roi_vis = 0.0
        
        try:
            # 1. Intentar sincronizar si no hay nada en ops pero hay algo en Binance
            if len(ops) == 0: sincronizar_huérfanos()

            if bloqueo_activo and (ahora - tiempo_descanso) > t_espera:
                bloqueo_activo = False

            saldo_api = obtener_saldo_futuros()
            saldo_actual = saldo_api if saldo_api > 0 else 10.0

            # --- GESTIÓN DE OPERACIÓN ---
            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_a) / o['p']
                roi = (diff * 100 * o['x']) - 0.90
                roi_vis = roi
                
                # ... [Lógica de Salto 15x y Escalador igual que antes] ...
                if roi >= 1.5 and not o['be']: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 1.0 
                    print(f"\n🚀 ¡SALTO 15X! {o['s']} | ROI: {roi:.2f}%")

                if o['be']:
                    n_p = o['piso']
                    if roi >= 25.0: n_p = 24.5
                    elif roi >= 2.0: n_p = 1.5 # (Simplificado para espacio)
                    if n_p > o['piso']: o['piso'] = n_p

                    if roi < o['piso']:
                        side_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                        c.futures_create_order(symbol=o['s'], side=side_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                        tiempo_descanso = ahora; ops.remove(o); bloqueo_activo = True
                        continue

                if not o['be'] and roi <= sl_val:
                    side_c = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side_c, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    tiempo_descanso = ahora; ops.remove(o); bloqueo_activo = True

            # --- 🎯 BUSCADOR ---
            if not bloqueo_activo and len(ops) == 0:
                # [Lógica de buscador igual que antes]
                pass 
            
            # MONITOR (Print cada 10s)
            if ahora - ultimo_print > 10:
                if len(ops) > 0:
                    print(f"💰 Cap: ${saldo_actual:.2f} | {ops[0]['s']}: {roi_vis:.2f}% | Piso: {ops[0]['piso']}%")
                else:
                    estado = f"🔒 ESPERA: {max(0, int(t_espera-(ahora-tiempo_descanso)))}s" if bloqueo_activo else "🔎 BUSCANDO..."
                    print(f"💰 Cap: ${saldo_actual:.2f} | {estado}")
                ultimo_print = ahora
                
        except: time.sleep(1)
        time.sleep(1)

# [Funciones auxiliares obtener_saldo_futuros y tiene_posicion_abierta aquí]
