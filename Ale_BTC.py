import os, time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN DIRECTA ===
def conectar():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

client = conectar()

# === MEMORIA QUANTUM ($30.76 base) ===
cap_base = 30.76
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_nison_veloz(k1, k2):
    """Análisis ultra rápido de patrones de 1 min"""
    op, hi, lo, cl = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cuerpo = abs(cl - op) if abs(cl - op) > 0 else 0.001
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    
    # Datos vela previa para Envolvente
    op_p, cl_p = float(k2[1]), float(k2[4])
    cuerpo_p = abs(cl_p - op_p)

    # MARTILLO (Gatillo rápido)
    if m_inf > (cuerpo * 2.8) and m_sup < (cuerpo * 0.6): return "MARTILLO 🔨"
    if m_sup > (cuerpo * 2.8) and m_inf < (cuerpo * 0.6): return "M_INVERTIDO ⚒️"
    if cl > op and cl_p < op_p and cuerpo > (cuerpo_p * 1.1): return "ENVOLVENTE 🌊"
    return "Normal"

def cuadro_reporte_5():
    global historial_bloque
    neto = ganado - perdido
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n╔{'═'*55}╗")
    print(f"║ 🔱 REPORTE SNIPER RÁPIDO | {ts}                    ║")
    print(f"║ TOTAL: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} | 💰 NETO: ${neto:.4f}  ║")
    print(f"║ 💵 SALDO ACTUAL: ${cap_base + neto:.2f}                         ║")
    print(f"╠{'═'*55}╣")
    for h in historial_bloque: print(f"║ • {h:<51} ║")
    print(f"╚{'═'*55}╝\n")
    historial_bloque.clear()

print("🚀 AMETRALLADORA CARGADA - ENTRADA RÁPIDA (1m/15s)")

while True:
    try:
        # 1. CAPTURA DE DATOS AL INSTANTE
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        k = client.get_klines(symbol='SOLUSDT', interval='1m', limit=3)
        
        patron = libro_nison_veloz(k[-1], k[-2])
        precio_cierre_v1 = float(k[-1][4])
        v2_roja = float(k[-2][4]) < float(k[-2][1])

        if not en_op:
            # Mostramos rastro de escaneo para que veas que está vivo
            print(f"📡 SCAN: {patron} | SOL: {sol} | {datetime.now().strftime('%S')}s", end='\r')
            
            # 2. GATILLO ULTRA-RÁPIDO
            if patron != "Normal" and v2_roja:
                # Si el precio ya supera el cierre anterior, dispara sin dudar
                if sol > precio_cierre_v1:
                    p_ent, en_op, t_op, p_al_entrar = sol, True, "LONG", patron
                    max_roi, break_even_listo = -99.0, False
                    print(f"\n⚡ DISPARO INSTANTÁNEO: {t_op} | {p_al_entrar} a {p_ent}")
        
        else:
            # 3. MONITOREO DE SALIDA (Fuerza Bruta)
            diff = (sol - p_ent) / p_ent if t_op == "LONG" else (p_ent - sol) / p_ent
            roi = (diff * 100 * 10) - 0.22 
            if roi > max_roi: max_roi = roi
            
            # Break Even (Protección Nison)
            if roi >= 0.28: break_even_listo = True
            
            # Cierres
            if break_even_listo and roi <= 0.04:
                res, motivo = (cap_base * (roi / 100)), "🛡️ BREAK EVEN"
                en_op = False
            elif (max_roi >= 0.45 and roi <= (max_roi - 0.12)) or roi <= -0.65:
                res, motivo = (cap_base * (roi / 100)), p_al_entrar
                en_op = False
                
            if not en_op:
                ops_totales += 1
                if res > 0: ganado += res; ops_ganadas += 1; ico = "✅"
                else: perdido += abs(res); ops_perdidas += 1; ico = "❌"
                historial_bloque.append(f"{ico} {roi:>5.2f}% | {motivo}")
                if ops_totales % 5 == 0: cuadro_reporte_5()

        # 4. SINCRONIZACIÓN DE 15 SEGUNDOS (Tu regla)
        time.sleep(15)

    except Exception as e:
        time.sleep(5)
        client = conectar()
