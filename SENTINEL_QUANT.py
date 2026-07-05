import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# =============================================================================
# 🧠 CONFIGURACIÓN INSTITUCIONAL V162.1 | COMBAT READY (KEEP-ALIVE MÓVIL)
# =============================================================================
st.set_page_config(page_title="SENTINEL V162.1", page_icon="🏦", layout="wide")

@st.cache_resource
def init_nlp():
    try:
        nltk.download('vader_lexicon', quiet=True)
        return SentimentIntensityAnalyzer()
    except: return None

sia = init_nlp()

# =============================================================================
# 🛡️ GESTIÓN DE PRIVACIDAD Y REGLAS DE SINCRO CON TRADINGVIEW
# =============================================================================
if 'liq' not in st.session_state: 
    st.session_state.liq = 3800000.0 # Tu liquidez real de comitente

st.sidebar.title("🛰️ ESTRATEGIA & RIESGO MACRO")
modo_privacidad = st.sidebar.toggle("Modo Privacidad En la Calle 👁️", value=False)
win_rate_exp = st.sidebar.slider("Probabilidad Base IA", 0.5, 0.9, 0.65)

# Parámetros estrictos de tu TradingView: 0.5% comitente + 2% de deslizamiento
comision_broker = 0.005
slippage_volatilidad = 0.02

def fmt_money(val):
    if modo_privacidad: return "∗∗∗.∗∗∗"
    return f"${val:,.0f} ARS"

# =============================================================================
# 🧠 MOTOR DE RISK MANAGEMENT (SIMULACIÓN DE MONTE CARLO - 1000 ESCENARIOS)
# =============================================================================
def run_monte_carlo(capital, days=30):
    sims = 1000
    results_mc = []
    for _ in range(sims):
        daily_ret = np.random.normal(0.0005, 0.02, days)
        results_mc.append(capital * np.prod(1 + daily_ret))
    return np.percentile(results_mc, 5), np.percentile(results_mc, 95)

# =============================================================================
# 🧠 LÓGICA DE SENTIMIENTO EN TITULARES DE WALL STREET (NLP)
# =============================================================================
def analyze_sentiment(ticker, sesion=None):
    if not sia: return 0.0, "⚖️ NEUTRAL"
    try:
        t = yf.Ticker(ticker, session=sesion)
        news = t.news[:5]
        if not news: return 0.0, "⚖️ CALMA"
        scores = [sia.polarity_scores(n['title'])['compound'] for n in news]
        avg = np.mean(scores)
        mood = "🔥 EUFORIA" if avg > 0.1 else ("😱 PÁNICO" if avg < -0.1 else "⚖️ CALMA")
        return round(avg * 100, 2), mood
    except: return 0.0, "⚖️ CALMA"

# =============================================================================
# 🛰️ MOTOR DE DATOS UNIFICADO DE ALTA VELOCIDAD (HORIZONTE 10 AÑOS REALES)
# =============================================================================
tickers_base = ['YPFD.BA', 'VIST.BA', 'PAMP.BA', 'DICP.BA', 'GGAL.BA', 'NVDA', 'TSLA', 'GGAL', 'BZ=F', 'DX-Y.NYB', 'GC=F', 'BTC-USD']

tenencia_real = {
    'YPFD.BA': {'nominales': 101, 'entrada': 61951.00}, 
    'VIST.BA': {'nominales': 89, 'entrada': 33049.21}, 
    'PAMP.BA': {'nominales': 196, 'entrada': 5135.00},
    'DICP.BA': {'nominales': 408, 'entrada': 505.20}
}

sesion_fortress = requests.Session()
sesion_fortress.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

with st.spinner("Sincronizando Satélites de la Terminal Sentinel..."):
    try:
        # Descarga a compresión diaria de largo plazo para alimentar los fractales sin agujeros de datos
        raw_data = yf.download(tickers_base, period="10y", interval="1d", progress=False, session=sesion_fortress)['Close']
        raw_data = raw_data.ffill().bfill()
        
        brent_live = float(raw_data["BZ=F"].values.ravel()[-1]) if "BZ=F" in raw_data.columns else 72.13
        dxy_now = float(raw_data["DX-Y.NYB"].values.ravel()[-1]) if "DX-Y.NYB" in raw_data.columns else 104.20
        
    except Exception as e:
        brent_live, dxy_now = 72.13, 104.20

# =============================================================================
# 🧠 RATIONALE ESTRATÉGICO DINÁMICO (CALIBRADO AL RANGO REAL DE 2026)
# =============================================================================
if brent_live > 85.0:
    msg, icono = "🔥 SHOCK DE OFERTA: Escenario de Tensión. Priorizar Cobertura de Energía (VIST/YPF).", "🚨"
elif brent_live < 70.0:
    msg, icono = "🕊️ SOPORTE QUEBRADO: Toma de ganancias táctica sugerida en commodities por fin de Onda C.", "🟢"
else:
    msg, icono = "⌛ CICLO NORMAL: Petróleo consolidando en zona de caza. Mercado procesando datos estructurales.", "⚖️"

st.title("🛰️ SENTINEL V162.1 | Institutional Fortress")
st.chat_message("assistant").write(f"**Rationale Estratégico Dinámico:** {icono} {msg} (Brent Live: u$s {brent_live:.2f} USD)")

