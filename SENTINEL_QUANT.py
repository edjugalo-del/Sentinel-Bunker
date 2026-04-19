import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from tradingview_ta import TA_Handler, Interval
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# --- 🛰️ CONFIGURACIÓN INSTITUCIONAL V110 ---
st.set_page_config(page_title="SENTINEL QUANT V110", page_icon="🧠", layout="wide")

# Descarga de léxico para el Nervio Óptico (NLP)
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

# --- 🎨 PROTOCOLOS VISUALES SUPREME ---
def color_sentinel(val):
    if "🔥" in str(val) or "🛡️" in str(val): return 'background-color: #1B5E20; color: white'
    if "⚖️" in str(val) or "⌛" in str(val): return 'background-color: #1A237E; color: white'
    if "🏹" in str(val) or "🛰️" in str(val): return 'background-color: #F57F17; color: white'
    if "⚠️" in str(val): return 'background-color: #B71C1C; color: white'
    return ''

# --- 🧠 MOTORES DE EVOLUCIÓN (TRANSFORMERS & BAYES) ---
def obtener_humor_sentinel(ticker):
    sia = SentimentIntensityAnalyzer()
    try:
        t = yf.Ticker(ticker)
        titulares = [n['title'] for n in t.news[:5]] 
        if not titulares: return 0.0, "⚖️ CALMA"
        scores = [sia.polarity_scores(tit)['compound'] for tit in titulares]
        avg = sum(scores) / len(scores)
        humor = "🔥 CODICIA" if avg > 0.05 else "😱 MIEDO" if avg < -0.05 else "⚖️ CALMA"
        return round(avg * 100, 1), humor
    except: return 0.0, "⚖️ CALMA"

def logica_atencion_tft(ticker):
    """ Mecanismo de Atención (Transformers): ¿El volumen respalda el precio? """
    try:
        data = yf.download(ticker, period="21d", interval="1d", progress=False)
        if data.empty: return 1.0
        # Comparamos volumen actual vs promedio de 21 días
        atencion = data['Volume'].iloc[-1] / data['Volume'].mean()
        return round(atencion, 2)
    except: return 1.0

def inferencia_bayesiana(prior_ia, humor_val, atencion):
    """ Cálculo de Certeza Bayesiana: Filtra el ruido institucional """
    # Prior: Nuestra confianza inicial (Score IA)
    # Evidencia: El humor de las noticias ajustado por la atención del volumen
    evidencia = 1.0 if humor_val > 0 else 0.5
    if atencion > 1.8: evidencia *= 1.2 # El volumen confirma la intención
    
    # Teorema de Bayes simplificado para probabilidad 'A Posteriori'
    posterior = (prior_ia * evidencia) / ((prior_ia * evidencia) + ((1 - prior_ia) * (1 - evidencia)))
    return round(posterior, 2)

# --- 🛠️ FUNCIONES DE MERCADO ---
def get_price(t):
    try:
        data = yf.Ticker(t).history(period="5d")
        if data.empty: return 0.0
        p = data['Close'].iloc[-1]
        if "DICP" in t: return round(p * 100, 2) if p < 1000 else round(p, 2)
        return round(p, 2)
    except: return 0.0

def calcular_kelly(score_ia):
    # Criterio de Kelly Institucional (Riesgo/Beneficio 1.5)
    f_kelly = (score_ia * 2.5 - 1) / 1.5
    return max(0, round(f_kelly / 4, 4))

# --- 🕹️ GESTIÓN DE SESIÓN ---
if 'liq' not in st.session_state: st.session_state.liq = 3800000.0
flota_init = {
    'YPFD.BA': {'score': 0.82, 'estado': "🛡️ HOLD"},
    'VIST.BA': {'score': 0.88, 'estado': "🛡️ HOLD"},
    'DICP.BA': {'score': 0.75, 'estado': "⚓ BÚNKER"},
    'PAMP.BA': {'score': 0.80, 'estado': "⌛ ACECHAR"}
}

# --- 📊 PROCESAMIENTO DE DATOS ---
df_radar = pd.DataFrame.from_dict(flota_init, orient='index').reset_index()
df_radar.columns = ['ACTIVO', 'SCORE IA', 'ESTADO TÁCTICO']
df_radar['PRECIO ACT'] = df_radar['ACTIVO'].apply(get_price)
df_radar['ATTENTION'] = df_radar['ACTIVO'].apply(logica_atencion_tft)

humor_res = df_radar['ACTIVO'].apply(obtener_humor_sentinel)
df_radar['SCORE HUMOR'] = [h[0] for h in humor_res]
df_radar['HUMOR'] = [h[1] for h in humor_res]

df_radar['CERTEZA'] = df_radar.apply(lambda x: inferencia_bayesiana(x['SCORE IA'], x['SCORE HUMOR'], x['ATTENTION']), axis=1)
df_radar['KELLY %'] = df_radar['SCORE IA'].apply(calcular_kelly)
df_radar['SUGERENCIA $'] = df_radar['KELLY %'] * st.session_state.liq

# Lógica de Acción Gated (Inspirada en TFT)
def gated_action(certeza, att):
    if certeza < 0.55: return "🛰️ FILTRANDO RUIDO"
    if att > 2.0: return "🔥 COMPRA VALIDADA"
    return "⌛ MANTENER / VIGILAR"

df_radar['ACCIÓN'] = df_radar.apply(lambda x: gated_action(x['CERTEZA'], x['ATTENTION']), axis=1)

# --- 🛰️ INTERFAZ SUPREME ---
st.title("🛰️ SENTINEL QUANT V110")
brent = get_price("BZ=F")
if brent == 0: brent = 95.12

st.info(f"🧠 **MODO LABORATORIO:** Inferencia Bayesiana activa. Brent Ref: u$s {brent}. Analizando señales institucionales para los $3.8M.")

c1, c2, c3 = st.columns(3)
c1.metric("🛡️ Liquidez Bunker", f"${st.session_state.liq:,.0f}")
c2.metric("⛽ Brent (Ref)", f"u$s {brent}")
c3.metric("📊 Certeza Media", f"{df_radar['CERTEZA'].mean():.2f}")

st.write("### 📊 Tablero de Inferencia Institucional")
columnas = ['ACTIVO', 'ACCIÓN', 'CERTEZA', 'ATTENTION', 'HUMOR', 'SCORE IA', 'PRECIO ACT', 'KELLY %', 'SUGERENCIA $']
st.dataframe(df_radar[columnas].style.map(color_sentinel, subset=['ACCIÓN']), use_container_width=True, hide_index=True)

# Radar Fractal Inferior
st.write("---")
st.write("### 🛰️ Radar Fractal Global")
radar_g = ['NVDA', 'TSM', 'ASML', 'YPF', 'GLD', 'CCJ', 'CAT']
try:
    df_g = yf.download(radar_g, period="6mo", interval="1d", progress=False)['Close'].ffill()
    cols = st.columns(len(radar_g))
    for i, t in enumerate(sorted(radar_g)):
        p = df_g[t].iloc[-1]
        f5 = "🔼" if p > df_g[t].iloc[-5] else "🔽"
        f21 = "🔼" if p > df_g[t].iloc[-21] else "🔽"
        f63 = "🔼" if p > df_g[t].iloc[-63] else "🔽"
        with cols[i]: st.code(f"{t}\n{f5}|{f21}|{f63}")
except:
    st.warning("Sincronizando satélites...")
