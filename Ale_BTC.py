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
    """Analiza la anatomía de la vela: Martillo, Estrella o Marubozu"""
    op, hi, lo, cl = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    cuerpo = abs(cl - op)
    mecha_sup = hi - max(op, cl)
    mecha_inf = min(op, cl) - lo
    total = hi - lo
    if total == 0: return "Doji"
    
    # Patrones de Reversión y Fuerza
    if mecha_inf > (cuerpo * 2) and mecha_sup < (cuerpo * 0.5): return "Martillo 🔨"
    if mecha_sup > (cuerpo * 2) and mecha_inf < (cuerpo * 0.5): return "Estrella ☄️"
    if cuerpo > (total * 0.85): return "Marubozu 💪"
    return "Normal"

# --- FASE CRÍTICA: ANÁLISIS DE LAS 20 VELAS PREVIAS ---
def fase_analisis_adn():
    print("📡 FASE 1: Leyendo ADN del mercado (Últimas 20 velas)...")
    klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=45)
    
    # 1. Calculamos elasticidad base de los últimos 20 minutos
    elasts = []
    for i in range(25, 45):
        ventana = klines[i-20:i]
        ema_v = sum([float(k[4]) for k in ventana]) / 20
        p_v = float(klines[i-1][4])
        elasts.append(abs(((ema_v - p_v) / p_v) * 100))
    e_base = sum(elasts) / len(elasts)
    
    # 2. Identificamos el patrón de velas en el historial
    ultimo_patron = libro_de_velas(klines[-1])
    print(f"✅ ADN FIJADO: Elasticidad {e_base:.4f}% | Patrón actual: {ultimo_patron}")
    return e_base

elast_base_fijada = fase_analisis_adn()

def mostrar_reporte_total():
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*65 + "╗")
    print(f"║ 🔱 REPORTE QUANTUM ADN 20V | {ts}              ║")
    print(f"║ 📊 TOTAL: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} | 💰 NETO: ${neto:.4f} ║")
    print("╠" + "═"*65 + "╣")
    for h in historial_bloque: print(f"║ • {h} ║")
    print("╚" + "═"*65 + "╝\n")
    historial_bloque.clear()

# --- BUCLE DE OPERACIÓN ---
while ops_totales < 1000:
    try:
        sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
        
        # Análisis de Racha (4V) y Tipo de Vela
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3, v4 = col(klines[-1]), col(klines[-2]), col(klines[-3]), col(klines[-4])
        patron_v1 = libro_de_velas(klines[-1])
        
        ema_v = sum([float(k[4]) for k in klines]) / 10
        elast_act = abs(((ema_v - sol) / sol) * 100)
        
        if not en_op:
            print(f"🔍 E_ACT:{elast_act:.3f}% | RACHA:{v4}{v3}{v2}{v1} | VELA:{patron_v1}", end='\r')
            
            # GATILLO: Racha de 4 o Patrón de Reversión + Elasticidad
            giro_confirmado = (v1 == "V" and patron_v1 == "Martillo 🔨") or (v1 == "R" and patron_v1 == "Estrella ☄️")
            
            if (v1 == v2 == v3 == v4 or giro_confirmado) and elast_act >= (elast_base_fijada * 0.95):
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "SHORT" if (v1 == "V" and not giro_confirmado) or (patron_v1 == "Estrella ☄️") else "LONG"
                e_al_entrar, p_al_entrar = elast_act, patron_v1
                print(f"\n🚀 DISPARO: {t_op} | Motivo: {p_al_entrar} | E: {e_al_entrar:.3f}%")
        
        else:
            # Trailing Stop para asegurar tus centavos (+0.01 / +0.02 netos)
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.22 # Descontando comisión Binance
            if roi_neto > max_roi: max_roi = roi_neto
            
            if (max_roi >= 0.35 and roi_neto <= (max_roi - 0.12)) or roi_neto <= -0.90:
                res = (cap_base * (roi_neto / 100))
                ops_totales += 1
                if res > 0: 
                    ganado += res
                    ops_ganadas += 1
                    icono = "✅"
                else: 
                    perdido += abs(res)
                    ops_perdidas += 1
                    icono = "❌"
                historial_bloque.append(f"{icono} {t_op:5} | ROI:{roi_neto:>5.2f}% | {p_al_entrar} | ${res:.4f}")
                if ops_totales % 5 == 0: mostrar_reporte_total()
                en_op = False
        time.sleep(6)
    except: time.sleep(5)
