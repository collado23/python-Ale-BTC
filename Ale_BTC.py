import time
import os

# CONFIGURACIÓN ALE IA QUANTUM  
ENTRADA = 0.80
PALANCA = 10
STOP_EMERGENCIA = -0.8  # Cierra si entra mal
COMPUESTO = 0.20

def programa_principal():
    saldo = ENTRADA
    vela = 0
    # CREAR EL ARCHIVO TXT SI NO EXISTE
    if not os.path.exists("analisis_ale.txt"):
        with open("analisis_ale.txt", "w") as f:
            f.write("--- INICIO DE INGENIERÍA SOL ---\n")

    print("🔱 PROGRAMA ACTIVO - ESPERANDO ADN 4 AÑOS")

    while True:
        # Simulamos lectura de mercado (Aquí va tu ADN)
        roi = 0.5 # Ejemplo de ROI
        
        # Lógica de Finanzas y Cierre
        volumen = saldo * PALANCA
        ganancia_neta = (volumen * (roi / 100)) - (volumen * 0.002)
        
        status = "OPERANDO"
        if roi <= STOP_EMERGENCIA:
            status = "🚨 CIERRE POR ERROR"
            saldo += ganancia_neta # Resta la pérdida
        elif roi > 0:
            status = "✅ GANANCIA"
            saldo += (ganancia_neta * COMPUESTO)

        vela += 1
        
        # ESCRIBIR AL TXT
        with open("analisis_ale.txt", "a") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] VELA: {vela} | STATUS: {status} | SALDO: ${saldo:.4f}\n")
        
        print(f"✅ Vela {vela} escrita en TXT. Saldo: ${saldo:.4f}")
        time.sleep(60)

if __name__ == "__main__":
    programa_principal()
