import time

# === CONFIGURACIÓN DE PODER ===
CAPITAL_OPERATIVO = 30.00
PALANCA = 10
MEDIA_200 = 145.20 # Este es el eje del elástico
MIN_GANANCIA = 2.0

def ejecutar_quantum_dual():
    global CAPITAL_OPERATIVO
    
    while True:
        # --- LÓGICA DE DETECCIÓN DE SENTIDO ---
        precio_sol = 83.51 # Precio actual
        
        if precio_sol < MEDIA_200:
            # ELÁSTICO ESTIRADO HACIA ABAJO
            sentido = "LONG (Compra) 🟢"
            distancia = MEDIA_200 - precio_sol
            proyeccion = (distancia / precio_sol) * 100
        else:
            # ELÁSTICO ESTIRADO HACIA ARRIBA
            sentido = "SHORT (Venta) 🔴"
            distancia = precio_sol - MEDIA_200
            proyeccion = (distancia / precio_sol) * 100

        # --- GATILLO DE ENTRADA (2% MÍNIMO) ---
        status = "🔍 ANALIZANDO MERCADO"
        if proyeccion >= MIN_GANANCIA:
            status = f"🚀 GATILLO: {sentido}"
            # Aquí entraría la lógica del Trailing Stop que ya armamos
        
        # --- REPORTE COMPLETO ---
        reporte = (
            "\n" + "═"*45 +
            f"\n📡 ADN CUÁNTICO | MODO: BIDIRECCIONAL"
            f"\n{ '🟢' if 'LONG' in sentido else '🔴' } DIRECCIÓN ESTIMADA: {sentido}"
            "\n" + "─"*45 +
            f"\n📊 STATUS: {status}"
            f"\n📈 PRECIO SOL: {precio_sol} | MEDIA 200: {MEDIA_200}"
            f"\n🎯 POTENCIAL ELÁSTICO: {proyeccion:.2f}%"
            f"\n💰 CAPITAL: ${CAPITAL_OPERATIVO:.2f} | APALANQUE: x10"
            "\n" + "═"*45
        )
        
        with open("analisis_ale.txt", "a") as f:
            f.write(reporte)
        
        print(reporte)
        time.sleep(60)

if __name__ == "__main__":
    ejecutar_quantum_dual()
