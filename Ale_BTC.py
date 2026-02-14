import os, time, csv
import pandas as pd
import numpy as np
from datetime import datetime
from binance.client import Client

# --- CONEXIÓN ---
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()

# --- CONFIGURACIÓN ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv" 
cap_inicial = 16.54 

# --- 🧠 MEMORIA CON FILTRO HORARIO ---
def gestionar_memoria(leer=False, datos=None):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            csv.writer(f).writerow(['fecha', 'hora', 'moneda', 'roi', 'res', 'dist_ema_open', 'duracion_min'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            cap_actual = cap_inicial + (cap_inicial * (df['roi'].sum() / 100))
            
            # --- 🕵️ ANALIZADOR DE HORARIOS ---
            # Bloqueamos las horas donde el ROI promedio es negativo (si hay suficientes datos)
            horas_negras = []
            if len(df) > 10:
                df['hora_h'] = pd.to_datetime(df['fecha'] + ' ' + df['hora']).dt.hour
                stats_horas = df.groupby('hora_h')['roi'].mean()
                horas_negras = stats_horas[stats_horas < -0.2].index.tolist()
            
            zonas_prohibidas = df[df['res'] == "LOSS"]['dist_ema_open'].tail(20).tolist() if 'dist_ema_open' in df.columns else []
            blindaje = (df.iloc[-1]['res'] == "WIN") if len(df) > 0 else False
            modo = "⚔️ ESTRATEGA" if cap_actual >= 15.0 else "🛡️ RECLUTA"
            
            return cap_actual, modo, blindaje, zonas_prohibidas, horas_negras
        except: return cap_inicial, "⚔️ ESTRATEGA", False, [], []
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            csv.writer(f).writerow([
                time.strftime('%Y-%m-%d'), time.strftime('%H:%M:%S'), 
                datos['m'], datos['roi'], datos['res'], 
                datos.get('dist', 0), datos.get('duracion', 0)
            ])

# --- ♟️ ANALIZADOR TÁCTICO CON RELOJ ---
def analizar_tablero(m, zonas_prohibidas, horas_negras):
    hora_actual = datetime.now().hour
    if hora_actual in horas_negras:
        return None # "Memoria dice: En esta hora solemos perder, no opero."

    try:
        k = cl.get_klines(symbol=m, interval='1m', limit=50)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).astype(float)
        v = df.iloc[-1]
        
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        dist_actual = round(abs(ema9 - ema27) / ema27 * 100, 4)
        
        for zona in zonas_prohibidas:
            if abs(dist_actual - zona) < 0.005: return None 

        v_mult = v['v'] / df['v'].tail(20).mean()
        cuerpo = abs(v['c'] - v['o'])
        rechazo = (v['h'] - max(v['c'], v['o'])) if v['c'] > v['o'] else (min(v['c'], v['o']) - v['l'])
        pct_rechazo = round(rechazo / cuerpo, 2) if cuerpo > 0 else 1
        racha = (df['c'].tail(4) > df['o'].tail(4)).sum() if v['c'] > v['o'] else (df['c'].tail(4) < df['o'].tail(4)).sum()

        return {'v_mult': v_mult, 'dist': dist_actual, 'rechazo': pct_rechazo, 'c': v['c'], 'e9': ema9, 'e27': ema27, 'racha': racha}
    except: return None

# --- 🚀 BUCLE PRINCIPAL ---
st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'x': 10, 'be': False, 'adn': {}, 'inicio': 0} for m in ms}
capital, modo, blindaje, zonas_prohibidas, horas_negras = gestionar_memoria(leer=True)

print(f"🧠 V67: RELOJ MAESTRO ACTIVADO | CAP: ${capital:.2f}")
print(f"🚫 HORAS BLOQUEADAS POR HISTORIAL: {horas_negras}")

while True:
    try:
        for m in ms:
            s = st[m]
            tab = analizar_tablero(m, zonas_prohibidas if not s['e'] else None, horas_negras)
            if not tab: continue
            px = tab['c']
            
            if not s['e']:
                if tab['dist'] > 0.082 and tab['v_mult'] > 2.7 and tab['rechazo'] < 0.22:
                    if px > tab['e9'] > tab['e27'] and tab['racha'] >= 3: s['t'] = "LONG"
                    elif px < tab['e9'] < tab['e27'] and tab['racha'] >= 3: s['t'] = "SHORT"
                    
                    if s['t']:
                        s.update({'e': True, 'p': px, 'x': 15, 'max': px, 'be': False, 'adn': tab, 'inicio': time.time()})
                        print(f"\n⚔️ ATAQUE: {m} | Hora: {datetime.now().strftime('%H:%M')}")
            else:
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * s['x']) - 0.26
                s['max'] = max(s['max'], px) if s['t'] == "LONG" else (min(s['max'], px) if s['max']>0 else px)
                retro = abs(s['max'] - px) / s['p'] * 100 * s['x']
                minutos_transcurridos = int((time.time() - s['inicio']) / 60)

                if roi > (0.22 if blindaje else 0.45) and not s['be']:
                    s['be'] = True; print(f"\n🔒 POSICIÓN ASEGURADA")

                cruce_contra = (s['t'] == "LONG" and tab['e9'] < tab['e27']) or (s['t'] == "SHORT" and tab['e9'] > tab['e27'])

                if (roi > 0.55 and retro > 0.20) or (s['be'] and roi < 0.05) or roi <= -1.25 or cruce_contra:
                    res = "WIN" if roi > 0 else "LOSS"
                    capital += (capital * (roi / 100))
                    
                    gestionar_memoria(datos={'m': m, 'roi': round(roi, 2), 'res': res, 'dist': s['adn']['dist'], 'duracion': minutos_transcurridos})
                    
                    print(f"\n🏁 CIERRE EN {m}: {res} | Cap: ${capital:.2f}")
                    s['e'], s['t'] = False, ''
                    capital, modo, blindaje, zonas_prohibidas, horas_negras = gestionar_memoria(leer=True)

        time.sleep(0.5)
    except: time.sleep(2)
