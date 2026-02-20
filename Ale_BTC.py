import os, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer  
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🚀 2. MOTOR V143 ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # El bot toma las llaves directo de las variables de Railway
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    ops = []
    
    # --- 💰 COMANDO PARA PEDIR SALDO A BINANCE ---
    def obtener_saldo_real():
        try:
            # Pide balances de la billetera de FUTUROS
            res = c.futures_account_balance()
            # Busca específicamente USDC (o cámbialo a USDT si es tu caso)
            for b in res:
                if b['asset'] == 'USDC':
                    return float(b['balance'])
            return 0.0
        except Exception as e:
            print(f"⚠️ Error leyendo saldo de Binance: {e}")
            return 0.0

    # Inicializa el capital con lo que hay en la cuenta
    cap = obtener_saldo_real()
    print(f"🎯 V143 FRANCOTIRADOR | SALDO REAL: ${cap:.2f} | STOP -1.6 | SALTO 2.5")

    while True:
        t_l = time.time()
        try:
            # 1. GESTIÓN DE OPERACIÓN ABIERTA
            for o in ops[:]:
                p_a = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                
                roi_bruto = diff * 100 * o['x']
                roi_n = roi_bruto - 0.9 
                
                # 🔥 SALTO A 15X (ROI 2.5% NETO)
                if roi_n >= 2.5 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True; o['piso'] = 2.0
                    try: c.futures_change_leverage(symbol=o['s'], leverage=15)
                    except: pass
                    print(f"\n🔥 SALTO 15X REALIZADO EN {o['s']}")

                # 🪜 ESCALADOR DINÁMICO (+0.5)
                if o['be']:
                    nuevo_piso = roi_n - 0.5
                    if nuevo_piso > o['piso']:
                        o['piso'] = nuevo_piso

                # 📉 CIERRE
                check_cierre = o['piso'] if o['be'] else -1.6
                if roi_n >= 10.0 or roi_n <= check_cierre:
                    # Al cerrar, esperamos un toque y pedimos el saldo real actualizado
                    time.sleep(2)
                    cap = obtener_saldo_real()
                    ops.remove(o)
                    print(f"\n✅ CIERRE EN {o['s']} | NETO: {roi_n:.2f}% | NUEVO SALDO: ${cap:.2f}")

            # 2. ENTRADA (E9/E27)
            if len(ops) < 1:
                # Monedas a vigilar
                for m in ['SOLUSDC', 'XRPUSDC', 'BNBUSDC', 'BTCUSDC']:
                    k = c.futures_klines(symbol=m, interval='1m', limit=50)
                    cl, op_v = float(k[-2][4]), float(k[-2][1]) 
                    
                    k_full = [float(x[4]) for x in k]
                    e9, e27 = sum(k_full[-9:])/9, sum(k_full[-27:])/27
                    
                    p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                    
                    # Gatillo original de las 9:27
                    if cl > op_v and cl > e9 and e9 > e27: # LONG
                        ops.append({'s':m,'l':'LONG','p':p_act,'x':5,'be':False, 'piso': -1.6})
                        print(f"\n🎯 DISPARO LONG: {m} | CAPITAL: ${cap:.2f}")
                        break
                    if cl < op_v and cl < e9 and e9 < e27: # SHORT
                        ops.append({'s':m,'l':'SHORT','p':p_act,'x':5,'be':False, 'piso': -1.6})
                        print(f"\n🎯 DISPARO SHORT: {m} | CAPITAL: ${cap:.2f}")
                        break

            # MONITOR DE CONSOLA
            if len(ops) > 0:
                print(f"💰 ${cap:.2f} | ROI: {roi_n:.2f}% | PISO: {check_cierre:.2f}% | {time.strftime('%H:%M:%S')}   ", end='\r')
            else:
                # Si no hay op, actualiza el saldo cada tanto por si metes plata manual
                if int(time.time()) % 60 == 0: cap = obtener_saldo_real()
                print(f"💰 ${cap:.2f} | Acechando entrada... | {time.strftime('%H:%M:%S')}   ", end='\r')
            
        except Exception as e:
            time.sleep(5)
        
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": 
    bot()
