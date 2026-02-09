import os, time, pandas as pd, numpy as np
from binance.client import Client

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = "SOLUSDT"
cantidad_prueba = 0.1  
archivo_memoria = "memoria_gladiador.txt"

# --- VARIABLES DE SEGUIMIENTO ---
precio_maximo_alcanzado = 0
posicion_abierta = False
ultimo_cierre_time = 0 

def guardar_en_memoria(precio, pnl, motivo):
    with open(archivo_memoria, "a") as f:
        log = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] P: {precio} | ROI: {pnl:.2f}% | {motivo}\n"
        f.write(log)
    print(f"✅ {motivo} | ROI FINAL: {pnl:.2f}%")

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

def ejecutar_gladiador_v6_1():
    global precio_maximo_alcanzado, posicion_abierta, ultimo_cierre_time
    print(f"🔱 GLADIADOR QUANTUM V6.1: FILTRO DE RUIDO Y API OPTIMIZADA")
    
    while True:
        try:
            # 1. Obtención de datos (1 sola llamada pesada)
            klines = client.futures_klines(symbol=symbol, interval='1m', limit=100)
            df = pd.DataFrame(klines, columns=['t','open','high','low','close','v','ct','q','n','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            
            v = df.iloc[-1]
            precio = v['close']
            adx_val = calcular_adx(df)
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            
            # Análisis de velas (Librería Japonesa)
            es_roja = v['close'] < v['open']
            es_verde = v['close'] > v['open']
            mecha_sup = v['high'] - max(v['open'], v['close'])
            mecha_inf = min(v['open'], v['close']) - v['low']
            cuerpo = abs(v['close'] - v['open'])

            # 2. Revisar posición
            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0
            pnl = 0

            # --- LÓGICA DE ENTRADA CON ENFRIAMIENTO ---
            # Esperamos 3 minutos entre trades para evitar el "ametrallamiento" de órdenes
            if amt == 0:
                posicion_abierta = False
                precio_maximo_alcanzado = 0
                
                if (time.time() - ultimo_cierre_time) > 180: # 180 seg = 3 min
                    if adx_val > 65:
                        if precio > ema_20 and es_roja and mecha_sup > (cuerpo * 1.5):
                            client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=cantidad_prueba)
                            print("📉 ENTRADA SHORT (GIRO)")
                        elif precio < ema_20 and es_verde and mecha_inf > (cuerpo * 1.5):
                            client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=cantidad_prueba)
                            print("🚀 ENTRADA LONG (GIRO)")

            # --- LÓGICA DE SEGUIMIENTO (TRAILING DINÁMICO) ---
            elif amt != 0:
                if not posicion_abierta:
                    posicion_abierta = True
                    precio_maximo_alcanzado = precio
                
                entrada = float(datos_pos['entryPrice'])
                pnl = ((precio - entrada) / entrada * 100) if amt > 0 else ((entrada - precio) / entrada * 100)

                if amt > 0: # Long
                    if precio > precio_maximo_alcanzado: precio_maximo_alcanzado = precio
                    retroceso = (precio_maximo_alcanzado - precio) / precio_maximo_alcanzado * 100
                else: # Short
                    if precio < precio_maximo_alcanzado: precio_maximo_alcanzado = precio
                    retroceso = (precio - precio_maximo_alcanzado) / precio_maximo_alcanzado * 100

                # --- FILTRO DE GANANCIA REAL ---
                # Si el ROI es menor a 0.3%, le damos aire (1.0%) para que no cierre en pérdida por ruido
                # Si ya ganamos más de 0.4%, el Trailing se vuelve agresivo (0.2%) para atrapar la punta
                if pnl > 0.4:
                    margen_vuelta = 0.2
                else:
                    margen_vuelta = 1.0 # Le damos aire para que corra
                
                if retroceso > margen_vuelta:
                    client.futures_create_order(symbol=symbol, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    ultimo_cierre_time = time.time()
                    guardar_en_memoria(precio, pnl, f"💰 CIERRE ESTRATÉGICO (ROI: {pnl:.2f}%)")

            print(f"📊 SOL: {precio:.2f} | ADX: {adx_val:.1f} | ROI: {pnl:.2f}% | Max: {precio_maximo_alcanzado}")
            
            # Aumentamos a 15 seg para evitar el baneo de IP de Railway (Error -1003)
            time.sleep(15) 

        except Exception as e:
            print(f"⚠️ API Info: {e}")
            time.sleep(40) # Respiro largo si hay error

if __name__ == "__main__":
    ejecutar_gladiador_v6_1()
