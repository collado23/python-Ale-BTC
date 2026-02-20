import os, time
from binance.client import Client
from binance.enums import *

# CONFIGURACIÓN DIRECTA
def bot():
    # Conexión limpia
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    c = Client(api_key, api_secret)
    
    lista_m = os.getenv("MONEDAS", "SOLUSDC,XRPUSDC,BNBUSDC").split(",") 
    p_inv = float(os.getenv("PORCENTAJE_INVERSION", 0.80))
    sl_val = float(os.getenv("STOP_LOSS", -2.5))
    
    ops = []
    bloqueadas = {}
    
    print("🚀 MOTOR HULK ACTIVADO - SIN FRENOS")

    while True:
        try:
            # 1. BUSCAR POSICIÓN ABIERTA (CADA 2 SEGUNDOS)
            if not ops:
                pos = c.futures_position_information()
                for p in pos:
                    amt = float(p['positionAmt'])
                    if amt != 0:
                        ops.append({'s': p['symbol'], 'l': "LONG" if amt > 0 else "SHORT", 'p': float(p['entryPrice']), 'q': abs(amt), 'x': int(p['leverage']), 'be': False, 'piso': sl_val})
                        print(f"✅ DENTRO DE: {p['symbol']}")

            # 2. GESTIÓN DE LA OPERACIÓN
            for o in ops[:]:
                p_act = float(c.futures_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_act - o['p']) / o['p'] if o['l'] == "LONG" else (o['p'] - p_act) / o['p']
                roi = (diff * 100 * o['x']) - 0.8
                
                # SALTO 15X REAL
                if roi >= 1.5 and not o['be']: 
                    try:
                        c.futures_change_leverage(symbol=o['s'], leverage=15)
                        o['x'], o['be'], o['piso'] = 15, True, 1.0
                        print("🚀 15X REAL EN BINANCE")
                    except: o['be'] = True

                # ESCALADOR (EL QUE ASEGURA GUITA)
                if o['be']:
                    if roi >= 30.0: o['piso'] = 28.5
                    elif roi >= 20.0: o['piso'] = 18.5
                    elif roi >= 10.0: o['piso'] = 8.5
                    elif roi >= 5.0: o['piso'] = 4.0
                    elif roi >= 2.0: o['piso'] = 1.5

                # CIERRE AUTOMÁTICO
                check = o['piso'] if o['be'] else sl_val
                if roi < check:
                    side = SIDE_SELL if o['l'] == "LONG" else SIDE_BUY
                    c.futures_create_order(symbol=o['s'], side=side, type=ORDER_TYPE_MARKET, quantity=o['q'])
                    print(f"💰 CERRADO CON {roi:.2f}%")
                    bloqueadas[o['s']] = time.time() + 60
                    ops.remove(o)

            # 3. BUSCADOR DE ENTRADAS (SI NO HAY NADA ABIERTO)
            if not ops:
                for m in lista_m:
                    if m in bloqueadas and time.time() < bloqueadas[m]: continue
                    
                    k = c.futures_klines(symbol=m, interval='1m', limit=5)
                    if float(k[-1][4]) > float(k[-1][1]): # Vela actual verde
                        bal = c.futures_account_balance()
                        saldo = float(next(b for b in bal if b['asset'] == 'USDC')['balance'])
                        c.futures_change_leverage(symbol=m, leverage=5)
                        p_act = float(c.futures_symbol_ticker(symbol=m)['price'])
                        cant = round(((saldo * p_inv) * 5) / p_act, 1)
                        if cant > 0:
                            c.futures_create_order(symbol=m, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=cant)
                            print(f"🎯 COMPRADO: {m}")
                            break

            print("🔎...") # Log mínimo para saber que no murió
            time.sleep(2)

        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    bot()
