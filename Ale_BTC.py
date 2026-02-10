import time 

# === CONFIGURACIÓN DE PODER Y BILLETERA ===
CAPITAL_OPERATIVO = 30.00  # Tu capital real
INTERES_COMPUESTO = 0.20   # 20% se reinvierte
PALANCA = 10
GANANCIA_NETA_ACUMULADA = 0.0
MEDIA_200 = 145.20
STOP_DINAMICO = -0.8

def ejecutar_quantum_completo():
    global CAPITAL_OPERATIVO, GANANCIA_NETA_ACUMULADA, STOP_DINAMICO
    
    print(f"🚀 SISTEMA ACTIVADO | CAPITAL: ${CAPITAL_OPERATIVO} | MODO: SIMULACIÓN")

    while True:
        # --- (SIMULACIÓN DE DATOS EN TIEMPO REAL) ---
        precio_sol = 87.67      
        adx_fuerza = 26.8       
        match_adn = 98.2        
        distancia_200 = precio_sol - MEDIA_200
        proyeccion_rebote = 2.45  # El bot ve un 2.45% de potencial
        roi_actual = 1.80         # Supongamos que va ganando esto
        
        # --- LÓGICA DE INTERÉS COMPUESTO AL CERRAR ---
        # Solo ocurre cuando la operación termina (ejemplo simbólico)
        if roi_actual >= 2.0: 
            ganancia_bruta = (CAPITAL_OPERATIVO * PALANCA) * (roi_actual / 100)
            reinvierte = ganancia_bruta * INTERES_COMPUESTO
            bolsillo = ganancia_bruta - reinvierte
            
            CAPITAL_OPERATIVO += reinvierte
            GANANCIA_NETA_ACUMULADA += bolsillo
            print(f"✅ OPERACIÓN CERRADA: Reinvertido ${reinvierte:.2f} | Ganado ${bolsillo:.2f}")

        # --- EL REPORTE MAESTRO (CON TODO LO QUE PEDISTE) ---
        reporte = (
            "\n=============================================="
            f"\n📡 ADN SOLANA 4 AÑOS | MATCH: {match_adn}%"
            "\n=============================================="
            f"\n📊 STATUS: TRAILING ACTIVO | ROI: {roi_actual:+.2f}%"
            f"\n📈 SOL: {precio_sol} | DIST. 200: {distancia_200:.4f}"
            f"\n🎯 PROYEC. REBOTE: {proyeccion_rebote:.2f}% | ADX: {adx_fuerza}"
            "\n----------------------------------------------"
            f"\n🛡️  STOP DINÁMICO: {STOP_DINAMICO:+.2f}% | PICOS: 3/3"
            f"\n💰 CAPITAL OPERATIVO: ${CAPITAL_OPERATIVO:.2f}"
            f"\n💵 GANANCIA NETA TOTAL: ${GANANCIA_NETA_ACUMULADA:.2f}"
            "\n==============================================\n"
        )
        
        # Guardar en el archivo TXT para que lo veas en el gráfico
        with open("analisis_ale.txt", "a") as f:
            f.write(reporte)
        
        print(reporte)
        time.sleep(60) # Actualiza cada minuto (vela japonesa)

if __name__ == "__main__":
    ejecutar_quantum_completo()
