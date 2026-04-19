import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from tradingview_ta import TA_Handler, Interval

# --- 🛰️ CONFIGURACIÓN SUPREME V105 ---
st.set_page_config(page_title="SENTINEL INSTITUTIONAL V105", page_icon="🛰️", layout="wide")

# --- 🎨 PROTOCOLOS VISUALES ---
def color_sentinel(val):
    if "🔥" in str(val) or "🛡️" in str(val): return 'background-color: #1B5E20; color: white'
    if "⚔️" in str(val) or "⚖️" in str(val): return 'background-color: #1A237E; color: white'
    if "🏹" in str(val): return 'background-color: #F57F17; color: white'
    if "⚠️" in str(val): return 'background-color: #B71C1C; color: white'
    return ''

def color_rsi(val):
    try:
        v = float(val)
        if v >= 70: return 'background-color: #B71C1C; color: white'
        if v <= 35: return 'background-color: #1B5E20; color: white'
    except: pass
    return ''

def color_gp(val):
    try:
        v = float(str(val).replace('%',''))
        return 'color: #2E7D32; font-weight: bold' if v > 0 else 'color: #C62828; font-weight: bold'
    except: return ''

# --- 🛠️ MOTOR QUANT & RATIOS ---
def obtener_brent_precio():
    try:
        brent = yf.Ticker("BZ=F").history(period="1d")
        return round(brent['Close'].iloc[-1], 2)
    except: return 0.0

def calcular_kelly(score_ia):
    b = 1.5 
    p = score_ia
    f_kelly = (p * (b + 1) - 1) / b
    return max(0, round(f_kelly / 4, 4))

def obtener_datos_tv(ticker):
    try:
        is_ba = ".BA" in ticker or "DICP" in ticker
        intervalo = Interval.INTERVAL_1_DAY if is_ba else Interval.INTERVAL_1_HOUR
        handler = TA_Handler(symbol=ticker.replace(".BA", ""), exchange="BCBA" if is_ba else "NASDAQ",
                            screener="argentina" if is_ba else "america", interval=intervalo)
        analysis = handler.get_analysis()
        return {'SEÑAL': analysis.summary['RECOMMENDATION'], 'RSI': round(analysis.indicators['RSI'], 2)}
    except: return {'SEÑAL': "NEUTRAL", 'RSI': 50.0}
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Descargamos el léxico (solo la primera vez)
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

def obtener_humor_sentinel(ticker):
    sia = SentimentIntensityAnalyzer()
    try:
        t = yf.Ticker(ticker)
        titulares = [n['title'] for n in t.news[:5]] 
        if not titulares: return 50.0, "⚖️ CALMA"
        
        scores = [sia.polarity_scores(tit)['compound'] for tit in titulares]
        avg = (sum(scores) / len(scores)) * 100
        
        if avg > 20: h = "🔥 CODICIA"
        elif avg < -20: h = "😱 MIEDO"
        else: h = "⚖️ CALMA"
        return round(avg, 1), h
    except: return 0.0, "⚖️ CALMA"

def get_price(t):
    try: 
        # Buscamos el precio más reciente (último minuto disponible)
        ticker = yf.Ticker(t)
        data = ticker.history(period="1d", interval="1m") # Intentamos capturar Asia
        
        if data.empty:
            # Si está vacío (mercado cerrado), buscamos el cierre del viernes
            data = ticker.history(period="5d")
            status_mercado = "🕒 CIERRE VIERNES"
        else:
            status_mercado = "🛰️ VIVO"
            
        p = data['Close'].iloc[-1]
        
        # Ajuste DICP
        if "DICP" in t: p = p * 100 if p < 1000 else p
            
        return round(p, 2)
    except: return 0.0

# --- 🕹️ GESTIÓN DE FLOTA Y SESIÓN ---
if 'liq' not in st.session_state: st.session_state.liq = 3800000.0

