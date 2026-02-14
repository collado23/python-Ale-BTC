import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 📖 LIBRERÍA "EL LIBRO COMPLETO" (Price Action) ---
def reconocer_patron_maestro(df):
    v = df.iloc[-2]      # Vela actual
    v_ant = df.iloc[-3]  # Vela anterior
    cuerpo = abs(v['c'] - v['o'])
    m_sup = v['h'] - max(v['c'], v['o'])
    m_inf = min(v['c'], v['o']) - v['l']
    rango = v['h'] - v['l'] if (v['h'] - v['l']) > 0 else 0.001

    # 🟢 PATRONES DE SUBIDA (LONG)
    martillo = m_inf > (cuerpo * 2.5) and m_sup < (cuerpo * 0.5)
    martillo_inv = m_sup > (cuerpo * 2.5) and m_inf < (cuerpo * 0.5)
    envolvente_alcista = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
    piercing = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > (v_ant['o'] + v_ant['c'])/2
    tres_soldados = v['c'] > v_ant['c'] and v_ant['c'] > df.iloc[-4]['c'] # 3 velas verdes seguidas
    
    # 🔴 PATRONES DE BAJADA (SHORT)
    estrella_fugaz = m_sup > (cuerpo * 2.5) and m_inf < (cuerpo * 0.5)
    colgado = m_inf > (cuerpo * 2.5) and m_sup < (cuerpo * 0.5)
    envolvente_bajista = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']
    nube_oscura = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < (v_ant['o'] + v_ant['c'])/2
    cuervos = v['c'] < v_ant['c'] and v_ant['c'] < df.iloc[-4]['c'] # 3 velas rojas seguidas

    # Veredicto
    if martillo or martillo_inv or envolvente_alcista or piercing or tres_soldados: return "ALCISTA"
    if estrella_fugaz or colgado or envolvente_bajista or nube_oscura or cuervos: return "BAJISTA"
    return "NEUTRAL"

# --- 📊 ANALISTA TOTAL (EMAs + RSI + VELAS + VOLUMEN) ---
def analista_superior(simbolo, cliente):
    try:
        # Traemos velas de 1m pero sincronizado a 15s
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=50)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        # 1. EMAs (Tendencia anterior)
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema21 = df['c'].ewm(span=21).mean().iloc[-1]
        
        # 2. RSI (Niveles de sobrecompra/venta)
        delta = df['c'].diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).mean() / -delta.where(delta < 0, 0).mean())))
        
        # 3. VOLUMEN (Confirmación de plata real)
        vol_avg = df['v'].rolling(15).mean().iloc[-1]
        vol_act = df['v'].iloc[-1]

        # 4. EL LIBRO DE VELAS (Price Action)
        patron = reconocer_patron_maestro(df)

        # 🎯 FILTRO INTELIGENTE: Tiene que coincidir TODO
        if patron == "ALCISTA" and rsi < 40 and ema9 > ema21 and vol_act > vol_avg:
            return True, "LONG", patron
        
        if patron == "BAJISTA" and rsi > 60 and ema9 < ema21 and vol_act > vol_avg:
            return True, "SHORT", patron

        return False, None, rsi
    except: return False, None, 50

# --- 🚀 BUCLE MAESTRO (Latido de 15 segundos) ---
while True:
    inicio = time.time()
    # Ejecuta analista_superior() para buscar entradas
    # Sigue calculando las X dinámicas (5x a 15x) si va en G
    # Muestra los cierres detallados con ROI y X finales
    
    # Sincronización perfecta con Binance
    time.sleep(max(0, 15 - (time.time() - inicio)))
