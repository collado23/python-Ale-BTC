import time
import os

# === INGENIERÍA ALE IA QUANTUM - SOL 1 MINUTO ===
CAPITAL_ENTRADA = 0.80   # Tus 80 centavos
PALANCA = 10             # x10
COMPUESTO = 0.20         # 20% reinversión
STOP_EMERGENCIA = -0.8   # Protección: Si baja de esto, CIERRA.

def iniciar():
    saldo = CAPITAL_ENTRADA
    vela = 0
    archivo_log = "analisis_ale.txt"
    
    print("🔱 ADN 4 AÑOS CARGADO - PROTECCIÓN DE ELÁSTICO ACTIVA")

    while True:
        try:
            # 1. Simulación de entrada ADN (Detectando el espejo)
            roi = 0.95  # Ejemplo de ganancia detectada
            
            # 2. Finanzas (80 centavos x 10)
            volumen = saldo * PALANCA
            comision = volumen * 0.002 # Comisión Binance
            ganancia_neta = (volumen * (roi / 100)) - comision
            
            # 3. Módulo de Cierre y Seguridad
            status = "ANALIZANDO"
            if roi <= STOP_EMERGENCIA:
                status = "🚨 CIERRE POR ERROR"
                saldo += ganancia_neta # Resta la pérdida pequeña
            elif roi > 0:
                status = "✅ GANANCIA"
                # Aplicamos el 20% de interés compuesto
                saldo += (ganancia_neta * COMPUESTO)

            vela += 1
            
            # 4. Volcado contable al TXT
            with open(archivo_log, "a") as f:
                f.write(f"\n--- REPORTE [{time.strftime('%H:%M:%S')}] ---")
                f.write(f"\n🕯️ VELA: {vela} | STATUS: {status}")
                f.write(f"\n💰 RESULTADO: ${ganancia_neta:.4f} | SALDO: ${saldo:.4f}")
                f.write(f"\n--------------------------------------------\n")
            
            print(f"✅ Vela {vela} escrita en TXT. Status: {status}")
            time.sleep(60) # 1 minuto exacto
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    iniciar()
