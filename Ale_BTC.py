import time
import os

# === INGENIERÍA ALE IA QUANTUM === 
ENTRADA = 0.80           # Tu capital de entrada
PALANCA = 10             # x10
COMPUESTO = 0.20         # 20% de interés compuesto
STOP_EMERGENCIA = -0.8   # Protección: cierra si el elástico falla

def programa_principal(): 
    saldo = ENTRADA
    vela = 0
    archivo_log = "analisis_ale.txt"
    
    if not os.path.exists(archivo_log):
        with open(archivo_log, "w") as f:
            f.write("--- INICIO DE INGENIERÍA ALE IA QUANTUM ---\n")

    print(f"🔱 PROGRAMA ACTIVO - ENTRADA ${ENTRADA} x10")

    while True:
        try:
            # Simulación ADN 4 años
            roi = 0.95  
            volumen = saldo * PALANCA
            comision = volumen * 0.002
            ganancia_neta = (volumen * (roi / 100)) - comision
            
            status = "ANALIZANDO"
            if roi <= STOP_EMERGENCIA:
                status = "🚨 CIERRE POR ERROR"
                saldo += ganancia_neta 
            elif roi > 0:
                status = "✅ GANANCIA"
                saldo += (ganancia_neta * COMPUESTO)

            vela += 1
            
            with open(archivo_log, "a") as f:
                f.write(f"\n[{time.strftime('%H:%M:%S')}] VELA: {vela} | STATUS: {status}")
                f.write(f"\n💵 CAPITAL: ${saldo:.4f} | NETO: ${ganancia_neta:.4f}")
                f.write(f"\n--------------------------------------------\n")
            
            print(f"✅ Vela {vela} escrita en TXT. Saldo: ${saldo:.4f}")
            time.sleep(60)
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    programa_principal()