def cargar_flota():
    return {
        'YPFD.BA': {'unidades': 101, 'costo': 61951.0, 'score': 0.82, 'estado': "🛡️ HOLD"},
        'VIST.BA': {'unidades': 89, 'costo': 33103.14, 'score': 0.88, 'estado': "🛡️ HOLD"},
        'DICP.BA': {'unidades': 202, 'costo': 500.09, 'score': 0.75, 'estado': "⚓ BÚNKER"},
        'PAMP.BA': {'unidades': 0, 'costo': 0.0, 'score': 0.80, 'estado': "⌛ ACECHAR"}
    }

if 'flota' not in st.session_state: st.session_state.flota = cargar_flota()

# --- 📊 PROCESAMIENTO DE DATOS ---
df_radar = pd.DataFrame.from_dict(st.session_state.flota, orient='index').reset_index()
df_radar.columns = ['ACTIVO', 'UNIDADES', 'COSTO PROM', 'SCORE IA', 'ESTADO TÁCTICO']

df_radar['PRECIO ACT'] = df_radar['ACTIVO'].apply(get_price)
tv_data = df_radar['ACTIVO'].apply(obtener_datos_tv)
df_radar['RSI'] = [d['RSI'] for d in tv_data]
df_radar['SEÑAL TV'] = [d['SEÑAL'] for d in tv_data]
df_radar['MONTO NETO'] = df_radar['UNIDADES'] * df_radar['PRECIO ACT']
df_radar['G/P %'] = ((df_radar['PRECIO ACT'] - df_radar['COSTO PROM']) / df_radar['COSTO PROM']) * 100
df_radar['KELLY %'] = df_radar['SCORE IA'].apply(calcular_kelly)
df_radar['SUGERENCIA $'] = df_radar['KELLY %'] * st.session_state.liq

# --- 🧠 ACTIVACIÓN DEL NERVIO ÓPTICO ---
df_radar['HUMOR'] = df_radar['ACTIVO'].apply(obtener_humor_sentinel)

# --- 🏹 LÓGICA DE ACCIÓN TÁCTICA ---
def definir_accion(gp, kelly, rsi):
    if rsi > 70: return "⚠️ VENDER / GANANCIA"
    if rsi < 35 and kelly > 0.10: return "🔥 COMPRAR / PROMEDIAR"
    if gp < -5 and kelly > 0.05: return "🏹 ACECHAR RECOMPRA"
    return "⌛ MANTENER / VIGILAR"

df_radar['ACCIÓN'] = df_radar.apply(lambda x: definir_accion(x['G/P %'], x['KELLY %'], x['RSI']), axis=1)

# --- 🛰️ INTERFAZ VISUAL ---

# --- 🧠 ESCENARIO RESUMIDO (NOTAS DEL CAPITÁN) ---
precio_brent = obtener_brent_precio()

def generar_nota_resumen(df, brent):
    # 1. Alerta Brent
    if brent < 94.0 and brent > 0:
        return "🚨 **ESCENARIO: DESCOMPRESIÓN GEOPOLÍTICA.** El Brent cayó de u$s 99 a u$s 90. Es una tregua frágil. **ACCIÓN:** No perseguir subas, esperar piso en u$s 88."
    # 2. Alerta Insumos/Oro
    if "😱" in str(df['HUMOR'].values):
        return "⚠️ **ESCENARIO: MIEDO DETECTADO.** Los titulares hablan de inestabilidad. El Oro ($4,780) confirma que el dinero busca refugio."
    
    return f"🛰️ **ESTADO:** Brent en u$s {brent}. Mercado digiriendo la paz de Ormuz. Mantener liquidez ($3.8M) para el martes clave."

# Procesamos el humor para la tabla antes de mostrar la nota
humor_data = df_radar['ACTIVO'].apply(obtener_humor_sentinel)
df_radar['SCORE HUMOR'] = [h[0] for h in humor_data]
df_radar['HUMOR'] = [h[1] for h in humor_data]

# --- 🧠 NOTA DE ESCENARIO RESUMIDO (CFO ADVISOR) ---
# Usamos el precio del cierre para el análisis del domingo
if precio_brent == 0: precio_brent = 95.12 

