import time
import os

# === CONFIGURACIÓN MAESTRA ===
ENTRADA_BASE = 0.80      
PALANCA = 10             
COMPUESTO = 0.20         
STOP_EMERGENCIA = -0.8   
MEDIA_200 = 145.20       

# Colores para la pantalla de Railway
VERDE = '\033[92m'
ROJO = '\033[91m'
AMARILLO = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

def iniciar_quantum():
    saldo = ENTRADA_BASE
    vela_count = 0
    archivo_log = "analisis_ale.txt"
    
    print(f"{CYAN}📡 Extrayendo ADN de Solana de los últimos 4 años...{RESET}")
    print(f"{CYAN}🔱 Iniciando Ingeniería de Inercia y ADX...{RESET}")

    while True:
        try:
            # --- FÍSICA DE VELA JAPONESA (60s) ---
            for s in range(60, 0, -1):
                if s % 15 == 0: 
                    print(f"⏳ Vela en desarrollo... {AMARILLO}{s}s restantes{RESET}")
                time.sleep(1)

            # --- CÁLCULOS DEL ADN DE 4 AÑOS (SIMULACIÓN FOTO 2) ---
            precio_sol = 87.67      
            adx_fuerza = 24.5       
            match_adn = 98.2        
            roi_actual = 0.18       # Cambiá esto a negativo para probar el Rojo
            distancia_btc = -0.00   
            
            volumen = saldo * PALANCA
            ganancia_neta = (volumen * (roi_actual / 100)) - (volumen * 0.002)
            
            # Definir color según el ROI
            color_roi = VERDE if roi_actual >= 0 else ROJO
            status = "⚖️ ELÁSTICO EN TENSIÓN" if adx_fuerza < 25 else "🚀 IMPULSO"

            # === FORMATO DE REPORTE (IDÉNTICO A FOTO 2) ===
            cuerpo_reporte = (
                f"\n=============================================="
                f"\n📡 ADN SOLANA 4 AÑOS | MATCH: {match_adn}%"
                f"\n=============================================="
                f"\n💰 SESIÓN: +0.00% | PROM/TRADE: +0.00%"
                f"\n📊 {status} | ROI ACTUAL: {color_roi}{roi_actual:+.2f}%{RESET}"
                f"\n📈 SOL: {precio_sol} ({color_roi}{roi_actual:+.2f}%{RESET}) | BTC Dist: {distancia_btc:.2f}%"
                f"\n=============================================="
                f"\n🔍 FISICA: ADX {adx_fuerza} | INERCIA OK | MEDIA 200: {MEDIA_200}"
                f"\n💵 CAPITAL: {VERDE}${saldo:.4f}{RESET} | NETO: {color_roi}${ganancia_neta:.4f}{RESET}"
                f"\n==============================================\n"
            )

            # 1. Escribir al TXT (Sin colores para que no se vea raro el archivo)
            reporte_limpio = cuerpo_reporte.replace(VERDE, "").replace(ROJO, "").replace(AMARILLO, "").replace(CYAN, "").replace(RESET, "")
            with open(archivo_log, "a") as f:
                f.write(reporte_limpio)
            
            # 2. Mostrar en pantalla con COLORES
            print(cuerpo_reporte)
            
            # Aplicar interés compuesto
            if roi_actual > 0:
                saldo += (ganancia_neta * COMPUESTO)
            elif roi_actual <= STOP_EMERGENCIA:
                print(f"{ROJO}🚨 CIERRE DE EMERGENCIA APLICADO{RESET}")
                saldo += ganancia_neta

            vela_count += 1

        except Exception as e:
            print(f"{ROJO}❌ Error: {e}{RESET}")
            time.sleep(10)

if __name__ == "__main__":
    iniciar_quantum()
