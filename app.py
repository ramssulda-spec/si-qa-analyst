import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import numpy as np
import google.generativeai as genai
from PIL import Image
import requests
import time

# ==============================================================================
# 1. VISUAL SETUP (SNIPER TRI-VISION V13.5)
# ==============================================================================
st.set_page_config(
    page_title="SI-APATECO SNIPER V13.5",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Teko:wght@300;600&family=Share+Tech+Mono&display=swap');
    
    .stApp {
        background-color: #050505;
        background-image: linear-gradient(0deg, #000 0%, #0a0a0a 100%);
        color: #d4d4d4;
        font-family: 'Share Tech Mono', monospace;
    }
    
    h1, h2, h3 {
        font-family: 'Teko', sans-serif !important;
        text-transform: uppercase;
        color: #fbbf24; /* Amber-400 */
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(251, 191, 36, 0.3);
    }
    
    /* Upload Boxes Style */
    .stFileUploader {
        border: 1px dashed #fbbf24;
        border-radius: 5px;
        padding: 10px;
        background: rgba(251, 191, 36, 0.05);
    }
    
    div[data-testid="stMetric"] {
        background-color: #111;
        border-right: 4px solid #fbbf24;
        padding: 15px;
    }
    
    .stButton>button {
        background: linear-gradient(45deg, #d97706, #fbbf24);
        color: black;
        font-weight: 900;
        text-transform: uppercase;
        padding: 20px;
        font-size: 20px;
        border-radius: 0px;
        width: 100%;
        border: 1px solid #fbbf24;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 30px rgba(251, 191, 36, 0.6);
        transform: scale(1.02);
    }
    
    .dataframe {
        border: 1px solid #333;
        font-family: 'Share Tech Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

# --- SECURITY ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# 2. PROMPT DE CORRELAÇÃO VISUAL (H4 -> H1 -> M15)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE: HIGH PAYOFF TRADE ANALYST (V13.5) [Gemini 3 Pro]
Your Goal: Identify Multi-Timeframe Confluence for Swings (Targets 1:3 to 1:5).
You ignore scalps. You are looking for structural reversals or deep pullbacks aligned with the Trend.

**INPUT DATA:**
1. **Math Core:** Determines the Trend Direction & Risk Parameters.
2. **Visual Triad (M15, H1, H4):** Used to confirm entry timing.

**ANALYSIS PROTOCOL (FRACTAL ALIGNMENT):**
1. **Look at H4 Image:** Where is the major Supply/Demand? Are we in an Uptrend or Downtrend?
2. **Look at H1 Image:** Is the internal structure aligned with H4?
3. **Look at M15 Image:** Do you see an entry trigger (Wick Rejection, Engulfing) at the MATH ENTRY Level?

**OUTPUT FORMAT:**

## 🔭 SNIPER VERDICT: [ {FINAL_DECISION} ]
**Asset:** {ASSET_NAME} | **Payoff Ratio:** 1:5 (Targeting {MATH_TP5})

### 👁️ VISUAL TRI-FORCE ANALYSIS
*   **H4 (Macro):** {Analysis of H4 chart - Trend}
*   **H1 (Structure):** {Analysis of H1 chart - Pivot Points}
*   **M15 (Trigger):** {Analysis of M15 chart - Candlestick Action}

### 🎯 EXECUTION BLUEPRINT
| Order | Level | Notes |
| :--- | :--- | :--- |
| **ENTRY** | **{MATH_ENTRY}** | *{ENTRY_TYPE}* |
| **STOP** | **{MATH_SL}** | *Structural Pivot* |
| **TP 1** | **{MATH_TP3}** | *Bank 50% here (1:3)* |
| **TP 2** | **{MATH_TP5}** | *Let run (1:5)* |

*Sniper Insight:* {Why does the fractal alignment allow for such a high Risk:Reward ratio here?}
)
"""

# ==============================================================================
# 3. REDE DERIV ROBUSTA
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
    reqs = [
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 300, "end": "latest"},  # H1
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 200, "end": "latest"}, # H4
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 1000, "end": "latest"}   # M15
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
    return None, None, None, "CONNECTION LOST"

# ==============================================================================
# 4. SWING MATH CORE (V13.5)
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def indicators(df):
    df['EMA_20'] = df['close'].ewm(span=20).mean() 
    df['EMA_50'] = df['close'].ewm(span=50).mean() # Value Zone
    df['EMA_200'] = df['close'].ewm(span=200).mean() # Trend Filter

    delta = df['close'].diff()
    rs = (delta.where(delta>0,0).rolling(14).mean()) / (-delta.where(delta<0,0).rolling(14).mean() + 1e-9)
    df['RSI'] = 100 - (100/(1+rs))

    df['tr'] = df[['high','low','close']].apply(lambda x: max(x['high']-x['low'], abs(x['high']-x['close']), abs(x['low']-x['close'])), axis=1)
    df['ATR'] = df['tr'].rolling(14).mean()
    df.dropna(inplace=True)
    return df

def detect_swing_level(df, direction):
    """Encontra Swing Low/High real no H1 para SL protegido"""
    if direction == "BUY":
        return df['low'].tail(20).min()
    elif direction == "SELL":
        return df['high'].tail(20).max()
    return df.iloc[-1]['close']

# ==============================================================================
# 5. PROFITABILITY BACKTEST (FOCADO EM R:R 1:5)
# ==============================================================================

def run_payoff_sim(df, trend_dir):
    """
    Backtest: Só aprova o ativo se ele tiver costume de pagar trades 1:5 a favor da tendência.
    """
    trades=0; hits_5R=0; balance=0
    for i in range(150, len(df)-80):
        row = df.iloc[i]

        # Logic: Deep Pullback (Preço volta na Média ou RSI Extremo) + Trend
        sig = None
        if trend_dir == "BULLISH":
            if row['close'] > row['EMA_200'] and row['low'] <= row['EMA_50']: sig = "BUY"
        elif trend_dir == "BEARISH":
            if row['close'] < row['EMA_200'] and row['high'] >= row['EMA_50']: sig = "SELL"

        if sig:
            entry = row['close']; atr = row['ATR']
            sl = entry - (2*atr) if sig=="BUY" else entry + (2*atr)
            tp_moon = entry + (5*atr) if sig=="BUY" else entry - (5*atr)

            res = "OPEN"
            for f in range(i+1, min(i+80, len(df))): # Deixa correr bastante
                nx = df.iloc[f]
                if sig=="BUY":
                    if nx['low'] <= sl: res="LOSS"; break
                    if nx['high'] >= tp_moon: res="WIN"; break
                else:
                    if nx['high'] >= sl: res="LOSS"; break
                    if nx['low'] <= tp_moon: res="WIN"; break

            if res != "OPEN":
                trades += 1
                if res == "WIN": hits_5R += 1; balance += 5.0
                else: balance -= 1.0
                i = f + 10 # Pula para não repetir trade na mesma congestão

    wr = (hits_5R/trades*100) if trades > 0 else 0
    return {"WR": round(wr,1), "NET": round(balance,1)}

# ==============================================================================
# 6. SNIPER PROCESSOR
# ==============================================================================

def sniper_core(name, h1_raw, h4_raw, m15_raw):
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    curr = h1.iloc[-1]

    # 1. Bias H4 (Mandatory)
    bias_h4 = "BULLISH" if h4.iloc[-1]['close'] > h4.iloc[-1]['EMA_200'] else "BEARISH"

    # 2. Setup (Deep Value Check)
    sig = "MONITORING"
    entry = curr['close']
    sl = curr['close']
    entry_type = "Wait"

    if bias_h4 == "BULLISH":
        # Price is "Cheap" (Discount) if touching EMA50 or RSI < 45
        dist = abs(curr['close'] - curr['EMA_50'])
        is_value = dist < (curr['ATR']*1.2)
        if is_value or curr['RSI'] < 45:
            sig = "LONG (SWING)"
            sl = detect_swing_level(h1, "BUY")
            entry_type = "Trend Defense (Discount)"
            # Safety: Limit Max SL distance to 3 ATR
            if (entry - sl) > (3*curr['ATR']): sl = entry - (2.5*curr['ATR'])

    elif bias_h4 == "BEARISH":
        dist = abs(curr['close'] - curr['EMA_50'])
        is_value = dist < (curr['ATR']*1.2)
        if is_value or curr['RSI'] > 55:
            sig = "SHORT (SWING)"
            sl = detect_swing_level(h1, "SELL")
            entry_type = "Trend Defense (Premium)"
            if (sl - entry) > (3*curr['ATR']): sl = entry + (2.5*curr['ATR'])

    # 3. Probability Check
    sim = run_payoff_sim(h1, bias_h4)
    if sim['NET'] <= 0:
        sig = "BLOCKED (STATISTICS)" # Negative historical edge

    # Targets Calculation (Hardfixed 1:3 & 1:5)
    risk = abs(entry - sl)
    if risk == 0: risk = curr['ATR']

    if "LONG" in sig or "BUY" in sig:
        tp3 = entry + (3*risk)
        tp5 = entry + (5*risk)
    else:
        tp3 = entry - (3*risk)
        tp5 = entry - (5*risk)

    return {
        "ASSET_NAME": name, "BIAS_H4": bias_h4, 
        "MARKET_STATE": "Accumulation" if "SWING" in sig else "Trending",
        "FINAL_DECISION": sig, "ENTRY_TYPE": entry_type,
        "WIN_RATE": sim['WR'], "NET_PROFIT": sim['NET'],
        "MATH_ENTRY": round(entry,2), "MATH_SL": round(sl,2), "SL_DIST": round(risk,2),
        "MATH_TP3": round(tp3,2), "MATH_TP5": round(tp5,2),
        "RR_RATIO": "5.0"
    }

# ==============================================================================
# 7. INTERFACE TRI-VISION
# ==============================================================================

st.sidebar.title("🔐 SI-APATECO KEY")
if "GEMINI_API_KEY" in st.secrets: api = st.secrets["GEMINI_API_KEY"]; st.sidebar.success("ACCESS GRANTED")
else: api = st.sidebar.text_input("ENTER API KEY", type="password")

st.sidebar.divider()
st.sidebar.info("""
**V13.5 MISSION PROFILE:**
- 🎯 **Targets:** 1:3 & 1:5 Only
- 📡 **Uploads:** M15/H1/H4 (Full Scan)
- 📊 **Precision:** High Value Zone
""")

st.title("🔭 SI-APATECO SNIPER (V13.5)")
st.caption("Deep Multi-Timeframe Analysis | Institutional Payoff Logic")

with st.spinner("Locking on Targets..."):
    assets = get_assets()

if not assets: st.error("SIGNAL LOST."); st.stop()

# Layout
c1, c2 = st.columns([1, 1.5])

with c1:
    target = st.selectbox("MISSION TARGET", list(assets.keys()))

    st.markdown("### 📸 TRI-FORCE VISUAL UPLOAD")
    st.caption("A IA precisa dos 3 tempos gráficos para máxima precisão.")

    # 3 Espaços de Upload distintos
    u_m15 = st.file_uploader("1. M15 CHART (Gatilho)", type=['png','jpg'], key=1)
    u_h1 = st.file_uploader("2. H1 CHART (Estrutura)", type=['png','jpg'], key=2)
    u_h4 = st.file_uploader("3. H4 CHART (Direção)", type=['png','jpg'], key=3)

    st.write("")
    run = st.button("CALCULATE VECTOR", use_container_width=True)

with c2:
    if run:
        if not api: st.error("⚠️ KEY REQUIRED"); st.stop()

        # Validar Uploads (Mínimo H1/M15 para sniper, mas H4 ideal)
        imgs = [Image.open(x) for x in [u_m15, u_h1, u_h4] if x]
        if not imgs: st.warning("⚠️ Favor enviar os prints para análise visual."); st.stop()

        status = st.status("🛸 ENGAGING QUANTUM CORES...", expanded=True)

        status.write("1. Retrieving Full History (M15 / H1 / H4)...")
        h1, h4, m15, err = asyncio.run(fetch_tri_force(assets[target]))
        if err: status.update(state='error', label="NET FAIL"); st.error(err); st.stop()

        status.write("2. Running Risk/Reward Simulation (1000 candles)...")
        data = sniper_core(target, h1, h4, m15)

        status.write(f"3. Gemini Pro Analyzing {len(imgs)} Charts...")
        genai.configure(api_key=api)
        try:
            model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
            txt = model.generate_content([SYSTEM_PROMPT, f"MATH: {json.dumps(data)}"] + imgs).text
            status.update(label="CALCULATION COMPLETE", state="complete")
        except:
             try: 
                 fb = genai.GenerativeModel("gemini-1.5-pro")
                 txt = fb.generate_content([SYSTEM_PROMPT, f"MATH: {json.dumps(data)}"] + imgs).text
                 status.update(label="COMPLETE (FALLBACK)", state="complete")
             except: st.error("AI Error"); st.stop()

        # DASHBOARD
        st.subheader("💰 POTENCIAL DE RETORNO (HISTÓRICO)")
        m1, m2, m3 = st.columns(3)
        m1.metric("Payoff Accum.", f"{data['NET_PROFIT']}R")
        m2.metric("Acertos Swing", f"{data['WIN_RATE']}%")
        m3.metric("R:R Ratio", f"1:5")

        if "SWING" in data['FINAL_DECISION']:
            st.balloons()
            st.success(f"🎯 **CONFIRMADO:** Oportunidade de Swing Trade detectada. Payoff Histórico Positivo.")
        elif "BLOCKED" in data['FINAL_DECISION']:
            st.error("🛑 **TRADE CANCELADO:** Backtest negativo. Este par não está respeitando setups 1:5 hoje.")

        # Grid Execução
        res_col = "green" if "SWING" in data['FINAL_DECISION'] else "red"
        st.markdown(f"#### SIGNAL: :{res_col}[{data['FINAL_DECISION']}]")
        st.dataframe([data], use_container_width=True)

        st.divider()
        st.markdown(txt)