def generar_nota_cfo(df, brent):
    # Alerta por descompresión de precios (La paz de Ormuz)
    if brent < 94.0:
        return f"🚨 **ESCENARIO: DESCOMPRESIÓN.** El Brent cayó a u$s {brent} por la paz en Ormuz. **ACCIÓN:** No perseguir subas, esperar piso en u$s 88 para usar los $3.8M."
    
    # Alerta por humor del mercado (Nervio Óptico)
    try:
        humores = df['HUMOR'].tolist()
        if "😱 MIEDO" in humores:
            return "⚠️ **ESCENARIO: MIEDO DETECTADO.** Los titulares hablan de inestabilidad. El Oro ($4,780) confirma que el dinero busca refugio."
    except: pass
    
    return f"🛰️ **ESTADO:** Brent en u$s {brent}. Mercado digiriendo la tregua. Mantener liquidez ($3.8M) para el martes clave."

# Mostramos la nota con el color correcto
nota_final = generar_nota_cfo(df_radar, precio_brent)
if "🚨" in nota_final: st.error(nota_final)
elif "⚠️" in nota_final: st.warning(nota_final)
else: st.info(nota_final)

# 2. BARRA LATERAL (INTELIGENCIA & RATIOS)
st.sidebar.header("🕹️ COMANDOS & NEWS")
ocultar = st.sidebar.toggle("👁️ Modo Privacidad")
def fmt(v): return "********" if ocultar else f"${v:,.0f}"

st.sidebar.write("### 🛰️ Sentinel Intelligence")
st.sidebar.metric("BRENT", f"📉 ${precio_brent}")
st.sidebar.metric("YPF_JUDICIAL", "⚖️ FALLO NULO")
st.sidebar.metric("ORO (NEM)", "🔥 $4.780")

# SENSOR DE RATIO YPF/PAMPA
ypf_p = df_radar.loc[df_radar['ACTIVO'] == 'YPFD.BA', 'PRECIO ACT'].values[0]
pamp_p = get_price('PAMP.BA')
if pamp_p > 0:
    ratio = ypf_p / pamp_p
    desv = (ratio / 14.5 - 1) * 100
    st.sidebar.write(f"📊 **Ratio YPF/Pampa:** {ratio:.2f}")
    if desv > 5: st.sidebar.warning(f"⚠️ YPF Caro ({desv:.1f}%)")
    elif desv < -5: st.sidebar.success(f"💎 YPF Barato ({desv:.1f}%)")
    else: st.sidebar.write("✅ Ratio en Equilibrio")

# 3. MÉTRICAS DE CAPITAL
cap_inv = df_radar['MONTO NETO'].sum()
c1, c2, c3 = st.columns(3)
c1.metric("🛡️ Capital Búnker", fmt(cap_inv + st.session_state.liq))
c2.metric("⚔️ Inversión Activa", fmt(cap_inv))
c3.metric("💵 Liquidez", fmt(st.session_state.liq))

# --- 4. TABLA DE CONTROL QUANT ---
st.write("### 📊 Despliegue de Flota (Gestión de Kelly)")

def calcular_paz(score, estado):
    # Lógica de blindaje para la jubilación
    base = score + (0.05 if "🛡️" in str(estado) else 0)
    valor = round(min(base, 1.0), 2)
    if valor >= 0.90: return f"{valor} (🛡️ ACORAZADO)"
    elif valor >= 0.80: return f"{valor} (⚖️ EQUILIBRADO)"
    return f"{valor} (⚠️ VIGILAR)"

df_radar['PAZ MENTAL'] = df_radar.apply(lambda x: calcular_paz(x['SCORE IA'], x['ESTADO TÁCTICO']), axis=1)

# Orden de columnas Institucional
columnas_orden = ['ACTIVO', 'ACCIÓN','HUMOR', 'PAZ MENTAL', 'SCORE IA', 'PRECIO ACT', 'G/P %', 'RSI', 'KELLY %', 'SUGERENCIA $', 'MONTO NETO']

