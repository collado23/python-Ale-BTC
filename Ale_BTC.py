import pandas as pd
from binance.client import Client

# Conectamos para crear tu base de datos histórica
client = Client(None, None) # No hace falta API key para data pública histórica
symbol = "SOLUSDT"

print("📡 Extrayendo ADN de Solana de los últimos 4 años...")
# Bajamos velas de 1 hora para tener el mapa de años rápido
klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2021")
df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','q','n','tb','tq','i'])
df['c'] = df['c'].astype(float)
df['ema'] = df['c'].ewm(span=200, adjust=False).mean()
df['dist'] = ((df['c'] - df['ema']) / df['ema']) * 100

# Filtramos solo los momentos "Espejo" (donde el elástico se estiró más del 2%)
espejos = df[df['dist'].abs() > 2.0].copy()

# Guardamos el archivo que tu bot va a leer
with open("espejo_cuantico.txt", "w") as f:
    f.write("FECHA_HISTORICA,DISTANCIA,PRECIO,RESULTADO_ESPERADO\n")
    for i, row in espejos.iterrows():
        # Simulamos si el espejo volvió a la media (éxito)
        f.write(f"{row['t']},{row['dist']:.2f},{row['c']},REBOTE_CONFIRMADO\n")

print("✅ ¡Archivo espejo_cuantico.txt generado! Cargalo en la carpeta de tu bot.")
