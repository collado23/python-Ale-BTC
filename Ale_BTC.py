import os, time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ULTRA-LIGERA ===
def conectar():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

client = conectar()

# === CONFIGURACIÓN $30.76 ===
cap_base = 30.76
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_nison_1min(k1, k2):
    """Análisis de velas de 1 minuto"""
    op, hi, lo, cl = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cuerpo = abs(cl - op) if abs(cl - op) > 0 else 0.001
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    color = "V" if cl > op else "R"
    
    # Vela anterior para Envolvente
    op_p, cl_p = float(k2[1]), float(k2[4])
    cuerpo_p = abs(cl_p - op_p)
    color_p = "V" if cl_p > op_p else "R"

    # Martillos (Mecha 3x cuerpo) o Envolvente
    if m_inf > (cuerpo * 3) and m_sup < (cuerpo * 0.5): return "MARTILLO 🔨"
    if m_sup > (cuerpo * 3) and m_inf < (cuerpo * 0.5): return "M_INVERTIDO ⚒️"
    if color == "V" and color_p == "R" and cuerpo > (cuerpo_p * 1.2): return "ENVOLVENTE 🌊"
    return "Normal"

print("🚀 SNIPER 1 MINUTO ACTIVADO - BREAK EVEN & NISON")

while True:
    try:
        t = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(t['price'])
        # Pedimos velas de 1 minuto ('1m')
        k = client.get_klines(symbol='SOLUSDT', interval='1m', limit=5)
        
        patron = libro_nison_1min(k[-1], k[-2])
        precio_cierre_anterior = float(k[-1][4])
        v1, v2 = ("V" if float(k[-1][4]) > float(k[-1][1]) else "R"), ("R" if float(k[-2][4]) < float(k[-2][1]) else "V")

        if not en_op:
            print(f"🔍 [1m] {datetime.now().strftime('%H:%M:%S')} | {patron} | SOL: {sol}", end='\r')
            # Gatillo tras caída (v2 roja) y confirmación de subida
            if patron != "Normal" and v2 == "R":
                if sol > precio_cierre_anterior:
                    p_ent, en_op, t_op, p_al_entrar = sol, True, "LONG", patron
                    max_roi, break_even_listo = -99.0, False
                    print(f"\n🎯 DISPARO EN 1m: {t_op} | {p_al_entrar} a {p_ent}")
        
        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi = (diff * 100 * 10) - 0.22 
            if roi > max_roi: max_roi = roi
            
            # --- BREAK EVEN (PROTECCIÓN DE 1 MINUTO) ---
            if roi >= 0.30: break_even_listo = True
            
            # Cierre seguro o normal
            if break_even_listo and roi <= 0.05:
                res, motivo = (cap_base * (roi / 100)), "🛡️ BREAK EVEN"
                en_op = False
            elif (max_roi >= 0.45 and roi <= (max_roi - 0.12)) or roi <= -0.70:
                res, motivo = (cap_base * (roi / 100)), p_al_entrar
                en_op = False
                
            if not en_op:
                ops_totales += 1
                if res > 0: ganado += res; ops_ganadas += 1; ico = "✅"
                else: perdido += abs(res); ops_perdidas += 1; ico = "❌"
                historial_bloque.append(f"{ico} {roi:>5.2f}% | {motivo}")
                if ops_totales % 5 == 0:
                    print(f"\n📊 REPORTE 5 OPS: NETO ${ganado-perdido:.4f} | G:{ops_ganadas} P:{ops_perdidas}")
                    historial_bloque.clear()

        time.sleep(15) # Sincronización obligatoria cada 15 seg

    except Exception as e:
        time.sleep(15)
        client = conectar()
