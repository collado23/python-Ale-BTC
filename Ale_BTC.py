import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA Y SINCRONIZACIÓN ---
def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini
    # ... (mismo sistema de persistencia para tus $15.77) ...

# --- 📖 2. EL LIBRO DE VELAS JAPONESAS COMPLETO ---
def leer_libro_velas_completo(df):
    v = df.iloc[-2]      # Vela cerrada
    v_ant = df.iloc[-3]  # Vela previa
    cuerpo = abs(v['c'] - v['o'])
    mecha_sup = v['h'] - max(v['c'], v['o'])
    mecha_inf = min(v['c'], v['o']) - v['l']
    
    # --- IDENTIFICACIÓN DE PATRONES ---
    # Martillos (Hammer) y Hombre Colgado (Hanging Man)
    es_martillo = mecha_inf > (cuerpo * 2.2) and mecha_sup < (cuerpo * 0.5)
    
    # Martillos Invertidos y Estrella Fugaz (Shooting Star)
    es_invertido = mecha_sup > (cuerpo * 2.2) and mecha_inf < (cuerpo * 0.5)
    
    # Envolventes (Engulfing)
    es_envolvente_alcista = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
    es_envolvente_bajista = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']

    # Doji (Indecisión)
    es_doji = cuerpo < ( (v['h'] - v['l']) * 0.1 )

    return {
        "m": es_martillo, "mi": es_invertido, 
        "ea": es_envolvente_alcista, "eb": es_envolvente_bajista,
        "d": es_doji
    }

# --- 📊 3. ANALISTA INTEGRAL (EMAs + RSI + VELAS + VOLUMEN) ---
def analista_total(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=30)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        # Estrategias anteriores (No se saca nada)
        ema_corta = df['c'].ewm(span=9).mean().iloc[-1]
        ema_larga = df['c'].ewm(span=21).mean().iloc[-1]
        rsi = calcular_rsi(df) # Función estándar
        vol_avg = df['v'].rolling(10).mean().iloc[-1]
        vol_act = df['v'].iloc[-1]

        # El Libro de Velas
        libro = leer_libro_velas_completo(df)

        # 🎯 LÓGICA DE ENTRADA (Saber cuándo entrar y salir)
        # LONG: RSI bajo + EMA corta arriba + (Martillo o Envolvente)
        if rsi < 38 and ema_corta > ema_larga and (libro['m'] or libro['ea']):
            motivo = "MARTILLO" if libro['m'] else "ENVOLVENTE"
            return True, "LONG", motivo
        
        # SHORT: RSI alto + EMA corta abajo + (Estrella Fugaz o Envolvente Bajista)
        if rsi > 62 and ema_corta < ema_larga and (libro['mi'] or libro['eb']):
            motivo = "ESTRELLA_FUGAZ" if libro['mi'] else "ENVOLVENTE_BAJ"
            return True, "SHORT", motivo

        return False, None, rsi
    except: return False, None, 50

# --- 🚀 4. BUCLE MAESTRO (Sincronizado a 15 segundos) ---
while True:
    inicio_ciclo = time.time()
    client = Client() # Conexión real/test
    
    # ... (Manejo de operaciones y X dinámicas) ...
    
    # ⏱️ SINCRONIZACIÓN BINANCE (15 SEGUNDOS)
    tiempo_ejecucion = time.time() - inicio_ciclo
    espera = max(0, 15 - tiempo_ejecucion) 
    time.sleep(espera) # El bot espera exactamente lo necesario para cumplir los 15s
