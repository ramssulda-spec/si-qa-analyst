import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import numpy as np
import google.generativeai as genai
from PIL import Image
import time

# ==============================================================================
# 1. CONFIGURAÇÕES VISUAIS (GOD MODE V11.1)
# ==============================================================================
st.set_page_config(
    page_title="SI-APATECO GOD MODE V11.1",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;700&family=Zen+Dots&display=swap');
    
    .stApp {
        background-color: #000;
        background-image: radial-gradient(circle at 50% 10%, #1c0029 0%, #000 60%);
        color: #e0e0e0;
        font-family: 'Rajdhani', sans-serif;
    }
    
    /* TITLES */
    h1, h2 {
        font-family: 'Zen Dots', cursive !important;
        text-transform: uppercase;
        background: linear-gradient(120deg, #d400ff, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(212, 0, 255, 0.4);
    }
    
    /* GLASS CARDS */
    div[data-testid="stMetric"] {
        background: rgba(10, 10, 10, 0.8);
        border: 1px solid #333;
        box-shadow: 0 0 15px rgba(0, 200, 255, 0.1);
        border-radius: 4px;
        padding: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Zen Dots';
        font-size: 1.6rem !important;
        color: #00d4ff !important;
    }
    div[data-testid="stMetricLabel"] { color: #888; }
    
    /* DATAFRAME */
    .dataframe {
        font-family: 'Rajdhani', monospace !important;
        font-size: 14px !important;
        background-color: #050505;
        border: 1px solid #444;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #3700b3, #03dac6);
        color: white;
        border: none;
        padding: 20px;
        font-family: 'Zen Dots';
        letter-spacing: 3px;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        letter-spacing: 5px;
        box-shadow: 0 0 30px rgba(3, 218, 198, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- SEGURANÇA ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# 2. PROMPT OMNISCIENTE (ALINHAMENTO FRACTAL + HISTÓRICO)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE: SI-APATECO "GOD MODE" (V11.1) [Gemini 3 Pro]
Your Purpose: Detect Perfect Fractal Alignment validated by Historical Backtests.

INPUT MATRIX (PYTHON TRUTH):
1. **FRACTAL SCORE (0-3):** Agreement between M15, H1, H4. (Must be > 1 for valid entry).
2. **HISTORICAL BACKTEST:** {WIN_RATE}% accuracy in last 1000 candles. 
   - IF WR < 45% -> CAUTION. 
   - IF WR > 60% -> AGGRESSIVE.
3. **SMC STRUCTURE:** Sweeps & Compression Squeezes.

OUTPUT PROTOCOL (Markdown):

## 👁️ GOD MODE VERDICT: [ {FINAL_DECISION} ]
**Asset:** {ASSET_NAME} | **Probability:** {WIN_RATE}% (Net: {NET_PROFIT}R)

### 🌐 MATRIX ALIGNMENT
*   **H4 (Trend):** {BIAS_H4}
*   **H1 (Flow):** {BIAS_H1}
*   **M15 (Entry):** {BIAS_M15}
*   **Vol. State:** {COMPRESSION_STATE}

### 🎯 QUANTUM EXECUTION
| Order | Level | Confluence Logic |
| :--- | :--- | :--- |
| **ENTRY** | **{MATH_ENTRY}** | *{ENTRY_NOTE}* |
| **STOP LOSS** | **{MATH_SL}** | *Structural Pivot* |
| **TP 1** | **{MATH_TP1}** | *Risk 1:2* |
| **TP 2** | **{MATH_TP2}** | *Extension* |

*God Mode Insight:* {Synthesize why Fractal Score + Backtest Result justifies this specific trade.}
)
"""

# ==============================================================================
# 3. CONEXÃO ROBUSTA (DERIV FAILOVER)
# ==============================================================================
DERIV_SERVERS = [
    "wss://ws.binaryws.com/websockets/v3?app_id=1089",      
    "wss://ws.derivws.com/websockets/v3?app_id=1089",       
    "wss://green.binaryws.com/websockets/v3?app_id=1089"
]

async def socket_req(url, req):
    try:
        async with websockets.connect(url, ping_interval=None, close_timeout=10) as ws:
            await ws.send(json.dumps(req))
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
    except: return None

@st.cache_data(ttl=3600)
def get_assets():
    req = {"active_symbols": "brief", "product_type": "basic"}
    for url in DERIV_SERVERS:
        res = asyncio.run(socket_req(url, req))
        if res and 'active_symbols' in res:
            return {x['display_name'].upper(): x['symbol'] for x in res['active_symbols'] if x['market']=='synthetic_index'}
    return None

async def fetch_tri_force(code):
    # Aumentei o M15 para 1000 velas para garantir Backtest sólido
    reqs = [
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 1000, "end": "latest"}, 
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 200, "end": "latest"}, 
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 200, "end": "latest"} 
    ]
    
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=None) as ws:
                data = []
                for r in reqs:
                    await ws.send(json.dumps(r))
                    raw = json.loads(await asyncio.wait_for(ws.recv(), 15))
                    if 'candles' in raw: data.append(raw['candles'])
                    else: break
                
                if len(data) == 3: return data[0], data[1], data[2], None
        except: continue
    return None, None, None, "SYSTEM FAILURE: DISCONNECTED"

# ==============================================================================
# 4. MATH CORE & INDICATORS
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def indicators(df):
    delta = df['close'].diff()
    gain = (delta.where(delta>0,0)).rolling(14).mean()
    loss = (-delta.where(delta<0,0)).rolling(14).mean()
    rs = gain/(loss+1e-9)
    df['RSI'] = 100 - (100/(1+rs))
    
    df['EMA_50'] = df['close'].ewm(span=50).mean()
    df['EMA_200'] = df['close'].ewm(span=200).mean()
    
    # ATR (Usado no Backtest)
    df['tr'] = df[['high','low','close']].apply(lambda x: max(x['high']-x['low'], abs(x['high']-x['close']), abs(x['low']-x['close'])), axis=1)
    df['ATR'] = df['tr'].rolling(14).mean()
    df.dropna(inplace=True)
    return df

def detect_squeeze(df):
    """Bollinger Band Squeeze"""
    sma = df['close'].rolling(20).mean(); std = df['close'].rolling(20).std()
    bw = ((sma + 2*std) - (sma - 2*std)) / sma
    return "⚡ HIGH COMPRESSION" if bw.iloc[-1] <= bw.rolling(50).min().iloc[-1] * 1.1 else "EXPANDED"

def get_fvg_target(df):
    df = df.tail(30).reset_index(drop=True)
    for i in range(len(df)-2, 2, -1):
        if df.iloc[i-2]['low'] > df.iloc[i]['high']:
            return {'type':'BEARISH', 'p': (df.iloc[i-2]['low']+df.iloc[i]['high'])/2}
        if df.iloc[i-2]['high'] < df.iloc[i]['low']:
            return {'type':'BULLISH', 'p': (df.iloc[i-2]['high']+df.iloc[i]['low'])/2}
    return None

def find_swings_fix(df, window=5):
    # Logica protegida contra erro do Pandas 2.0+
    lows = df['low'].rolling(window=2*window+1, center=True).min()
    highs = df['high'].rolling(window=2*window+1, center=True).max()
    
    df['is_low'] = df['low'] == lows
    df['is_high'] = df['high'] == highs
    
    last_low = df[df['is_low']].iloc[-1]['low'] if df['is_low'].any() else df['low'].min()
    last_high = df[df['is_high']].iloc[-1]['high'] if df['is_high'].any() else df['high'].max()
    return last_low, last_high

# ==============================================================================
# 5. RESTORED BACKTEST ENGINE
# ==============================================================================

def run_backtest_stats(df, name):
    trades=0; wins=0; balance=0
    # Começa na vela 200 para garantir dados de indicadores
    for i in range(200, len(df)-60):
        row = df.iloc[i]
        
        # Filtros de Backtest (Replica lógica básica de entrada)
        bull = row['close'] > row['EMA_200']
        bear = row['close'] < row['EMA_200']
        
        sig = None
        if "BOOM" in name and bull and row['RSI']<40: sig="BUY"
        elif "CRASH" in name and bear and row['RSI']>60: sig="SELL"
        elif "STEP" in name or "VOLATILITY" in name:
            if bull and row['RSI']<30: sig="BUY"
            if bear and row['RSI']>70: sig="SELL"
            
        if sig:
            entry = row['close']; atr = row['ATR']
            # TP mais longo (3R) e SL (1.5R) para validar consistencia
            sl = entry - 2*atr if sig=="BUY" else entry + 2*atr
            tp = entry + 6*atr if sig=="BUY" else entry - 6*atr
            
            res = "OPEN"
            for f in range(i+1, min(i+60, len(df))):
                if sig=="BUY":
                    if df.iloc[f]['low'] <= sl: res="LOSS"; break
                    if df.iloc[f]['high'] >= tp: res="WIN"; break
                else:
                    if df.iloc[f]['high'] >= sl: res="LOSS"; break
                    if df.iloc[f]['low'] <= tp: res="WIN"; break
            
            if res!="OPEN":
                trades+=1
                if res=="WIN": wins+=1; balance+=3.0
                else: balance-=1.0
                i=f # Pula
    
    wr = (wins/trades*100) if trades>0 else 0
    return {"WR": round(wr,1), "N": trades, "R": round(balance,2)}

# ==============================================================================
# 6. ORACLE PROCESSOR
# ==============================================================================

def run_god_engine(name, m15_raw, h1_raw, h4_raw):
    # Processa Dados
    m15 = indicators(prep_df(m15_raw))
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    
    # 1. Roda Backtest Primeiro
    bt = run_backtest_stats(m15, name)
    
    # 2. Fractal Matrix
    def get_bias(d): return "BULLISH" if d.iloc[-1]['close'] > d.iloc[-1]['EMA_50'] else "BEARISH"
    b_m15 = get_bias(m15); b_h1 = get_bias(h1); b_h4 = get_bias(h4)
    
    fractal_score = 0
    if b_h1 == b_h4: fractal_score += 2 # Peso maior para H1+H4
    if b_m15 == b_h4: fractal_score += 1
    
    # 3. Market State
    compression = detect_squeeze(m15)
    fvg = get_fvg_target(m15)
    s_low, s_high = find_swings_fix(m15)
    curr = m15.iloc[-1]['close']; rsi = m15.iloc[-1]['RSI']
    
    sig="WAIT"; note="Low Probability"; entry=curr
    
    # Logic: Backtest Check + Fractal Sync
    strong_setup = fractal_score >= 2 or ("COMPRESSION" in compression)
    
    if "BOOM" in name:
        if b_h4 == "BULLISH" and rsi < 45:
            sig = "BUY (TREND)"
            if fvg and fvg['type']=='BULLISH': entry = fvg['p']; note="FVG Entry"
            else: note="Trend Pullback"
    elif "CRASH" in name:
        if b_h4 == "BEARISH" and rsi > 55:
            sig = "SELL (TREND)"
            if fvg and fvg['type']=='BEARISH': entry = fvg['p']; note="FVG Entry"
            else: note="Trend Pullback"
    else:
        if strong_setup:
            if b_h4 == "BULLISH" and rsi < 40: sig = "BUY"; note="Aligned Flow"
            elif b_h4 == "BEARISH" and rsi > 60: sig = "SELL"; note="Aligned Flow"

    # Risk Calc
    atr = m15.iloc[-1]['ATR']
    if "BUY" in sig:
        sl = s_low if s_low < entry else entry - 2*atr
        tp1 = entry + abs(entry-sl)*2
        tp2 = entry + abs(entry-sl)*4
    else: # SELL
        sl = s_high if s_high > entry else entry + 2*atr
        tp1 = entry - abs(entry-sl)*2
        tp2 = entry - abs(entry-sl)*4
        
    return {
        "ASSET_NAME": name, "FRACTAL_SCORE": fractal_score,
        "BIAS_H4": b_h4, "BIAS_H1": b_h1, "BIAS_M15": b_m15,
        "COMPRESSION_STATE": compression, "FINAL_DECISION": sig,
        "ENTRY_NOTE": note, "WIN_RATE": bt['WR'], "NET_PROFIT": bt['R'], "TOTAL_TRADES": bt['N'],
        "MATH_ENTRY": round(entry,2), "MATH_SL": round(sl,2),
        "MATH_TP1": round(tp1,2), "MATH_TP2": round(tp2,2)
    }

# ==============================================================================
# 7. INTERFACE
# ==============================================================================
st.sidebar.image("https://img.icons8.com/nolan/64/all-seeing-eye.png", width=60)
st.sidebar.title("ACCESS V11.1")
if "GEMINI_API_KEY" in st.secrets: api = st.secrets["GEMINI_API_KEY"]; st.sidebar.success("LINKED")
else: api = st.sidebar.text_input("ENTER KEY", type="password")

st.sidebar.info("""
**V11.1 FEATURES:**
- 📐 **Fractal Matrix:** 3 Timeframes.
- 📜 **Backtest Stats:** Restored.
- 🤖 **AI:** Gemini 3 Pro.
""")

st.title("👁️ SI-APATECO GOD MODE")
st.caption("THE TRI-FORCE ENGINE: Historical Probability + Present Fractal Alignment")

with st.spinner("Connecting to Quantum Matrix..."):
    assets = get_assets()

if not assets:
    st.error("🔴 DISCONNECTED. Check Network."); st.stop()

col1, col2 = st.columns([1,2])
with col1:
    target = st.selectbox("ASSET", list(assets.keys()))
    st.markdown("---")
    u_m15 = st.file_uploader("M15 (Entry)", type=['png','jpg'], key=1)
    u_h1 = st.file_uploader("H1 (Flow)", type=['png','jpg'], key=2)
    u_h4 = st.file_uploader("H4 (Vector)", type=['png','jpg'], key=3)
    st.markdown("---")
    run = st.button("INITIATE SEQUENCE", use_container_width=True)

with col2:
    if run:
        if not api: st.error("⚠️ KEY MISSING"); st.stop()
        imgs = [Image.open(x) for x in [u_m15,u_h1,u_h4] if x]
        if not imgs: st.warning("⚠️ M15 IMAGE REQUIRED"); st.stop()
        
        status = st.status("🛸 CALCULATING...", expanded=True)
        
        status.write("1. Downloading 1000 candles (History)...")
        m15, h1, h4, err = asyncio.run(fetch_tri_force(assets[target]))
        if err: status.update(state="error", label="NET FAIL"); st.error(err); st.stop()
        
        status.write("2. Running Historical Backtest & Fractal Matrix...")
        data = run_god_engine(target, m15, h1, h4)
        
        status.write("3. Consulting Oracle (Gemini)...")
        genai.configure(api_key=api)
        try:
            model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
            txt = model.generate_content([SYSTEM_PROMPT, f"MATRIX_JSON: {json.dumps(data)}"] + imgs).text
            status.update(label="GOD MODE RESULT", state="complete")
        except:
             txt = "⚠️ AI Fail (Visual). Use Data."
             status.update(label="DONE (DATA ONLY)", state="complete")

        # DASHBOARD
        
        # CARD DE BACKTEST (VOLTOU)
        st.subheader("📊 PROBABILIDADE & BACKTEST")
        b1, b2, b3 = st.columns(3)
        b1.metric("Win Rate", f"{data['WIN_RATE']}%")
        b2.metric("Saldo (R)", f"{data['NET_PROFIT']}R")
        b3.metric("Trade Bias", data['FINAL_DECISION'])
        
        if data['WIN_RATE'] > 60: st.success("✅ Ativo em condições EXCELENTES para a estratégia.")
        elif data['WIN_RATE'] < 40: st.error("⚠️ CUIDADO: Backtest negativo recente. Requer confirmação extra.")
        
        st.divider()
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Bias H4", data['BIAS_H4'])
        k2.metric("Bias H1", data['BIAS_H1'])
        k3.metric("Vol. State", "⚠️ COMPRESSION" if "COMPRESSION" in data['COMPRESSION_STATE'] else "NORMAL")
        k4.metric("Fractal Score", f"{data['FRACTAL_SCORE']}/3")
        
        st.dataframe([data], use_container_width=True)
        st.markdown(txt)
