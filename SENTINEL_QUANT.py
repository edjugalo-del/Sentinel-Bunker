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

st.subheader("🎯 Radar de Convergencia & P&L (SENTINEL V161)")

# --- 🚀 BYPASS DE DATOS: CARGA FORZADA ---
try:
    # 1. Cálculo de Dólar Arbitraje (GGAL)
    gl = yf.Ticker("GGAL.BA").history(period="2d")['Close'].iloc[-1]
    ga = yf.Ticker("GGAL").history(period="2d")['Close'].iloc[-1]
    ccl_v161 = (gl * 10) / ga

    # 2. Reconstrucción del Radar en Tiempo Real
    # Ratios: VIST (3:1), YPF (2:1), NVDA (48:1)
    activos = {'VIST': 3, 'YPF': 2, 'NVDA': 48, 'TSLA': 15}
    arb_data = []

    for ticker, ratio in activos.items():
        t_l = f"{ticker}.BA" if ticker != 'VIST' else 'VIST.BA'
        p_u = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
        p_l = yf.Ticker(t_l).history(period="1d")['Close'].iloc[-1]
        
        p_teo = (p_u * ccl_v161) / ratio
        sprd = ((p_l - p_teo) / p_teo) * 100
        
        # --- 🎯 SENSIBILIDAD SOLICITADA: 0.8% ---
        if sprd < -0.8: acc, sug = "🔥 COMPRA", "MANTENER POSICIÓN"
        elif sprd > 0.8: acc, sug = "⚠️ VENTA", "TOMAR GANANCIA"
        else: acc, sug = "✅ OK", "WAIT & WATCH"

        arb_data.append({
            "ACTIVO": ticker, "ACCIÓN": acc, "PRECIO NY": f"u$s {p_u:.2f}",
            "TEÓRICO": f"${p_teo:,.0f}", "LOCAL": f"${p_l:,.0f}",
            "SPREAD": f"{sprd:+.2f}%", "SUGERENCIA": sug
        })
    
    # Visualización forzada de la tabla
    st.table(pd.DataFrame(arb_data))
    st.success(f"🛰️ Radar Sincronizado (CCL: ${ccl_v161:.2f})")

except Exception as e:
    st.info(f"🛰️ Sincronizando datos... Error de Enlace: {e}")

st.write("---")
# --- 🌐 ALERTA TEMPRANA (Mantenemos tu lógica de Fractales) ---
st.markdown("### 🌐 Alerta Temprana & Fractal Global")
# ... resto de tu código de columnas macro ...


st.write("---")
# --- 🎯 MONITOR DE ARBITRAJE QUIRÚRGICO (V161.1) ---
st.write("---")
st.subheader("🎯 Detector de Desarbitraje en Tiempo Real")

try:
    # 1. Dólar Sentinel (CCL Promedio GGAL)
    gl_h = yf.Ticker("GGAL.BA").history(period="2d")['Close']
    ga_h = yf.Ticker("GGAL").history(period="2d")['Close']
    
    if not gl_h.empty and not ga_h.empty:
        ccl_s = (gl_h.iloc[-1] * 10) / ga_h.iloc[-1]
        st.info(f"💵 **Dólar CCL Referencia:** ${ccl_s:.2f}")

        # --- 🛡️ RATIOS ACTUALIZADOS (VIST es 3:1) ---
        ratios = {'VIST': 3, 'YPF': 2, 'NVDA': 48, 'TSLA': 15, 'AAPL': 10}
        arb_res = []
        
        for t_u, ratio in ratios.items():
            try:
                t_l = f"{t_u}.BA" if t_u != 'VIST' else 'VIST.BA'
                # Forzamos 1m de intervalo para capturar el post-market/pre-market
                p_u = yf.Ticker(t_u).history(period="1d", interval="1m")['Close'].iloc[-1]
                p_l = yf.Ticker(t_l).history(period="1d", interval="1m")['Close'].iloc[-1]
                
                p_t = (p_u * ccl_s) / ratio
                sprd = ((p_l - p_t) / p_t) * 100
                
                # --- 🎯 SENSIBILIDAD SOLICITADA: 0.8% ---
                if sprd < -0.8: # Antes 1.2, ahora 0.8
                    estado = "🔥 COMPRA TÁCTICA"
                    color = "color: #76FF03"
                elif sprd > 0.8: 
                    estado = "⚠️ VENTA / ARBITRAR"
                    color = "color: #FF1744"
                else: 
                    estado = "✅ EQUILIBRIO"
                    color = "color: #FFFFFF"

                arb_res.append({
                    "ACTIVO": t_u, 
                    "PRECIO NY": f"u$s {p_u:.2f}",
                    "SPREAD %": f"{sprd:+.2f}%", 
                    "ACCIÓN": estado
                })
            except: continue
        
        st.table(pd.DataFrame(arb_res)) # Usamos table para evitar el "scroll" y ver todo de una
    else:
        st.warning("⚠️ BYMA Offline - Usando último cierre conocido")
except Exception as e:
    st.error(f"Error de Sincronización: {e}")
