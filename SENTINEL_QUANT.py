import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# --- 🛰️ CONFIGURACIÓN INSTITUCIONAL V160 ---
st.set_page_config(page_title="SENTINEL V160", page_icon="🏦", layout="wide")

@st.cache_resource
def init_nlp():
    try:
        nltk.download('vader_lexicon', quiet=True)
        return SentimentIntensityAnalyzer()
    except: return None

sia = init_nlp()

# --- 🛡️ GESTIÓN DE SESIÓN Y PRIVACIDAD ---
if 'liq' not in st.session_state: st.session_state.liq = 3800000.0

st.sidebar.title("🛰️ ESTRATEGIA & RIESGO")
modo_privacidad = st.sidebar.toggle("Modo Privacidad 👁️", value=False)
win_rate_exp = st.sidebar.slider("Probabilidad IA", 0.5, 0.9, 0.65)

def fmt_money(val):
    if modo_privacidad: return "∗∗∗.∗∗∗"
    return f"${val:,.0f}"

# --- 🧠 MOTOR DE RIESGO (MONTE CARLO) ---
def run_monte_carlo(capital, days=30):
    sims = 1000
    results_mc = []
    for _ in range(sims):
        daily_ret = np.random.normal(0.0005, 0.02, days)
        results_mc.append(capital * np.prod(1 + daily_ret))
    return np.percentile(results_mc, 5), np.percentile(results_mc, 95)

# --- 🧠 LÓGICA DE SENTIMIENTO ---
def analyze_sentiment(ticker):
    if not sia: return 0.0, "⚖️ NEUTRAL"
    try:
        t = yf.Ticker(ticker)
        news = t.news[:5]
        if not news: return 0.0, "⚖️ CALMA"
        scores = [sia.polarity_scores(n['title'])['compound'] for n in news]
        avg = np.mean(scores)
        mood = "🔥 EUFORIA" if avg > 0.1 else "😱 PÁNICO" if avg < -0.1 else "⚖️ CALMA"
        return round(avg * 100, 2), mood
    except: return 0.0, "⚖️ CALMA"

# --- 📊 PROCESAMIENTO DE DATOS ---
f_init = {'YPFD.BA': 0.82, 'VIST.BA': 0.88, 'GGAL.BA': 0.80, 'NVDA': 0.85, 'TSLA': 0.75}
precios_entrada = {'YPFD.BA': 58500.0, 'VIST.BA': 31000.0, 'GGAL.BA': 3200.0, 'NVDA': 850.0, 'TSLA': 170.0}
tickers = list(f_init.keys())

with st.spinner("Sincronizando Terminal Sentinel..."):
    raw_data = yf.download(tickers, period="60d", interval="1d", progress=False)
    if not raw_data.empty: raw_data = raw_data.ffill().bfill()
    try:
        dxy_now = yf.Ticker("DX-Y.NYB").history(period="5d")['Close'].iloc[-1]
        brent_now = yf.Ticker("BZ=F").history(period="5d")['Close'].iloc[-1]
    except: dxy_now, brent_now = 104.5, 95.0

results = []
for t in tickers:
    try:
        hist = raw_data[t]['Close'] if len(tickers) > 1 else raw_data['Close']
        curr_p = float(hist.iloc[-1])
        entry_p = precios_entrada.get(t, curr_p)
        pnl_pct = ((curr_p - entry_p) / entry_p) * 100
        pnl_neto = (st.session_state.liq * 0.1) * (pnl_pct / 100)
        
        vol_hist = raw_data[t]['Volume'] if len(tickers) > 1 else raw_data['Volume']
        atn = round(vol_hist.iloc[-1] / vol_hist.mean(), 2)
        
        score_h, mood_h = analyze_sentiment(t)
        prior = f_init[t]
        likelihood = (1.3 if atn > 1.4 else 1.0) * (1.2 if score_h > 10 else 1.0)
        post = round(min((prior * likelihood) / ((prior * likelihood) + (1 - prior)), 0.99), 2)
        
        results.append({
            "ACTIVO": t,
            "ACCIÓN": "🔥 COMPRA" if post > 0.8 else "⌛ MANTENER" if post > 0.6 else "🛰️ FILTRAR",
            "CONFIDENCIA": f"{int(post*100)}%",
            "ATTN": atn,
            "P&L %": f"{pnl_pct:+.2f}%",
            "P&L NETO": fmt_money(pnl_neto),
            "SUGERENCIA": fmt_money(st.session_state.liq * 0.15),
            "val_post": post
        })
    except: continue

