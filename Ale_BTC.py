import os, time, pandas as pd, numpy as np
from binance.client import Client

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = "SOLUSDT"
cantidad_prueba = 0.1  # Mínimo para testear
archivo_memoria = "memoria_gladiador.txt"
precio_extremo = None

def guardar_memoria_distancia(precio, dist, motivo):
    with open(archivo_memoria, "a") as f:
        log = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Precio: {precio} | Dist_EMA200: {dist:.2f}% | Motivo: {motivo}\n"
        f.write(log)
    print(f"📝 MEMORIA GUARDADA: {motivo} a {dist:.2f}% de distancia.")

def calcular_adx(df, period=14):
    df = df.copy()
    df['h-l'] = df['high'] - df['low']
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
    df['up'] = df['high'] - df['high'].shift(1)
    df['dn'] = df['low'].shift(1) - df['low']
    df['+dm'] = np.where((df['up'] > df['dn']) & (df['up'] > 0), df['up'], 0)
    df['-dm'] = np.where((df['dn'] > df['up']) & (df['dn'] > 0), df['dn'], 0)
    tr_smooth = df['tr'].rolling(window=period).sum()
    dm_plus_smooth = df['+dm'].rolling(window=period).sum()
    dm_minus_smooth = df['-dm'].rolling(window=period).sum()
    df['+di'] = 100 * (dm_plus_smooth / tr_smooth)
    df['-di'] = 100 * (dm_minus_smooth / tr_smooth)
    df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
    return df['dx'].rolling(window=period).mean().iloc[-1]

def ejecutar_gladiador_quantum():
    global precio_extremo
    print(f"🔱 GLADIADOR QUANTUM: LEYENDO DISTANCIAS Y VELAS...")
    
    while True:
        try:
            klines = client.futures_klines(symbol=symbol, interval='1m', limit=100)
            df = pd.DataFrame(klines, columns=['t','open','high','low','close','v','ct','q','n','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            
            # --- DATOS ACTUALES ---
            v = df.iloc[-1]
            precio = v['close']
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            adx_val = calcular_adx(df)
            dist_200 = abs(precio - ema_200) / ema_200 * 100

            # --- ANÁLISIS DE VELAS (PATRONES DE LIBRO) ---
            cuerpo = abs(v['close'] - v['open'])
            mecha_sup = v['high'] - max(v['open'], v['close'])
            mecha_inf = min(v['open'], v['close']) - v['low']
            martillo_inv = mecha_sup > (cuerpo * 2) and cuerpo > 0
            
            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0

            # --- LÓGICA DE ENTRADA INTELIGENTE ---
            if amt == 0:
                precio_extremo = None
                # Solo entramos si no estamos en el pico (Distancia < 1.2% y ADX < 45)
                if 30 < adx_val < 45 and dist_200 < 1.2:
                    if precio > (ema_20 * 1.002):
                        client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=cantidad_prueba)
                        guardar_memoria_distancia(precio, dist_200, "ENTRADA LONG")
                    elif precio < (ema_20 * 0.998):
                        client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=cantidad_prueba)
                        guardar_memoria_distancia(precio, dist_200, "ENTRADA SHORT")

            # --- CIERRE POR DISTANCIA O VELAS ---
            elif amt != 0:
                if precio_extremo is None: precio_extremo = precio
                
                if amt > 0: # LONG
                    if precio > precio_extremo: precio_extremo = precio
                    caida = (precio_extremo - precio) / precio_extremo * 100
                    # GATILLO: Si cae 0.6% O si hace el Martillo Invertido que dijiste arriba
                    if caida > 0.6 or (martillo_inv and dist_200 > 1.0):
                        client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=abs(amt))
                        guardar_memoria_distancia(precio, dist_200, f"CIERRE LONG (Gatillo Vela/Caída {caida:.2f}%)")

            print(f"📊 SOL: {precio:.2f} | ADX: {adx_val:.1f} | Dist: {dist_200:.2f}%")
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ Error: {e}"); time.sleep(10)

if __name__ == "__main__":
    ejecutar_gladiador_quantum()
