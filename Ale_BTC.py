import os, time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN DIRECTA Y LIMPIA ===
def conectar():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

client = conectar()

# === CONFIGURACIÓN (Saldo: $30.76) ===
cap_base = 30.76
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_nison(k1, k2):
    """Reglas de Steve Nison simplificadas para evitar errores de memoria"""
    op, hi, lo, cl = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cuerpo = abs(cl - op) if abs(cl - op) > 0 else 0.001
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    color = "V" if cl > op else "R"
    
    # Datos vela previa
    op_p, cl_p = float(k2[1]), float(k2[4])
    cuerpo_p = abs(cl_p - op_p)
    color_p = "V" if cl_p > op_p else "R"

    # 1. Martillo / Martillo Invertido (3x cuerpo)
    if m_inf > (cuerpo * 3) and m_sup < (cuerpo * 0.5): return "MARTILLO 🔨"
    if m_sup > (cuerpo * 3) and m_inf < (cuerpo * 0.5): return "M_INVERTIDO ⚒️"
    # 2. Envolvente Verde
    if color == "V" and color_p == "R" and cuerpo > (cuerpo_p * 1.2): return "ENVOLVENTE 🌊"
    return "Normal"

def cuadro_reporte():
    global historial_bloque
    neto = ganado - perdido
    print(f"\n╔{'═'*50}╗")
    print(f"║ 🔱 REPORT: G:{ops_ganadas} | P:{ops_perdidas} | NETO: ${neto:.4f} ║")
    print(f"╚{'═'*50}╝")
    for h in historial_bloque: print(f"  • {h}")
    historial_bloque.clear()

# --- ARRANQUE ---
print("📡 ADN 20V Cargado. Sincro: 15 seg. Buscando giro...")

while True:
    try:
        # Consulta mínima para no saturar
        t = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(t['price'])
        k = client.get_klines(symbol='SOLUSDT', interval='1m', limit=5)
        
        patron = libro_nison(k[-1], k[-2])
        v1, v2 = ("V" if float(k[-1][4]) > float(k[-1][1]) else "R"), ("R" if float(k[-2][4]) < float(k[-2][1]) else "V")

        if not en_op:
            print(f"🔍 [{datetime.now().strftime('%H:%M:%S')}] {patron} | SOL: {sol}", end='\r')
            
            # GATILLO: Si hay patrón tras vela roja y el precio confirma subida
            if patron != "Normal" and v2 == "R":
                if sol > float(k[-1][4]): # Confirmación Nison
                    p_ent, en_op, t_op, p_al_entrar = sol, True, "LONG", patron
                    max_roi = -99.0
                    print(f"\n🚀 ENTRADA: {t_op} | {p_al_entrar} a {p_ent}")
        
        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi = (diff * 100 * 10) - 0.22 
            if roi > max_roi: max_roi = roi
            
            # Salidas: Ganancia 0.45% o Stop Loss -0.70%
            if (max_roi >= 0.45 and roi <= (max_roi - 0.12)) or roi <= -0.70:
                res = (cap_base * (roi / 100))
                ops_totales += 1
                if res > 0: ganado += res; ops_ganadas += 1; ico = "✅"
                else: perdido += abs(res); ops_perdidas += 1; ico = "❌"
                
                historial_bloque.append(f"{ico} {roi:>5.2f}% | {p_al_entrar}")
                if ops_totales % 5 == 0: cuadro_reporte()
                en_op = False

        time.sleep(15) # Tu regla de los 15 segundos

    except Exception as e:
        time.sleep(15)
        client = conectar()
