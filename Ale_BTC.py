import os
import time
import socket
from datetime import datetime, timedelta
from binance.client import Client

# === 1. CONFIGURACIÓN DE LLAVES ===
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# === 2. PARÁMETROS DE ESTRATEGIA (SIMULACIÓN) ===
CAPITAL_INICIAL = 30.00
capital_actual = 30.00
distancia_gatillo = 2.0
media_200_fija = 84.34
op_ganadas = 0
op_perdidas = 0
inicio_sesion = datetime.now()

# === 3. LLAVE DE SEGURIDAD (Para no trabar Railway) ===
def esperar_red():
    print("⏳ Verificando red en Railway... No cortes el proceso.")
    while True:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            print("✅ RED DETECTADA. Conectando a Binance...")
            return True
        except:
            time.sleep(5)

# === 4. INICIO DEL MOTOR ===
esperar_red()
try:
    client = Client(API_KEY, API_SECRET)
    print("✅ CONEXIÓN EXITOSA CON BINANCE API")
except Exception as e:
    print(f"❌ ERROR API: {e}")

# === 5. BUCLE DE ANÁLISIS CADA 15 SEGUNDOS ===
while True:
    try:
        # Obtener precio real
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        precio = float(ticker['price'])

        # Cálculo de Elástico
        if precio < media_200_fija:
            sentido = "LONG 🟢"
            distancia = ((media_200_fija - precio) / precio) * 100
        else:
            sentido = "SHORT 🔴"
            distancia = ((precio - media_200_fija) / precio) * 100

        # --- TABLERO EN PANTALLA ---
        tiempo_vikingo = str(datetime.now() - inicio_sesion).split('.')[0]
        
        print("\n" + "═"*50)
        print(f"🔱 ALE IA QUANTUM | ACTIVO: {tiempo_vikingo}")
        print(f"💰 CAPITAL: ${capital_actual:.2f} | NETO: ${capital_actual - 30:.2f}")
        print(f"✅ G: {op_ganadas} | ❌ P: {op_perdidas} | 🔄 OP: {op_ganadas+op_perdidas}")
        print("-" * 50)
        print(f"📈 PRECIO SOL: ${precio:.2f} | 📏 DISTANCIA: {distancia:.2f}%")
        print(f"📡 ADN DETECTA: {sentido}")
        print("🔍 ESCANEANDO CADA 15 SEGUNDOS...")
        print("═"*50)

        # Registro de Logs
        with open("analisis_ale.txt", "a") as f:
            f.write(f"\n[{datetime.now().strftime('%H:%M:%S')}] SOL: {precio} | DIST: {distancia:.2f}%")

        time.sleep(15)

    except Exception as e:
        print(f"⚠️ Reintentando conexión en 10s... ({e})")
        time.sleep(10)
