import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN SEGURA ===
def conectar():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

client = conectar()

# === CONFIGURACIÓN (Capital: $30.76) ===
cap_base = 30.76
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_velas_maestro(k_actual, k_previa):
    """Aplica las reglas de Steve Nison: Martillos y Envolventes"""
    # Vela Actual
    op, hi, lo, cl = float(k_actual[1]), float(k_actual[2]), float(k_actual[3]), float(k_actual[4])
    cuerpo = abs(cl - op) if abs(cl - op) > 0 else 0.001
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    color = "V" if cl > op else "R"

    # Vela Previa (Para Envolvente)
    op_p, cl_p = float(k_previa[1]), float(k_previa[4])
    cuerpo_p = abs(cl_p - op_p)
    color_p = "V" if cl_p > op_p else "R"

    # 1. MARTILLO (Hammer) 🔨 - Mecha 3x cuerpo
    if m_inf > (cuerpo * 3) and m_sup < (cuerpo * 0.5):
        return "MARTILLO 🔨"

    # 2. MARTILLO INVERTIDO ⚒️ - Mecha arriba 3x cuerpo
    if m_sup > (cuerpo * 3) and m_inf < (cuerpo * 0.5):
        return "M_INVERTIDO ⚒️"

    # 3. ENVOLVENTE VERDE (Bullish Engulfing) 🌊
    # Si la vela actual es verde, la anterior roja, y el cuerpo actual supera al anterior
    if color == "V" and color_p == "R" and cuerpo > (cuerpo_p * 1.2):
        return "ENVOLVENTE 🌊"

    return "Normal"

def mostrar_cuadro_5():
    global historial_bloque
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*60 + "╗")
    print(f"║ 🔱 REPORTE NISON SUPREMO | {ts}               ║")
    print(f"║ 📊 OPS: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} | 💰 NETO: ${neto:.4f} ║")
    print("╠" + "═"*60 + "╣")
    for h in historial_bloque: print(f"║ • {h} ║")
    print("╚" + "═"*60 + "╝\n")
    historial_bloque.clear()

# --- FASE 1: ADN 20 VELAS ---
print(f"📡 Iniciando... Sincro 15s | Reglas de Nison: Martillo + Envolvente")
try:
    client.get_klines(symbol='SOLUSDT', interval='1m', limit=20)
    print("✅ ADN Cargado. Buscando señales de giro...")
except: client = conectar()

# --- BUCLE PRINCIPAL ---
while True:
    try:
        t = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(t['price'])
        k = client.get_klines(symbol='SOLUSDT', interval='1m', limit=5)
        
        patron = libro_velas_maestro(k[-1], k[-2])
        cierre_v1 = float(k[-1][4])
        # Racha de 3 para asegurar contexto
        v1, v2, v3 = [("R" if float(x[4]) < float(x[1]) else "V") for x in k[-3:]]

        if not en_op:
            print(f"🔍 [{datetime.now().strftime('%H:%M:%S')}] Racha: {v3}{v2}{v1} | Señal: {patron}", end='\r')
            
            # GATILLO CON CONFIRMACIÓN
            if patron != "Normal" and v2 == "R":
                # Confirmación: Precio actual debe estar por encima del cierre anterior (Fuerza alcista)
                if sol > cierre_v1:
                    p_ent, en_op, t_op, p_al_entrar = sol, True, "LONG", patron
                    max_roi = -99.0
                    print(f"\n🚀 DISPARO NISON: {t_op} por {patron} a {p_ent}")
        
        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.22 
            if roi_neto > max_roi: max_roi = roi_neto
            
            # Salida táctica para asegurar centavos
            if (max_roi >= 0.45 and roi_neto <= (max_roi - 0.12)) or roi_neto <= -0.70:
                res = (cap_base * (roi_neto / 100))
                ops_totales += 1
                if res > 0: 
                    ganado += res; ops_ganadas += 1; ico = "✅"
                else: 
                    perdido += abs(res); ops_perdidas += 1; ico = "❌"
                
                historial_bloque.append(f"{ico} {t_op:5} | ROI:{roi_neto:>5.2f}% | {p_al_entrar}")
                if ops_totales % 5 == 0: mostrar_cuadro_5()
                en_op = False

        time.sleep(15) # Sincronización de 15 segundos obligatoria

    except Exception as e:
        time.sleep(15)
        client = conectar()
