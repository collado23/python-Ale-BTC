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

# --- 🧠 MEMORIA ESPECIALIZADA POR MONEDA ---
def gestionar_memoria(leer=False, datos=None):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            csv.writer(f).writerow(['fecha', 'hora', 'moneda', 'roi', 'res', 'dist_ema_open', 'duracion_min'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            cap_actual = cap_inicial + (cap_inicial * (df['roi'].sum() / 100))
            
            # --- 🕵️ ANALIZADOR INDIVIDUAL ---
            # Diccionario para guardar qué horas bloquear por cada moneda
            bloqueos_por_moneda = {m: [] for m in ms}
            
            if len(df) > 5:
                df['h_solo'] = pd.to_datetime(df['hora']).dt.hour
                for moneda in ms:
                    m_data = df[df['moneda'] == moneda]
                    if not m_data.empty:
                        stats = m_data.groupby('h_solo')['roi'].mean()
                        # Si en esa hora esa moneda específica pierde, se bloquea
                        bloqueos_por_moneda[moneda] = stats[stats < -0.15].index.tolist()
            
            zonas_prohibidas = df[df['res'] == "LOSS"]['dist_ema_open'].tail(30).tolist()
            modo = "⚔️ GENERAL" if cap_actual >= 15.50 else "🛡️ INFANTERÍA"
            
            return cap_actual, modo, zonas_prohibidas, bloqueos_por_moneda
        except: return cap_inicial, "⚔️ GENERAL", [], {m: [] for m in ms}
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            csv.writer(f).writerow([time.strftime('%Y-%m-%d'), time.strftime('%H:%M:%S'), datos['m'], datos['roi'], datos['res'], datos.get('dist', 0), datos.get('duracion', 0)])

# --- ♟️ ANALIZADOR TÁCTICO INDIVIDUAL ---
def analizar_tablero(m, zonas_prohibidas, horas_negras_m):
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

        # Reloj de desbloqueo individual
        mins_para_libre = 60 - ahora.minute
        
        # ¿Esta moneda específica está bloqueada a esta hora?
        esta_bloqueada = h_actual in horas_negras_m
        
        # EXCEPCIÓN: Si la oportunidad es perfecta (Racha 4/4 y mucho volumen)
        permiso = racha >= 4 and v_mult > 3.8 and dist > 0.12

        if esta_bloqueada and not permiso:
            return f"⏳ {m} BLOQUEADA ({mins_para_libre} min)"

        for zona in zonas_prohibidas:
            if abs(dist - zona) < 0.004: return None

        return {'v_mult': v_mult, 'dist': dist, 'c': v['c'], 'e9': ema9, 'e27': ema27, 'racha': racha, 'permiso': permiso}
    except: return None

# --- 🚀 BUCLE DE CONSCIENCIA POR MONEDA ---
st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'x': 10, 'be': False, 'adn': {}, 'inicio': 0} for m in ms}
capital, modo, zonas_prohibidas, bloqueos_m = gestionar_memoria(leer=True)

print(f"🧠 V69: ESPECIALISTA POR MONEDA | CAP: ${capital:.2f}")

while True:
    try:
        for m in ms:
            s = st[m]
            # Pasamos solo las horas negras de esta moneda
            res_ana = analizar_tablero(m, zonas_prohibidas, bloqueos_m[m])
            
            if isinstance(res_ana, str):
                # Imprime el estado de cada moneda por separado
                print(f"[{modo}] {res_ana} | Historial: {len(bloqueos_m[m])} horas feas", end='\r')
                continue
            
            tab = res_ana
            if not tab: continue
            
            if not s['e']:
                if tab['dist'] > 0.082 and tab['v_mult'] > 2.7:
                    if tab['c'] > tab['e9'] > tab['e27'] and tab['racha'] >= 3: s['t'] = "LONG"
                    elif tab['c'] < tab['e9'] < tab['e27'] and tab['racha'] >= 3: s['t'] = "SHORT"
                    
                    if s['t']:
                        if tab.get('permiso'): print(f"\n💎 OPORTUNIDAD ÚNICA EN {m} (Saltando bloqueo)")
                        s.update({'e': True, 'p': tab['c'], 'x': 15, 'max': tab['c'], 'be': False, 'adn': tab, 'inicio': time.time()})
                        print(f"\n⚔️ {m} ATACANDO | Dist: {tab['dist']} | Racha: {tab['racha']}/4")
            else:
                # GESTIÓN DE SALIDA
                px = float(cl.get_symbol_ticker(symbol=m)['price'])
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * s['x']) - 0.26
                s['max'] = max(s['max'], px) if s['t'] == "LONG" else (min(s['max'], px) if s['max']>0 else px)
                retro = abs(s['max'] - px) / s['p'] * 100 * s['x']
                
                # Cierre por cruce de EMAs (Análisis rápido)
                k_c = cl.get_klines(symbol=m, interval='1m', limit=5)
                df_c = pd.DataFrame(k_c).astype(float)
                e9_c = df_c[4].ewm(span=9).mean().iloc[-1]
                e27_c = df_c[4].ewm(span=27).mean().iloc[-1]
                cruce = (s['t'] == "LONG" and e9_c < e27_c) or (s['t'] == "SHORT" and e9_c > e27_c)

                if roi > 0.40 and not s['be']: s['be'] = True; print(f"\n🔒 {m} ASEGURADA")

                if (roi > 0.55 and retro > 0.18) or (s['be'] and roi < 0.05) or roi <= -1.25 or cruce:
                    res = "WIN" if roi > 0 else "LOSS"
                    capital += (capital * (roi / 100))
                    gestionar_memoria(datos={'m': m, 'roi': round(roi, 2), 'res': res, 'dist': s['adn']['dist'], 'duracion': int((time.time()-s['inicio'])/60)})
                    print(f"\n🏁 CIERRE {m}: {res} | ROI: {roi:.2f}% | Nuevo Cap: ${capital:.2f}")
                    s['e'], s['t'] = False, ''
                    capital, modo, zonas_prohibidas, bloqueos_m = gestionar_memoria(leer=True)

        time.sleep(0.5)
    except: time.sleep(2)
