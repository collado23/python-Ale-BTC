import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === CONFIGURACIÓN (Capital según tu última captura: $28.77) ===
cap_base = 28.77
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_de_velas(k):
    op, hi, lo, cl = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    cuerpo = abs(cl - op)
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    total = hi - lo
    if total == 0: return "Normal"
    if m_inf > (cuerpo * 2.2): return "Martillo 🔨" # Filtro más estricto
    if m_sup > (cuerpo * 2.2): return "Estrella ☄️"
    return "Normal"

# --- FASE DE ANÁLISIS 20V ---
def analizar_inicio():
    print("📡 ESCANEANDO ADN (20 VELAS)...")
    klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=20)
    return klines

analizar_inicio()

def mostrar_reporte_total():
    """REPORTE PARA CAPTURA: GANADAS VS PERDIDAS"""
    global historial_bloque
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*65 + "╗")
    print(f"║ 🔱 REPORTE DE VICTORIAS | {ts}                   ║")
    print(f"║ 📊 TOTAL: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} | 💰 NETO: ${neto:.4f} ║")
    print(f"║ 💵 CAPITAL ACTUAL: ${cap_base + neto:.2f}                        ║")
    print("╠" + "═"*65 + "╣")
    for h in historial_bloque: print(f"║ • {h} ║")
    print("╚" + "═"*65 + "╝\n")
    historial_bloque.clear()

# --- BUCLE PRINCIPAL ---
while ops_totales < 1000:
    try:
        sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=6)
        
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3 = col(klines[-1]), col(klines[-2]), col(klines[-3])
        patron_v1 = libro_de_velas(klines[-1])
        
        if not en_op:
            print(f"🔍 BUSCANDO VICTORIA | RACHA: {v3}{v2}{v1} | VELA: {patron_v1}", end='\r')
            
            # SOLO ENTRA CON PATRÓN DE LIBRO CONFIRMADO
            # Martillo en roja = LONG | Estrella en verde = SHORT
            es_martillo = (v1 == "R" and patron_v1 == "Martillo 🔨")
            es_estrella = (v1 == "V" and patron_v1 == "Estrella ☄️")
            
            if es_martillo or es_estrella:
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "LONG" if es_martillo else "SHORT"
                p_al_entrar = patron_v1
                print(f"\n🚀 DISPARO ESTRATÉGICO: {t_op} | {p_al_entrar}")
        
        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.22 
            if roi_neto > max_roi: max_roi = roi_neto
            
            # --- CIERRES INTELIGENTES ---
            # 1. Take Profit con Trailing (dejamos que crezca a 0.50% antes de vigilar)
            if max_roi >= 0.50:
                if roi_neto <= (max_roi - 0.15): # Protege la subida
                    res = (cap_base * (roi_neto / 100))
                    en_op = False
            
            # 2. Stop Loss Corto (Cortamos la pérdida rápido si el Martillo falla)
            elif roi_neto <= -0.70:
                res = (cap_base * (roi_neto / 100))
                en_op = False
            
            if not en_op:
                ops_totales += 1
                if res > 0:
                    ganado += res; ops_ganadas += 1; ico = "✅"
                else:
                    perdido += abs(res); ops_perdidas += 1; ico = "❌"
                
                historial_bloque.append(f"{ico} {t_op:5} | ROI:{roi_neto:>5.2f}% | {p_al_entrar} | ${res:.4f}")
                if ops_totales % 5 == 0: mostrar_reporte_total()

        time.sleep(6)
    except: time.sleep(5)
