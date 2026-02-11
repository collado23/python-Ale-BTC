import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === CONFIGURACIÓN $30 ===
cap_base = 30.00
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_de_velas(k):
    """Identifica la anatomía de la vela para decidir la entrada"""
    op, hi, lo, cl = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    cuerpo = abs(cl - op)
    m_inf = min(op, cl) - lo
    m_sup = hi - max(op, cl)
    total = hi - lo
    
    if total == 0: return "Doji"
    # Patrones de Reversión (Libro)
    if m_inf > (cuerpo * 2): return "Martillo 🔨"  # Indica rebote al alza
    if m_sup > (cuerpo * 2): return "Estrella ☄️"  # Indica rebote a la baja
    if cuerpo > (total * 0.85): return "Marubozu 💪" # Indica fuerza extrema
    return "Normal"

# --- FASE 1: ANÁLISIS DE LAS 20 VELAS PREVIAS ---
def analizar_adn_velas():
    print("📡 LEYENDO EL LIBRO DE LAS ÚLTIMAS 20 VELAS...")
    klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=20)
    
    verdes = sum(1 for k in klines if float(k[4]) > float(k[1]))
    rojas = sum(1 for k in klines if float(k[4]) < float(k[1]))
    
    print(f"✅ ADN CARGADO: {rojas} Rojas y {verdes} Verdes en el historial.")
    return "BAJISTA" if rojas > verdes else "ALCISTA"

tendencia_dominante = analizar_adn_velas()

def mostrar_reporte_total():
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*65 + "╗")
    print(f"║ 🔱 REPORTE LIBRO DE VELAS | {ts}                   ║")
    print(f"║ 📊 TOTAL: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} | 💰 NETO: ${neto:.4f} ║")
    print("╠" + "═"*65 + "╣")
    for h in historial_bloque: print(f"║ • {h} ║")
    print("╚" + "═"*65 + "╝\n")
    historial_bloque.clear()

# --- BUCLE DE LA AMETRALLADORA ---
while ops_totales < 1000:
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=6)
        
        # Color y Patrón de las velas
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3, v4 = col(klines[-1]), col(klines[-2]), col(klines[-3]), col(klines[-4])
        patron_actual = libro_de_velas(klines[-1])
        
        if not en_op:
            print(f"🔍 BUSCANDO GIRO | RACHA: {v4}{v3}{v2}{v1} | VELA: {patron_actual}", end='\r')
            
            # GATILLO BASADO EN EL LIBRO Y RACHA (Sin elasticidad)
            # 1. Por Racha: 4 velas del mismo color
            # 2. Por Patrón: Racha de 2 + Vela de reversión (Martillo o Estrella)
            racha_completa = (v1 == v2 == v3 == v4)
            giro_por_libro = (v2 == "R" and patron_actual == "Martillo 🔨") or (v2 == "V" and patron_actual == "Estrella ☄️")
            
            if racha_completa or giro_por_libro:
                p_ent, en_op, max_roi = sol, True, -99.0
                # Si venía rojo, vamos en LONG. Si venía verde, vamos en SHORT.
                t_op = "LONG" if v1 == "R" or patron_actual == "Martillo 🔨" else "SHORT"
                p_al_entrar = patron_actual
                print(f"\n🚀 ENTRADA POR {p_al_entrar} | Tipo: {t_op} | Precio: {p_ent}")

        else:
            # Trailing Stop para capturar esos 1 o 2 centavos netos
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20 # X10 menos comisión
            
            if roi_neto > max_roi: max_roi = roi_neto
            
            # Cierre con beneficio real
            if max_roi >= 0.35 and roi_neto <= (max_roi - 0.12):
                res = (cap_base * (roi_neto / 100))
                en_op = False
            elif roi_neto <= -0.85: # Stop loss
                res = (cap_base * (roi_neto / 100))
                en_op = False
            
            if not en_op:
                ops_totales += 1
                if res > 0: 
                    ganado += res; ops_ganadas += 1; icono = "✅"
                else: 
                    perdido += abs(res); ops_perdidas += 1; icono = "❌"
                
                historial_bloque.append(f"{icono} {t_op:5} | ROI:{roi_neto:>5.2f}% | {p_al_entrar} | ${res:.4f}")
                if ops_totales % 5 == 0: mostrar_reporte_total()

        time.sleep(5)
    except: time.sleep(5)
