import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# --- 🛰️ INSTITUTIONAL CONFIG ---
st.set_page_config(page_title="SENTINEL QUANT V120", page_icon="🏦", layout="wide")

@st.cache_resource
def init_nlp():
    try:
        nltk.download('vader_lexicon', quiet=True)
        return SentimentIntensityAnalyzer()
    except Exception: return None

sia = init_nlp()

# --- 🛠️ CORE ENGINE (Vectorized & Robust) ---

def get_market_data(tickers):
    """Descarga masiva para evitar latencia y bloqueos de API"""
    try:
        data = yf.download(tickers, period="60d", interval="1d", progress=False, group_by='ticker')
        return data
    except Exception as e:
        st.error(f"Error de Feed: {e}")
        return pd.DataFrame()

def analyze_sentiment_institutional(ticker):
    if not sia: return 0.0, "⚖️ NEUTRAL"
    try:
        t = yf.Ticker(ticker)
        news = t.news
        if not news: return 0.0, "⚖️ SIN DATA"
        
        scores = [sia.polarity_scores(n['title'])['compound'] for n in news[:5]]
        avg_score = np.mean(scores)
        
        if avg_score > 0.10: mood = "🔥 EUFORIA"
        elif avg_score < -0.10: mood = "😱 PÁNICO"
        else: mood = "⚖️ CALMA"
        
        return round(avg_score * 100, 2), mood
    except: 
        return 0.0, "⚖️ CALMA"


def calculate_kelly(edge, win_rate=0.55):
    """
    Kelly Criterion Fraccional (Conservador para CFO)
    Fórmula: (bp - q) / b  donde b es el payout ratio.
    Simplificado para equities: (2 * WinRate - 1) * Factor de Confianza
    """
    fractional_kelly = 0.25 # 1/4 Kelly para evitar Drawdowns agresivos
    k = (2 * win_rate - 1) * edge
    return max(0, round(k * fractional_kelly, 4))

# --- 📊 EXECUTION LAYER ---

st.title("🛰️ SENTINEL QUANT | Institutional Dashboard")
st.sidebar.header("Risk Management")
liq = st.sidebar.number_input("Liquidez Operativa (ARS/USD)", value=3800000.0)
win_rate_exp = st.sidebar.slider("Probabilidad de Acierto IA", 0.5, 0.9, 0.58)

f_init = {'YPFD.BA': 0.82, 'VIST.BA': 0.88, 'DICP.BA': 0.75, 'PAMP.BA': 0.80, 'GGAL.BA': 0.85}
tickers = list(f_init.keys())

# Fetch masivo de datos
with st.spinner("Sincronizando con terminales de mercado..."):
    raw_data = get_market_data(tickers)

results = []
for t in tickers:
    try:
        # 1. Obtención de Datos con Rescate para DICP/Local
        hist = raw_data[t] if len(tickers) > 1 else raw_data
        try:
            p_val = float(hist['Close'].iloc[-1])
            curr_price = round(p_val, 2) if not np.isnan(p_val) else 0.0
        except:
            try:
                p_val = yf.Ticker(t).history(period="5d")['Close'].iloc[-1]
                curr_price = round(p_val, 2)
            except: curr_price = 0.0

        # 2. Métricas de Atención y Humor
        vol_avg = hist['Volume'].mean() if not hist['Volume'].empty else 1
        vol_curr = hist['Volume'].iloc[-1] if not hist['Volume'].empty else 0
        atencion = round(vol_curr / vol_avg, 2)
        score_humor, humor_label = analyze_sentiment_institutional(t)
        
        # 3. Inferencia Bayesiana Refinada
        prior = f_init[t]
        likelihood = 1.0
        if atencion > 1.5: likelihood *= 1.3
        if score_humor > 10: likelihood *= 1.2
        if atencion < 0.6: likelihood *= 0.7
        
        posterior = (prior * likelihood) / ((prior * likelihood) + (1 - prior))
        post_f = round(min(posterior, 0.99), 2) 

        # 4. Money Management (Kelly 1/4)
        k_perc = calculate_kelly(post_f, win_rate_exp)
        sug_cash = k_perc * liq
        
        # 5. Lógica de Señal
        if post_f > 0.80 and atencion > 1.2: accion = "🔥 COMPRA FUERTE"
        elif post_f > 0.65: accion = "⌛ MANTENER"
        elif post_f < 0.45: accion = "🛰️ FILTRAR"
        else: accion = "⚖️ NEUTRAL"

        # 6. Empaquetado Profesional
        results.append({
            "ACTIVO": t,
            "ACCIÓN": accion,
            "CONFIDENCIA": f"{int(post_f*100)}%",
            "ATTN": atencion,
            "HUMOR": humor_label,
            "PRECIO": f"{curr_price:,.2f}" if curr_price > 0 else "Sincronizando...",
            "KELLY": f"{k_perc*100:.1f}%",
            "SUGERENCIA": f"${sug_cash:,.0f}"
        })
    except Exception as e:
        continue

df_final = pd.DataFrame(results)

# --- 🖥️ INTERFACE ---
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Radar de Alta Prioridad")
    st.dataframe(df_final.style.map(
        lambda x: 'background-color: #06402B; color: #76FF03' if "COMPRA" in str(x) else '',
        subset=['ACCIÓN']
    ), use_container_width=True, hide_index=True)

with col2:
    st.subheader("Resumen de Riesgo")
    total_exp = sum([float(x.replace('$','').replace(',','')) for x in df_final['SUGERENCIA']])
    st.metric("Exposición Sugerida", f"${total_exp:,.0f}")
    st.progress(min(total_exp / liq, 1.0))
    st.caption(f"Utilización de Capital: {round((total_exp/liq)*100, 2)}%")

# --- 🛰️ GLOBAL FRACTAL MONITOR ---
st.write("---")
st.markdown("### 🌐 Global Macro Momentum (5D | 21D | 63D)")
global_tickers = ['NVDA', 'AAPL', 'YPF', 'BTC-USD', 'GC=F']
cols = st.columns(len(global_tickers))

for i, gt in enumerate(global_tickers):
    try:
        g_hist = yf.Ticker(gt).history(period="100d")['Close']
        p_now = g_hist.iloc[-1]
        def get_t(days): return "🔼" if p_now > g_hist.iloc[-days] else "🔽"
        with cols[i]:
            st.metric(gt, f"{p_now:,.2f}")
            st.code(f"{get_t(5)} | {get_t(21)} | {get_t(63)}")
    except:
        with cols[i]: st.caption(f"{gt}: ⌛ Sync")
