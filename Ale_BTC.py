import os, time, pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN Y CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = "SOLUSDT"
leverage = 10
cantidad_prueba = 0.5 # Mantenemos cantidad fija para evitar errores de decimales

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

def ejecutar_gladiador_inteligente():
    print(f"🔱 GLADIADOR SOL: MODO SALIDA ANTICIPADA ACTIVADO")
    
    while True:
        try:
            klines = client.futures_klines(symbol=symbol, interval='1m', limit=100)
            df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','ct','q','n','tb','tq','i'])
            df[['high','low','close']] = df[['high','low','close']].astype(float)
            
            precio = df['close'].iloc[-1]
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            adx_val = calcular_adx(df)
            
            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0

            # --- LÓGICA DE PROTECCIÓN ---
            adx_debil = adx_val < 25 # Si baja de 25, la tendencia se agota

            # 1. SI NO HAY POSICIÓN: Solo entra con ADX fuerte (>30)
            if amt == 0:
                if adx_val > 30:
                    side = 'SELL' if precio < (ema_20 * 0.999) else 'BUY' if precio > (ema_20 * 1.001) else None
                    if side:
                        client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=cantidad_prueba)
                        print(f"🚀 ENTRADA FUERTE: {side} (ADX: {adx_val:.1f})")

            # 2. SI ESTAMOS EN SHORT
            elif amt < 0:
                # Cierre por cruce de EMA o porque la tendencia se murió (ADX débil)
                if precio > (ema_20 * 1.001) or adx_debil:
                    razon = "Giro EMA" if precio > ema_20 else "ADX Débil (Asegurando)"
                    client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=abs(amt))
                    print(f"⚠️ CIERRE SHORT: {razon} | ADX: {adx_val:.1f}")

            # 3. SI ESTAMOS EN LONG
            elif amt > 0:
                # Cierre por cruce de EMA o porque la tendencia se murió (ADX débil)
                if precio < (ema_20 * 0.999) or adx_debil:
                    razon = "Giro EMA" if precio < ema_20 else "ADX Débil (Asegurando)"
                    client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=abs(amt))
                    print(f"⚠️ CIERRE LONG: {razon} | ADX: {adx_val:.1f}")

            print(f"📊 MONITOR: SOL {precio:.2f} | EMA20 {ema_20:.2f} | ADX {adx_val:.1f}")
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    ejecutar_gladiador_inteligente()
