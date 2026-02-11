import os
import time
from datetime import datetime
from binance.client import Client

# === INICIO SEGURO ===
def conectar():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

client = conectar()

# === MEMORIA (Basada en tus $30.76) ===
cap_base = 30.76
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_velas_sniper(k):
    """Detecta solo Martillos potentes para evitar el 'anclaje' en pérdidas"""
    op, hi, lo, cl = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    cuerpo = abs(cl - op)
    if cuerpo == 0: cuerpo = 0.001
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    # Martillo: Mecha inferior 3 veces el cuerpo y poca mecha superior
    if m_inf > (cuerpo * 3) and m_sup < (cuerpo * 0.5): return "MARTILLO 🔨⚡"
    if m_sup > (cuerpo * 3) and m_inf < (cuerpo * 0.5): return "ESTRELLA ☄️"
    return "Normal"

def mostrar_cuadro_5():
    global historial_bloque
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*60 + "╗")
    print(f"║ 🔱 REPORTE QUANTUM SNIPER | {ts}              ║")
    print(f"║ 📊 OPS: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} | 💰 NETO: ${neto:.4f} ║")
    print("╠" + "═"*60 + "╣")
    for h in historial_bloque: print(f"║ • {h} ║")
    print("╚" + "═"*60 + "╝\n")
    historial_bloque.clear()

# --- FASE 1: ADN DE 20 VELAS ---
print("📡 Analizando ADN de 20 velas antes de empezar...")
try:
    k_ini = client.get_klines(symbol='SOLUSDT', interval='1m', limit=20)
    print(f"✅ ADN Cargado. Buscando Martillos en SOL...")
except:
    print("⚠️ Error inicial, reintentando conexión...")

# --- BUCLE INFINITO REFORZADO ---
while True:
    try:
        # Consultamos precio y velas actuales
        t = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(t['price'])
        k = client.get_klines(symbol='SOLUSDT', interval='1m', limit=5)
        
        patron = libro_velas_sniper(k[-1])
        v1 = "V" if float(k[-1][4]) > float(k[-1][1]) else "R"

        if not en_op:
            print(f"🔍 Escaneando... Vela: {patron} | Precio: {sol}", end='\r')
            
            # GATILLO: Martillo en vela roja o Estrella en vela verde
            if patron == "MARTILLO 🔨⚡" and v1 == "R":
                p_ent, en_op, t_op, p_al_entrar = sol, True, "LONG", patron
                max_roi = -99.0
                print(f"\n🚀 DISPARO SNIPER: {t_op} a {p_ent}")
            elif patron == "ESTRELLA ☄️" and v1 == "V":
                p_ent, en_op, t_op, p_al_entrar = sol, True, "SHORT", patron
                max_roi = -99.0
                print(f"\n🚀 DISPARO SNIPER: {t_op} a {p_ent}")
        
        else:
            # Lógica de salida para asegurar el centavo
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.22 
            if roi_neto > max_roi: max_roi = roi_neto
            
            # Cierre: Take Profit o Stop Loss corto
            if (max_roi >= 0.40 and roi_neto <= (max_roi - 0.12)) or roi_neto <= -0.75:
                res = (cap_base * (roi_neto / 100))
                ops_totales += 1
                if res > 0: 
                    ganado += res; ops_ganadas += 1; ico = "✅"
                else: 
                    perdido += abs(res); ops_perdidas += 1; ico = "❌"
                
                historial_bloque.append(f"{ico} {t_op:5} | ROI:{roi_neto:>5.2f}% | {p_al_entrar}")
                if ops_totales % 5 == 0: mostrar_cuadro_5()
                en_op = False

        time.sleep(4) # Escaneo cada 4 segundos para que no se ancle

    except Exception as e:
        print(f"\n⚠️ Re-conectando por error: {e}")
        time.sleep(10)
        client = conectar() # Reset de conexión
