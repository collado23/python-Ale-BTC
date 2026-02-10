import time

# === CONFIGURACIÓN DE INGENIERÍA SOL (ENTRADA 80 CENTAVOS) === 
CAPITAL_ENTRADA = 0.80         # Tu capital de entrada: 80 centavos
APALANCAMIENTO = 10            # x10 (Movés $8 USD totales)
INTERES_COMPUESTO_FACTOR = 0.20 # 20% de la ganancia se suma al capital
STOP_EMERGENCIA = -0.8         # Tu stop de seguridad
TIEMPO_VELA = 60               # Velas de 1 minuto

# Variables de seguimiento
capital_actualizado = CAPITAL_ENTRADA
contador_velas = 0

def calcular_resultado_exacto(roi_mercado):
    global capital_actualizado
    
    # El volumen que movés en Binance es capital * palanca
    volumen_operacion = capital_actualizado * APALANCAMIENTO
    
    # Ganancia bruta
    ganancia_bruta = volumen_operacion * (roi_mercado / 100)
    
    # Comisiones (Binance cobra sobre el volumen de $8, aprox 0.016 USD)
    comisiones = volumen_operacion * 0.002
    
    ganancia_neta = ganancia_bruta - comisiones
    return ganancia_neta

def ejecutar_sol_80cts():
    global capital_actualizado, contador_velas
    
    print(f"🔱 --- INGENIERÍA SOL: ENTRADA ${CAPITAL_ENTRADA} USD (x10) ---")
    
    while True:
        # --- SIMULACIÓN DE VELA (1 MINUTO) ---
        roi_mercado = 1.0  # Supongamos que SOL sube 1%
        
        resultado_plata = calcular_resultado_exacto(roi_mercado)
        
        # INTERÉS COMPUESTO: Sumamos el 20% de la ganancia a tus 80 centavos
        if resultado_plata > 0:
            capital_actualizado += (resultado_plata * INTERES_COMPUESTO_FACTOR)
            
        contador_velas += 1
        
        # --- VOLCADO AL TXT ---
        with open("analisis_sol_80cts.txt", "a") as f:
            f.write(f"\n--- LOG SOL 1min [{time.strftime('%H:%M:%S')}] ---")
            f.write(f"\n💵 Capital de Entrada: ${capital_actualizado:.4f} USD")
            f.write(f"\n🚀 Poder en Mercado (x10): ${(capital_actualizado * APALANCAMIENTO):.2f} USD")
            f.write(f"\n📈 ROI Mercado: {roi_mercado}%")
            f.write(f"\n💰 GANANCIA NETA: ${resultado_plata:.4f} USD")
            f.write(f"\n🕯️ Vela: {contador_velas} | Estado: Analizando Espejo")
            f.write(f"\n--------------------------------------------\n")

        print(f"✅ Minuto {contador_velas}: Capital ahora es ${capital_actualizado:.4f}")

        time.sleep(TIEMPO_VELA)

if __name__ == "__main__":
    ejecutar_sol_80cts()
