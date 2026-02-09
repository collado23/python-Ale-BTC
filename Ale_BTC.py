import os, time, pandas as pd
import numpy as np
from binance.client import Client

# --- CONFIGURACIÓN DE PRUEBA RÁPIDA ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = "BTCUSDT"
leverage = 10
capital_percent = 0.02  # Mantenemos el 2% para seguridad

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

def ejecutar_gladiador_veloz():
    print(f"🔱 SIMULACIÓN ULTRA-RÁPIDA (1 MIN) - {symbol}")
    
    while True:
        try:
            # CAMBIO A 1 MINUTO (interval='1m')
            klines = client.futures_klines(symbol=symbol, interval='1m', limit=100)
            df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','ct','q','n','tb','tq','i'])
            df[['high','low','close']] = df[['high','low','close']].astype(float)
            
            precio = df['close'].iloc[-1]
            # EMA 20 en 1 minuto reacciona al instante
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            adx_val = calcular_adx(df)
            
            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0
            balance = float(client.futures_account_balance()[1]['balance'])
            distancia = ((precio - ema_20) / ema_20) * 100

            # 🔱 LÓGICA DE GIRO INSTANTÁNEO
            if amt == 0:
                if precio < ema_20:
                    qty = round((balance * capital_percent * leverage) / precio, 3)
                    client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=qty)
                    print(f"📉 [1m] ENTRADA SHORT")
                elif precio > ema_20:
                    qty = round((balance * capital_percent * leverage) / precio, 3)
                    client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty)
                    print(f"🚀 [1m] ENTRADA LONG")

            elif amt < 0 and precio > ema_20: # GIRO A LONG
                client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=abs(amt))
                qty = round((balance * capital_percent * leverage) / precio, 3)
                client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty)
                print(f"🔄 [1m] GIRO RÁPIDO A LONG")

            elif amt > 0 and precio < ema_20: # GIRO A SHORT
                client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=abs(amt))
                qty = round((balance * capital_percent * leverage) / precio, 3)
                client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=qty)
                print(f"🔄 [1m] GIRO RÁPIDO A SHORT")

            print(f"⏱️ 1min | Precio: {precio:.1f} | EMA20: {ema_20:.1f} | Dist: {distancia:.2f}%")
            time.sleep(10) # Revisamos cada 10 segundos para no perder el movimiento

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    ejecutar_gladiador_veloz()
