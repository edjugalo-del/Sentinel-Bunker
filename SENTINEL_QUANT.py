import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

st.set_page_config(page_title="SENTINEL QUANT V110", page_icon="🧠", layout="wide")

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

def color_sentinel(val):
    if "🔥" in str(val): return 'background-color: #1B5E20; color: white'
    if "⌛" in str(val): return 'background-color: #1A237E; color: white'
    if "🛰️" in str(val): return 'background-color: #F57F17; color: white'
    return ''

def obtener_humor_sentinel(ticker):
    sia = SentimentIntensityAnalyzer()
    try:
        t = yf.Ticker(ticker)
        titulares = [n['title'] for n in t.news[:5]]
        if not titulares: return 0.0, "⚖️ CALMA"
        scores = [sia.polarity_scores(tit)['compound'] for tit in titulares]
        avg = sum(scores) / len(scores)
        h = "🔥 CODICIA" if avg > 0.05 else "😱 MIEDO" if avg < -0.05 else "⚖️ CALMA"
        return round(avg * 100, 1), h
    except: return 0.0, "⚖️ CALMA"

def logica_atencion_tft(ticker):
    try:
        data = yf.download(ticker, period="30d", interval="1d", progress=False)
        if data.empty or len(data) < 2: return 1.0
        v_act = float(data['Volume'].values[-1])
        v_med = float(data['Volume'].mean())
        return round(v_act / v_med, 2)
    except: return 1.0

def inferencia_bayesiana(prior_ia, humor_val, atencion):
    evid = 1.0 if humor_val > 0 else 0.5
    if atencion > 1.8: evid *= 1.2
    post = (prior_ia * evid) / ((prior_ia * evid) + ((1 - prior_ia) * (1 - evid)))
    return round(post, 2)

def get_price(t):
    try:
        d = yf.Ticker(t).history(period="5d")
        if d.empty: return 0.0
        p = d['Close'].iloc[-1]
        if "DICP" in t: p = p * 100 if p < 1000 else p
        return round(p, 2)
    except: return 0.0

if 'liq' not in st.session_state: st.session_state.liq = 3800000.0
f_init = {'YPFD.BA': 0.82, 'VIST.BA': 0.88, 'DICP.BA': 0.75, 'PAMP.BA': 0.80}

df_radar = pd.DataFrame(list(f_init.items()), columns=['ACTIVO', 'SCORE IA'])
df_radar['PRECIO ACT'] = df_radar['ACTIVO'].apply(get_price)
df_radar['ATTENTION'] = df_radar['ACTIVO'].apply(logica_atencion_tft)
hum_data = df_radar['ACTIVO'].apply(obtener_humor_sentinel)
hum_data = df_radar['ACTIVO'].apply(obtener_humor_sentinel)
# Separamos: el Score (número) para el cálculo y el Humor (texto) para la vista
df_radar['SCORE HUMOR'] = [float(x[0]) for x in hum_data]
df_radar['HUMOR'] = [str(x[1]) for x in hum_data]

df_radar['CERTEZA'] = df_radar.apply(lambda x: inferencia_bayesiana(x['SCORE IA'], x['SCORE HUMOR'], x['ATTENTION']), axis=1)
df_radar['KELLY %'] = df_radar['SCORE IA'].apply(lambda x: max(0, round((x * 2.5 - 1) / 1.5 / 4, 4)))
df_radar['SUGERENCIA $'] = df_radar['KELLY %'] * st.session_state.liq
df_radar['ACCIÓN'] = df_radar.apply(lambda x: "🛰️ FILTRANDO" if x['CERTEZA'] < 0.55 else ("🔥 COMPRA" if x['ATTENTION'] > 2.0 else "⌛ MANTENER"), axis=1)


st.title("🛰️ SENTINEL QUANT V110")
st.info(f"🧠 **MODO LABORATORIO:** Inferencia Bayesiana activa. Liquidez: ${st.session_state.liq:,.0f}")
cols = ['ACTIVO', 'ACCIÓN', 'CERTEZA', 'ATTENTION', 'HUMOR', 'SCORE IA', 'PRECIO ACT', 'KELLY %', 'SUGERENCIA $']
st.dataframe(df_radar[cols].style.map(color_sentinel, subset=['ACCIÓN']), use_container_width=True, hide_index=True)

st.write("---")
st.write("### 🛰️ Radar Fractal Global")
r_g = ['NVDA', 'TSM', 'ASML', 'YPF', 'GLD', 'CCJ', 'CAT']
try:
    df_g = yf.download(r_g, period="6mo", interval="1d", progress=False)['Close'].ffill()
    cl = st.columns(len(r_g))
    for i, t in enumerate(sorted(radar_g)): # Usar radar_g aquí
        p = float(df_g[t].iloc[-1])
        f5, f21, f63 = ("🔼" if p > float(df_g[t].iloc[-x]) else "🔽" for x in [5, 21, 63])
        with cl[i]: st.code(f"{t}\n{f5}|{f21}|{f63}")
except: st.warning("Sincronizando...")
