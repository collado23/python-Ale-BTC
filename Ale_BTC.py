import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === CONFIGURACIÓN DE RESETEO ($30) ===
cap_inicial = 30.00
ganado = 0.00
perdido = 0.00
ops_ganadas = 0
ops_perdidas = 0
ops_totales = 0
en_op = False
lista_precios = [] # Para guardar el detalle de las 5 ops

def mostrar_reporte_pantalla():
    """Muestra el reporte visual para la captura de pantalla del celular"""
    global lista_precios
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    
    print("\n" + "█"*50)
    print(f"📥 REPORTE PARA CAPTURA | {ts}")
    print("█" + " " * 48 + "█")
    print(f"  🔢 OPERACIONES TOTALES: {ops_totales}")
    print(f"  ✅ GANADAS: {ops_ganadas} (+${ganado:.4f})")
    print(f"  ❌ PERDIDAS: {ops_perdidas} (-${perdido:.4f})")
    print(f"  💰 BALANCE NETO: ${neto:.4f}")
    print(f"  💵 CAPITAL FINAL: ${cap_inicial + neto:.2f}")
    print("█" + " " * 48 + "█")
    print("  📝 DETALLE DE LAS ÚLTIMAS 5:")
    for p in lista_precios:
        print(f"  • {p}")
    print("█"*50 + "\n")
    
    # Limpiamos la lista para las próximas 5
    lista_precios = []

def registrar_evento(tipo_cierre, roi_n, res_plata, t_op, p_entrada, p_salida):
    global ops_totales, ganado, perdido, ops_ganadas, ops_perdidas, lista_precios
    
    ops_totales += 1
    simbolo = "✅" if res_plata > 0 else "❌"
    
    # Guardamos el detalle para el reporte
    detalle = f"{simbolo} {t_op} | ROI: {roi_n:.2f}% | ${res_plata:.4f}"
    lista_precios.append(detalle)

    if res_plata > 0:
        ganado += res_plata
        ops_ganadas += 1
    else:
        perdido += abs(res_plata)
        ops_perdidas += 1
    
    # Cada 5 operaciones, mostramos el cuadro para la foto
    if ops_totales % 5 == 0:
        mostrar_reporte_pantalla()

print(f"🚀 AMETRALLADORA INICIADA - REPORTE VISUAL CADA 5 OPS")

while ops_totales < 1000:
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=5)
        
        def get_color(k): return "VERDE 🟢" if float(k[4]) > float(k[1]) else "ROJA 🔴"
        v1, v2 = get_color(klines[-2]), get_color(klines[-3])
        
        # Elasticidad disparo rápido
        klines_ema = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
        ema = sum([float(k[4]) for k in klines_ema]) / 10
        elasticidad = abs(((ema - sol) / sol) * 100)
        
        if not en_op:
            # Tablero de espera (más simple para no ensuciar)
            print(f"⏱️ Ops: {ops_totales} | SOL: ${sol} | Dist: {elasticidad:.3f}% | Velas: {v2}+{v1}", end='\r')
            
            if v1 == v2 and elasticidad >= 0.015:
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "SHORT 🔴" if "VERDE" in v1 else "LONG 🟢"
        
        else:
            diff = ((sol - p_ent) / p_ent) if "LONG" in t_op else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20
            if roi_neto > max_roi: max_roi = roi_neto
            
            # Cierre rápido
            if (max_roi >= 0.30 and roi_neto <= (max_roi - 0.10)) or roi_neto <= -0.65:
                res = (30.0 * (roi_neto / 100))
                registrar_evento("CIERRE", roi_neto, res, t_op, p_ent, sol)
                en_op = False

        time.sleep(10)
    except Exception as e:
        time.sleep(5)
