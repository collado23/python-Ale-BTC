import os, time, csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from binance.client import Client

# --- CONEXIÓN ---
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 

cl = c()

# --- CONFIGURACIÓN ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv" 
cap_inicial = 16.54 

# --- 🧠 MEMORIA CON INTELIGENCIA TEMPORAL ---
def gestionar_memoria(leer=False, datos=None):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            csv.writer(f).writerow(['fecha', 'hora', 'moneda', 'roi', 'res', 'dist_ema_open', 'duracion_min'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            cap_actual = cap_inicial + (cap_inicial * (df['roi'].sum() / 100))
            
            # Analizador de Horas Negras
            horas_negras = []
            if len(df) > 5:
                df['h_solo'] = pd.to_datetime(df['hora']).dt.hour
                stats = df.groupby('h_solo')['roi'].mean()
                horas_negras = stats[stats < -0.15].index.tolist()
            
            zonas_prohibidas = df[df['res'] == "LOSS"]['dist_ema_open'].tail(20).tolist() if 'dist_ema_open' in df.columns else []
            modo = "⚔️ GENERAL" if cap_actual >= 15.50 else "🛡️ INFANTERÍA"
            
            return cap_actual, modo, zonas_prohibidas, horas_negras
        except: return cap_inicial, "⚔️ GENERAL", [], []
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            csv.writer(f).writerow([time.strftime('%Y-%m-%d'), time.strftime('%H:%M:%S'), datos['m'], datos['roi'], datos['res'], datos.get('dist', 0), datos.get('duracion', 0)])

# --- ♟️ ANALIZADOR CON PERMISO ESPECIAL ---
def analizar_tablero(m, zonas_prohibidas, horas_negras):
    ahora = datetime.now()
    h_actual = ahora.hour
    
    try:
        k = cl.get_klines(symbol=m, interval='1m', limit=50)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).astype(float)
        v = df.iloc[-1]
        
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema27 = df['c'].ewm(span=27).mean().iloc[-1]
        dist = round(abs(ema9 - ema27) / ema27 * 100, 4)
        v_mult = v['v'] / df['v'].tail(20).mean()
        racha = (df['c'].tail(4) > df['o'].tail(4)).sum() if v['c'] > v['o'] else (df['c'].tail(4) < df['o'].tail(4)).sum()

        # --- 🕒 LÓGICA DEL RELOJ ---
        mins_para_desbloqueo = 60 - ahora.minute
        bloqueado = h_actual in horas_negras

        # --- 👑 EL PERMISO DEL GENERAL (Oportunidad 10/10) ---
        # Si la racha es perfecta (4/4) y el volumen es brutal (>3.5), ignoramos el bloqueo.
        permiso_especial = racha >= 4 and v_mult > 3.5 and dist > 0.12

        if bloqueado and not permiso_especial:
            return f"⏳ Bloqueado por {mins_para_desbloqueo} min"

        # Filtro de zonas prohibidas
        for zona in zonas_prohibidas:
            if abs(dist - zona) < 0.005: return None

        return {'v_mult': v_mult, 'dist': dist, 'c': v['c'], 'e9': ema9, 'e27': ema27, 'racha': racha, 'especial': permiso_especial}
    except: return None

# --- 🚀 BUCLE ---
st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'x': 10, 'be': False, 'adn': {}, 'inicio': 0} for m in ms}
capital, modo, zonas_prohibidas, horas_negras = gestionar_memoria(leer=True)

while True:
    try:
        for m in ms:
            s = st[m]
            res_ana = analizar_tablero(m, zonas_prohibidas, horas_negras)
            
            if isinstance(res_ana, str):
                print(f"[{modo}] {m}: {res_ana} | Cap: ${capital:.2f}", end='\r')
                continue
            
            tab = res_ana
            if not tab: continue
            px = tab['c']
            
            if not s['e']:
                # Solo entra si el análisis dio el OK
                if tab['dist'] > 0.082 and tab['v_mult'] > 2.7:
                    if px > tab['e9'] > tab['e27'] and tab['racha'] >= 3: s['t'] = "LONG"
                    elif px < tab['e9'] < tab['e27'] and tab['racha'] >= 3: s['t'] = "SHORT"
                    
                    if s['t']:
                        if tab.get('especial'): print(f"\n🚀 ¡PERMISO ESPECIAL! Oportunidad 10/10 en {m}")
                        s.update({'e': True, 'p': px, 'x': 15, 'max': px, 'be': False, 'adn': tab, 'inicio': time.time()})
                        print(f"\n⚔️ ATAQUE: {m} {s['t']} | Dist: {tab['dist']}")
            else:
                # GESTIÓN DE SALIDA (Aire y Cruce)
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * s['x']) - 0.26
                s['max'] = max(s['max'], px) if s['t'] == "LONG" else (min(s['max'], px) if s['max']>0 else px)
                retro = abs(s['max'] - px) / s['p'] * 100 * s['x']
                
                cruce = (s['t'] == "LONG" and tab['e9'] < tab['e27']) or (s['t'] == "SHORT" and tab['e9'] > tab['e27'])

                if roi > 0.40 and not s['be']: s['be'] = True; print(f"\n🔒 BLINDAJE")

                if (roi > 0.55 and retro > 0.20) or (s['be'] and roi < 0.05) or roi <= -1.25 or cruce:
                    res = "WIN" if roi > 0 else "LOSS"
                    capital += (capital * (roi / 100))
                    gestionar_memoria(datos={'m': m, 'roi': round(roi, 2), 'res': res, 'dist': s['adn']['dist'], 'duracion': int((time.time()-s['inicio'])/60)})
                    print(f"\n🏁 FIN: {res} | Cap: ${capital:.2f}")
                    s['e'], s['t'] = False, ''
                    capital, modo, zonas_prohibidas, horas_negras = gestionar_memoria(leer=True)

        time.sleep(0.5)
    except: time.sleep(2)