st.dataframe(
    df_radar[columnas_orden].style.map(color_sentinel, subset=['ACCIÓN'])
    .map(color_rsi, subset=['RSI'])
    .map(color_gp, subset=['G/P %'])
    .format({
        'PRECIO ACT': '${:,.2f}', 
        'SCORE IA': '{:.2f}', 
        'G/P %': '{:.2f}%', 
        'RSI': '{:.2f}',
        'KELLY %': '{:.2%}', 
        'SUGERENCIA $': '${:,.0f}', 
        'MONTO NETO': '${:,.2f}'
    }),
    use_container_width=True, 
    hide_index=True
)

# --- 🛰️ RADAR DE INCONGRUENCIAS GLOBAL (CIERRE DEL BÚNKER) ---
st.write("---")
st.write("### 🛰️ Radar de Incongruencias (IA & Energía Global)")
radar_global = ['NVDA', 'TSM', 'ASML', 'YPF', 'VIST', 'PAMP.BA', 'MSFT', 'GLD', 'CCJ', 'CAT']

try:
    df_g = yf.download(radar_global, period="6mo", interval="1d", progress=False)['Close'].ffill()
    cols = st.columns(len(radar_global))
    for i, t in enumerate(sorted(radar_global)):
        p = df_g[t].iloc[-1]
        f5 = "🔼" if p > df_g[t].iloc[-5] else "🔽"
        f21 = "🔼" if p > df_g[t].iloc[-21] else "🔽"
        f63 = "🔼" if p > df_g[t].iloc[-63] else "🔽"
        with cols[i]:
            st.code(f"{t}\n{f5}|{f21}|{f63}")
except:
    st.warning("Reconectando satélites...")
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Descargamos el léxico necesario la primera vez
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

def obtener_humor_mercado(ticker):
    sia = SentimentIntensityAnalyzer()
    try:
        stock = yf.Ticker(ticker)
        # Extraemos los titulares de las noticias (news) del ticker
        titulares = [n['title'] for n in stock.news[:5]] 
        if not titulares: return 50.0, "⚪ NEUTRAL"
        
        scores = [sia.polarity_scores(t)['compound'] for t in titulares]
        avg_score = (sum(scores) / len(scores)) * 100 # Escala -100 a 100
        
        # Mapeo a Humor Sentinel
        if avg_score > 20: humor = "🔥 CODICIA"
        elif avg_score < -20: humor = "😱 MIEDO"
        else: humor = "⚖️ CALMA"
        
        return round(avg_score, 1), humor
    except:
        return 50.0, "⚪ NEUTRAL"

import pandas as pd
import os

LOG_FILE = "historial_sentinel.csv"

def registrar_operacion(ticker, precio_venta, rsi_venta):
    # Guardamos los datos de tu salida
    nuevo_dato = pd.DataFrame([{
        'fecha': pd.Timestamp.now(),
        'ticker': ticker,
        'precio': precio_venta,
        'rsi': rsi_venta
    }])
    
    if not os.path.isfile(LOG_FILE):
        nuevo_dato.to_csv(LOG_FILE, index=False)
    else:
        nuevo_dato.to_csv(LOG_FILE, mode='a', header=False, index=False)

def sugerencia_aprendizaje_ml(ticker, rsi_actual):
    if not os.path.isfile(LOG_FILE): return ""
    
    df_hist = pd.read_csv(LOG_FILE)
    df_ticker = df_hist[df_hist['ticker'] == ticker]
    
    if len(df_ticker) > 2:
        # Si históricamente vendiste con RSI 70 y el precio siguió subiendo
        # el bot te dirá que vendas antes (ej: RSI 65)
        avg_rsi_venta = df_ticker['rsi'].mean()
        if rsi_actual >= (avg_rsi_venta - 5):
            return "🧠 ML: Salida histórica detectada. ¡Ojo con el 'timing'!"
    return ""