df_final = pd.DataFrame(results)

# --- 🖥️ INTERFACE ÚNICA V160 ---
st.title("🛰️ SENTINEL V160 | Institutional Fortress")

def generar_nota(df, dxy, brent):
    c_avg = df['val_post'].mean() if (not df.empty and 'val_post' in df.columns) else 0.5
    if dxy > 105.5: return "⚠️ DEFENSA: DXY fuerte. Presión en commodities."
    if brent > 94.0 and c_avg > 0.70: return "🔥 ATAQUE: Brent firme. Inferencia Bayesiana valida momentum."
    return "⌛ NEUTRAL: Mercado lateral. Esperando volumen."

st.chat_message("assistant").write(f"**Rationale Estratégico:** {generar_nota(df_final, dxy_now, brent_now)}")

worst, best = run_monte_carlo(st.session_state.liq)
c1, c2, c3 = st.columns(3)
with c1: st.metric("Riesgo Monte Carlo (VAR 5%)", fmt_money(worst), delta=f"-{((st.session_state.liq-worst)/st.session_state.liq)*100:.1f}%")
with c2: st.metric("Potencial Upside (95%)", fmt_money(best))
with c3: st.metric("Dólar DXY", f"{dxy_now:.2f}", delta="ALERTA" if dxy_now > 105 else "CALMA", delta_color="inverse")

st.subheader("🎯 Radar de Convergencia & P&L")
if not df_final.empty:
    cols_v = ["ACTIVO", "ACCIÓN", "CONFIDENCIA", "ATTN", "P&L %", "P&L NETO", "SUGERENCIA"]
    safe_c = [c for c in cols_v if c in df_final.columns]
    st.dataframe(df_final[safe_c].style.map(
        lambda x: 'color: #76FF03' if any(w in str(x) for w in ["+", "COMPRA"]) else 'color: #FF1744' if any(w in str(x) for w in ["-", "FILTRAR"]) else '',
        subset=[c for c in ["ACCIÓN", "P&L %", "P&L NETO"] if c in safe_c]
    ), use_container_width=True, hide_index=True)
else:
    st.info("🛰️ Sincronizando datos... El radar se activará en la apertura.")

st.write("---")
st.markdown("### 🌐 Alerta Temprana & Fractal Global")
global_dict = {'DX-Y.NYB': 'DXY', 'BZ=F': 'BRENT', 'GC=F': 'ORO', 'BTC-USD': 'BITCOIN'}
cols_macro = st.columns(len(global_dict))
for i, (ticker, nombre) in enumerate(global_dict.items()):
    try:
        m_hist = yf.Ticker(ticker).history(period="100d")['Close']
        p_actual = m_hist.iloc[-1]
        def trend(d): return "🔼" if p_actual > m_hist.iloc[-d] else "🔽"
        with cols_macro[i]:
            st.metric(nombre, f"{p_actual:,.2f}")
            st.code(f"{trend(5)} | {trend(21)} | {trend(63)}")
    except: continue

st.write("---")
st.subheader("🎯 Detector de Desarbitraje CEDEARs")
try:
    gl = yf.Ticker("GGAL.BA").history(period="5d")['Close'].iloc[-1]
    ga = yf.Ticker("GGAL").history(period="5d")['Close'].iloc[-1]
    ccl_s = (gl * 10) / ga
    st.info(f"💵 **Dólar CCL Referencia:** ${ccl_s:.2f}")
    ratios = {'NVDA': 48, 'TSLA': 15, 'AAPL': 10, 'VIST': 1}
    arb_res = []
    for t_u, ratio in ratios.items():
        try:
            t_l = f"{t_u}.BA" if t_u != 'VIST' else 'VIST.BA'
            p_u = yf.Ticker(t_u).history(period="5d")['Close'].iloc[-1]
            p_l = yf.Ticker(t_l).history(period="5d")['Close'].iloc[-1]
            p_t = (p_u * ccl_s) / ratio
            sprd = ((p_l - p_t) / p_t) * 100
            arb_res.append({"ACTIVO": t_u, "SPREAD %": f"{sprd:+.2f}%", "ESTADO": "🔥 COMPRAR" if sprd < -1.2 else "⚠️ VENDER" if sprd > 1.2 else "✅ OK"})
        except: continue
    st.dataframe(pd.DataFrame(arb_res), use_container_width=True, hide_index=True)
except: st.caption("Esperando apertura...")

