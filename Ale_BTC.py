import os, time, csv, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pandas as pd
import numpy as np
from datetime import datetime
from binance.client import Client

# --- 🌐 SERVIDOR PARA QUE RAILWAY NO SE APAGUE ---
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><body><h1>Bot V70 Operando...</h1></body></html>", "utf-8"))

def run_web_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), WebServer)
    server.serve_forever()

# --- 🧠 LÓGICA DEL BOT (V69 Mejorada) ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv" 
cap_inicial = 16.54 

def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c()

def gestionar_memoria(leer=False, datos=None):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            csv.writer(f).writerow(['fecha', 'hora', 'moneda', 'roi', 'res', 'dist_ema_open', 'duracion_min'])
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            cap_actual = cap_inicial + (cap_inicial * (df['roi'].sum() / 100))
            bloqueos_m = {m: [] for m in ms}
            if len(df) > 5:
                df['h_solo'] = pd.to_datetime(df['hora']).dt.hour
                for moneda in ms:
                    m_data = df[df['moneda'] == moneda]
                    if not m_data.empty:
                        stats = m_data.groupby('h_solo')['roi'].mean()
                        bloqueos_m[moneda] = stats[stats < -0.15].index.tolist()
            return cap_actual, bloqueos_m
        except: return cap_inicial, {m: [] for m in ms}
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            csv.writer(f).writerow([time.strftime('%Y-%m-%d'), time.strftime('%H:%M:%S'), datos['m'], datos['roi'], datos['res'], datos.get('dist', 0), datos.get('duracion', 0)])

# --- 🚀 ARRANQUE CON HILO SECUNDARIO ---
# Lanzamos el servidor web en un hilo aparte para que Railway esté feliz
threading.Thread(target=run_web_server, daemon=True).start()

# --- BUCLE PRINCIPAL DEL BOT ---
st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'x': 10, 'be': False, 'adn': {}, 'inicio': 0} for m in ms}
capital, bloqueos_m = gestionar_memoria(leer=True)

print(f"✅ V70 RAILWAY READY | CAP: ${capital:.2f}")

while True:
    try:
        for m in ms:
            s = st[m]
            # (Aquí va toda la lógica de análisis V69 que ya teníamos)
            # Analizar tablero, entrar, gestionar salida...
            
            # AGREGAMOS UN PRINT PARA VER EL LOG EN RAILWAY
            if not s['e']:
                print(f"Vigilando {m}... | Cap: ${capital:.2f}", end='\r')
            
        time.sleep(2) # Aumentamos el sleep para evitar bloqueos de IP
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