# =============================================================================
# 📊 DESPLIEGUE DE MÉTRICAS DE RIESGO DE MONTE CARLO
# =============================================================================
worst, best = run_monte_carlo(st.session_state.liq)
c1, c2, c3 = st.columns(3)
with c1: 
    st.metric("Riesgo Monte Carlo (VAR 5%)", fmt_money(worst), delta=f"-{((st.session_state.liq-worst)/st.session_state.liq)*100:.1f}%")
with c2: 
    st.metric("Potencial Upside Teórico (95%)", fmt_money(best))
with c3: 
    st.metric("Dólar Índice DXY", f"{dxy_now:.2f}", delta="ALERTA" if dxy_now > 105 else "CALMA", delta_color="inverse")

# =============================================================================
# 📊 MANDO CENTRAL SENTINEL V162 (TENENCIA DE ACTIVOS REAL)
# =============================================================================
st.write("---")
st.subheader("📊 Mando Central: Operaciones y Ejecución en Pesos")

try:
    p_ggal_ba = float(raw_data["GGAL.BA"].values.ravel()[-1])
    p_ggal_us = float(raw_data["GGAL"].values.ravel()[-1])
    ccl_v = (p_ggal_ba * 10) / p_ggal_us if p_ggal_us > 0 else 1571.25
    
    mando_res = []
    
    for t_l, valores in tenencia_real.items():
        try:
            nominales = valores['nominales']
            entrada = valores['entrada']
            
            cp_l = float(raw_data[t_l].values.ravel()[-1])
            
            t_u = t_l.replace('D.BA', '').replace('.BA', '')
            p_u = float(yf.Ticker(t_u, session=sesion_fortress).fast_info['last_price']) if 'DICP' not in t_l else None
            
            ratio = round((p_u * ccl_v) / cp_l) if p_u else 1
            p_t = (p_u * ccl_v) / ratio if p_u else cp_l
            sprd = ((cp_l - p_t) / p_t) * 100 if p_u else 0.0

            score_ia = 0.5 + (0.3 if brent_live > 82.0 else -0.1) + (0.15 if sprd < -0.8 else 0)
            score_ia = min(0.99, max(0.05, score_ia))
            
            monto_neto = cp_l * nominales
            pnl_neto = (cp_l - entrada) * nominales
            kelly_f = max(0.0, (score_ia - (1 - score_ia)))
            st_cap = st.session_state.liq * kelly_f * 0.5
            
            # SINCRO TRADINGVIEW: Límite estricto con el 2.5% de recargo por deslizamiento y costos
            limite_compra_tv = cp_l * (1 + comision_broker + slippage_volatilidad)
            sug_nominales_tv = int(np.floor((st_cap * (1 - comision_broker)) / cp_l)) if cp_l > 0 else 0

            mando_res.append({
                "ACTIVO": t_l,
                "ACCCIÓN": "🚀 RECOMPRA" if sprd < -1.2 else ("⚠️ VENTA" if sprd > 1.5 else "⌛ MANTENER"),
                "ESTADO TÁCTICO": "🛡️ ACORAZADA" if score_ia > 0.85 else "⚖️ NEUTRAL",
                "PRECIO ARS": f"${cp_l:,.2f}",
                "LÍMITE COMPRA (TV)": f"${limite_compra_tv:,.2f}",
                "P&L NETO CONTABLE": f"{'+' if pnl_neto > 0 else ''}{fmt_money(pnl_neto)}",
                "NOMINALES SUGERIDOS": f"{sug_nominales_tv} Acc",
                "CAPITAL SUGERIDO": f"${st_cap:,.0f} ARS",
                "MONTO NETO TOTAL": fmt_money(monto_neto)
            })
            time.sleep(2) 
        except:
            continue

    st.dataframe(pd.DataFrame(mando_res), use_container_width=True, hide_index=True)
    st.info(f"💵 Tipo de Cambio Financiero Implícito: ${ccl_v:.2f} ARS | 🧠 Mando Central V162.1: **CONECTADO A CARTERA REAL**")

except Exception as e:
    st.error(f"Error de Sincronización: {e}")

# =============================================================================
# 🌐 ALERTA TEMPRANA & FRACTAL GLOBAL (100% DINÁMICO Y MÓVIL)
# =============================================================================
st.write("---")
st.markdown("### 🌐 Alerta Temprana & Panel Fractal Global")
macro_dict = {'DX-Y.NYB': 'DXY (Dólar Índice)', 'BZ=F': 'BRENT (Crudo)', 'GC=F': 'ORO (Refugio)', 'BTC-USD': 'BTC (Cripto)'}
cols_macro = st.columns(4)

for i, (tk, nom) in enumerate(macro_dict.items()):
    try:
        # Extraemos el valor del segundo exacto erradicando el hardcoding de parches del pasado
        valores_macro = raw_data[tk].values.ravel()
        val = float(valores_macro[-1])
        
        # Lentes Estructurales exactos: 5 días (Táctico) | 21 días (Estratégico) | 63 días (Búnker)
        f5 = "🔼" if val > float(valores_macro[-5]) else "🔽"
        f21 = "🔼" if val > float(valores_macro[-21]) else "🔽"
        f63 = "🔼" if val > float(valores_macro[-63]) else "🔽"
        
        with cols_macro[i]:
            st.metric(nom, f"{val:,.2f}" if "DXY" in nom or "BRENT" in nom or "ORO" in nom else f"${val:,.0f}")
            st.code(f"Fases: {f5} | {f21} | {f63}")
            
    except: 
        continue

st.sidebar.markdown("---")
st.sidebar.caption(f"Sentinel V162.1 | Combat Mode Activo | Brent Real: ${brent_live:.2f} USD")
