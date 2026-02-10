import os
import time
from datetime import datetime
from binance.client import Client

# === CONFIGURACIÓN Y APIS ===
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
client = Client(API_KEY, API_SECRET)

# === PARÁMETROS ADN ===
archivo_memoria = "memoria_quantum.txt"
espera_segundos = 11
palanca = 10

# === CONTADORES DE CAJA Y ANÁLISIS ===
capital_actual = 30.00
ganancia_hoy = 0.0    
perdida_hoy = 0.0     
contador_ops = 0      
neto_real = 0.0

def registrar_en_txt(tipo, mensaje, valor=0):
    global contador_ops, ganancia_hoy, perdida_hoy, neto_real
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(archivo_memoria, "a") as f:
        f.write(f"[{ts}] {tipo} | {mensaje}\n")
    
    if tipo == "CIERRE":
        contador_ops += 1
        if valor > 0: ganancia_hoy += valor
        else: perdida_hoy += abs(valor)
        neto_real = ganancia_hoy - perdida_hoy
        
        # --- DISPARADOR DE ANÁLISIS UNO ---
        if contador_ops % 20 == 0:
            resumen_analisis = (
                f"\n--- 🧠 ANÁLISIS UNO (Ciclo de 20 Ops) ---\n"
                f"Resultado Neto: ${neto_real:.2f}\n"
                f"Eficiencia: {'ALTA' if neto_real > 0 else 'BAJA - REVISANDO ADN'}\n"
                f"------------------------------------------\n"
            )
            with open(archivo_memoria, "a") as f:
                f.write(f"[{ts}] 🏁 {resumen_analisis}")
            print(f"🔱 EJECUTANDO ANÁLISIS UNO... Guardado en memoria.")

print(f"🚀 MOTOR 'ANÁLISIS UNO' ACTIVADO - CICLO {espera_segundos}s")

while True:
    try:
        # 1. Obtención de datos reales
        precio = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        # (Lógica de EMA, DX y Velas que ya integramos)
        ema = 83.50 # Ejemplo
        dx = 28.5
        v_verdes, v_rojas = 2, 1
        distancia_x = abs(((ema - precio) / precio) * 100)

        # --- EL CUADRO DE MANDO (Tu Pedido) ---
        print("\n" + "═"*55)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 CAP. ACTUAL: ${capital_actual:.2f} | 📈 NETO REAL: ${neto_real:.2f}")
        print(f"✅ GANANCIA HOY: +${ganancia_hoy:.2f} | ❌ PÉRDIDA HOY: -${perdida_hoy:.2f}")
        print("-" * 55)
        print(f"📏 DIST X: {distancia_x:.2f}% | ⚡ DX (ELEC): {dx}")
        print(f"🕯️ VELAS: {v_verdes}V / {v_rojas}R | 🧭 MEDIA: {ema}")
        print(f"🔢 CONTADOR OPS: {contador_ops} / 20 (Hacia Análisis Uno)")
        print("═"*55)

        # Lógica de Gatillo y Cierre (Dual: Alza/Baja)
        # ... (Ya integrado en el ADN anterior) ...

        time.sleep(espera_segundos)

    except Exception as e:
        time.sleep(espera_segundos)
