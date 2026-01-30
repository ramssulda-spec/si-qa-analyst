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
# 1. VISUAL (SI-APATECO BLACK BOX V10)
# ==============================================================================
st.set_page_config(
    page_title="SI-APATECO V10 ENDGAME",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Red+Hat+Mono:wght@300;700&family=Syncopate:wght@700&display=swap');
    
    /* Ambiente Black Box */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(135deg, #0a0a0a 25%, #000000 100%);
        color: #dcdcdc;
        font-family: 'Red Hat Mono', monospace;
    }
    
    h1, h2, h3 {
        font-family: 'Syncopate', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        background: -webkit-linear-gradient(0deg, #c471ed, #f64f59);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Metrics estilo Dashboard Financeiro */
    div[data-testid="stMetric"] {
        background: #050505;
        border-left: 4px solid #f64f59;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Red Hat Mono', monospace;
        font-weight: 700;
        font-size: 1.5rem !important;
        color: #fff !important;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #12c2e9, #c471ed, #f64f59);
        color: white;
        border: none;
        padding: 15px 30px;
        text-transform: uppercase;
        font-family: 'Syncopate', sans-serif;
        font-weight: bold;
        transition: 0.3s ease;
        border-radius: 0px;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(246, 79, 89, 0.4);
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
# 2. PROMPT "BLACK BOX" (LÓGICA SMC INSTITUCIONAL)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE: SI-APATECO "BLACK BOX" [Gemini 3 Pro]
Your Objective: Analyze Mathematical Liquidity & Structure to output High Probability Trades.
Ignore all News. Synthetic Indices follow Algo-Patterns only.

INPUT DATA (Source of Truth):
1. **SWEEP STATUS:** Has price just grabbed liquidity (false breakout)? This is a massive confirmation.
2. **ZONE (FIBONACCI):** Premium (Sell Only) vs Discount (Buy Only).
3. **DIVERGENCE:** RSI Disagreement.

OUTPUT FORMAT (Markdown):

## ♟️ ALGORITHM VERDICT: [ {FINAL_DECISION} ]
**Asset:** {ASSET_NAME} | **Algo-Confidence:** {WIN_RATE}%

### 🕶️ INSTITUTIONAL DATA
*   **Liquidity Sweep:** {SWEEP_DETECTED} (Hunt Logic)
*   **Fibonacci Zone:** Trading in **{FIB_ZONE}** (Favors {FIB_FAVORS})
*   **Macro Bias (H4):** {MACRO_TREND}

### 🎯 EXECUTION MATRIX
| Order Type | Price Level | Logic |
| :--- | :--- | :--- |
| **ENTRY** | **{MATH_ENTRY}** | *{ENTRY_TYPE}* |
| **STOP LOSS** | **{MATH_SL}** | *Protected by Sweep/Structure* |
| **TARGET 1** | **{MATH_TP1}** | *1:2 RR* |
| **TARGET 2** | **{MATH_TP2}** | *Run Liquidity* |

### 🧬 STRATEGY SYNTHESIS:
{Synthesize the data: E.g., "Although Trend is Bearish, we are in deep Discount and just Swept Liquidity Lows with Bullish Divergence. A counter-trend Reversal is highly probable." OR "Trend is Bearish, we are in Premium, and price tapped a Bearish FVG. Continuation Short."}
)
"""

# ==============================================================================
# 3. CONECTIVIDADE BLINDADA
# ==============================================================================
DERIV_SERVERS = [
    "wss://ws.binaryws.com/websockets/v3?app_id=1089",      
    "wss://ws.derivws.com/websockets/v3?app_id=1089",       
    "wss://green.binaryws.com/websockets/v3?app_id=1089",
    "wss://blue.binaryws.com/websockets/v3?app_id=1089"
]

async def connect_socket(url, msg):
    try:
        async with websockets.connect(url, ping_interval=None, close_timeout=10) as ws:
            await ws.send(json.dumps(msg))
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
    except: return None

@st.cache_data(ttl=3600)
def get_assets():
    req = {"active_symbols": "brief", "product_type": "basic"}
    for url in DERIV_SERVERS:
        data = asyncio.run(connect_socket(url, req))
        if data and 'active_symbols' in data:
            return {x['display_name'].upper(): x['symbol'] for x in data['active_symbols'] if x['market']=='synthetic_index'}
    return None

async def fetch_data_safe(code):
    req_m15 = {"ticks_history": code, "style": "candles", "granularity": 900, "count": 1000, "adjust_start_time": 1, "end": "latest"}
    req_h4 = {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 250, "adjust_start_time": 1, "end": "latest"}
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=None) as ws:
                await ws.send(json.dumps(req_m15)); m15 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                await ws.send(json.dumps(req_h4)); h4 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                if 'candles' in m15 and 'candles' in h4: return m15['candles'], h4['candles'], None
        except: continue
    return None, None, "FALHA TOTAL DE REDE (BLOQUEIO)."

# ==============================================================================
# 4. MATH CORE (V10 FEATURES: SWEEP + PRICING)
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def indicators_v10(df):
    delta = df['close'].diff()
    gain = (delta.where(delta>0,0)).rolling(14).mean(); loss = (-delta.where(delta<0,0)).rolling(14).mean()
    df['RSI'] = 100 - (100/(1 + (gain/(loss+1e-9))))
    
    df['EMA_50'] = df['close'].ewm(span=50).mean()
    df['EMA_200'] = df['close'].ewm(span=200).mean()
    
    # ATR Institucional
    df['tr'] = df[['high','low','close']].apply(lambda x: max(x['high']-x['low'], abs(x['high']-x['close']), abs(x['low']-x['close'])), axis=1)
    df['ATR'] = df['tr'].rolling(14).mean()
    
    df.dropna(inplace=True)
    return df

def get_fib_pricing(df, lookback=50):
    """SMC: Compra em Discount (<50%), Vende em Premium (>50%)"""
    high = df['high'].tail(lookback).max()
    low = df['low'].tail(lookback).min()
    mid = (high + low) / 2
    curr = df.iloc[-1]['close']
    
    zone = "PREMIUM 🔴" if curr > mid else "DISCOUNT 🟢"
    favors = "SHORT" if curr > mid else "LONG"
    return zone, favors

def detect_liquidity_sweep(df):
    """
    Detecta 'Turtle Soup': O preço violou um fundo/topo anterior
    mas fechou o corpo DENTRO da estrutura (Rejeição/Wick).
    """
    recent = df.tail(10)
    last = recent.iloc[-1]
    
    # Varrer Liquidez de Baixa (Bullish Sweep)
    prev_low = df['low'].iloc[-20:-5].min()
    bullish_sweep = (last['low'] < prev_low) and (last['close'] > prev_low)
    
    # Varrer Liquidez de Alta (Bearish Sweep)
    prev_high = df['high'].iloc[-20:-5].max()
    bearish_sweep = (last['high'] > prev_high) and (last['close'] < prev_high)
    
    if bullish_sweep: return "BULLISH SWEEP (Liquidity Grabbed) 🐂"
    if bearish_sweep: return "BEARISH SWEEP (Liquidity Grabbed) 🐻"
    return "NONE (Inside Range)"

def detect_rsi_div(df):
    p = df['close'].tail(15).values; r = df['RSI'].tail(15).values
    # Logica simplificada robusta de Slope Divergence
    if (p[-1] < p[0]) and (r[-1] > r[0]): return "BULLISH DIV (STRONG)"
    if (p[-1] > p[0]) and (r[-1] < r[0]): return "BEARISH DIV (STRONG)"
    return "NEUTRAL"

def get_fvg(df):
    rc = df.tail(40).reset_index(drop=True)
    fvg = None
    for i in range(len(rc)-2, 2, -1):
        if rc.iloc[i-2]['low'] > rc.iloc[i]['high']:
            mitigated = False
            mid = (rc.iloc[i-2]['low'] + rc.iloc[i]['high'])/2
            for j in range(i+1, len(rc)): 
                if rc.iloc[j]['high'] >= mid: mitigated=True
            if not mitigated: fvg = {'type':'BEARISH', 'p':mid}; break
            
        elif rc.iloc[i-2]['high'] < rc.iloc[i]['low']:
            mitigated = False
            mid = (rc.iloc[i-2]['high'] + rc.iloc[i]['low'])/2
            for j in range(i+1, len(rc)): 
                if rc.iloc[j]['low'] <= mid: mitigated=True
            if not mitigated: fvg = {'type':'BULLISH', 'p':mid}; break
    return fvg

# ==============================================================================
# 5. BACKTEST ALIGNMENT ENGINE (V10)
# ==============================================================================
def run_backtest(df, name):
    trades=0; wins=0; bal=0
    for i in range(100, len(df)-60):
        row=df.iloc[i]
        
        # Simulando Regra de Ouro (Discount/Premium)
        local_high = df['high'].iloc[i-50:i].max()
        local_low = df['low'].iloc[i-50:i].min()
        mid = (local_high+local_low)/2
        is_discount = row['close'] < mid
        is_premium = row['close'] > mid
        
        sig = None
        trend = row['close'] > row['EMA_200']
        
        # Boom Logic: Compra na tendência e em Discount ou Sobrevenda
        if "BOOM" in name:
            if trend and (row['RSI'] < 40 or is_discount): sig='BUY'
        # Crash Logic: Venda na tendência e em Premium ou Sobrecompra
        elif "CRASH" in name:
            if not trend and (row['RSI'] > 60 or is_premium): sig='SELL'
        else:
            if trend and is_discount and row['RSI'] < 40: sig='BUY'
            if not trend and is_premium and row['RSI'] > 60: sig='SELL'
            
        if sig:
            ent = row['close']; atr = row['ATR']
            sl = ent - 2*atr if sig=='BUY' else ent + 2*atr
            tp = ent + 4*atr if sig=='BUY' else ent - 4*atr
            
            res="OPEN"
            for f in range(i+1, min(i+60, len(df))):
                nx = df.iloc[f]
                if sig=='BUY':
                    if nx['low']<=sl: res='LOSS'; break
                    if nx['high']>=tp: res='WIN'; break
                else:
                    if nx['high']>=sl: res='LOSS'; break
                    if nx['low']<=tp: res='WIN'; break
            
            if res!='OPEN':
                trades+=1
                if res=='WIN': wins+=1; bal+=2
                else: bal-=1
                i=f
    
    return {"WR": round((wins/trades*100) if trades>0 else 0, 1), "N": trades, "P": round(bal, 2)}

# ==============================================================================
# 6. BLACK BOX CORE
# ==============================================================================
def black_box_logic(name, m15_raw, h4_raw):
    m15 = indicators_v10(prep_df(m15_raw))
    h4 = indicators_v10(prep_df(h4_raw))
    bt = run_backtest(m15, name)
    
    curr = m15.iloc[-1]
    
    # 1. H4 Trend
    bias_h4 = "BULLISH" if h4.iloc[-1]['close'] > h4.iloc[-1]['EMA_50'] else "BEARISH"
    
    # 2. SMC Checkpoint
    zone, zone_favors = get_fib_pricing(m15)
    sweep = detect_liquidity_sweep(m15)
    div = detect_rsi_div(m15)
    fvg = get_fvg(m15)
    
    sig = "WAIT / MONITOR"
    entry=curr['close']; sl=curr['close']; tp1=curr['close']; tp2=curr['close']
    type_txt = "Market Price"

    # LOGICA ENDGAME
    # Se BOOM -> Procura Spike. Confluências: Bias Bull, Zona Discount, Sweep de baixa ou Div.
    if "BOOM" in name:
        buy_score = 0
        if bias_h4 == "BULLISH": buy_score += 1
        if zone_favors == "LONG": buy_score += 1
        if "BULLISH" in sweep: buy_score += 2 # Peso alto p/ Sweep
        if "BULLISH" in div: buy_score += 1
        
        if buy_score >= 3:
            sig = "STRONG BUY 🟢"
            # O Stop tem que ficar atrás do Sweep
            sl_base = curr['low'] - (curr['ATR']*1) 
            if "BULLISH" in sweep: # Aumenta precisão do SL
                # Busca a minima dos ultimos 5 candles para proteger
                sl_base = m15['low'].tail(5).min() - (curr['ATR']*0.2)
            
            entry = fvg['p'] if (fvg and fvg['type']=='BULLISH') else curr['close']
            type_txt = "Limit FVG" if fvg else "Market (Discount)"
            sl = sl_base
            tp1 = entry + (abs(entry-sl)*2)
            tp2 = entry + (abs(entry-sl)*5)

    # Se CRASH -> Procura Drop
    elif "CRASH" in name:
        sell_score = 0
        if bias_h4 == "BEARISH": sell_score += 1
        if zone_favors == "SHORT": sell_score += 1
        if "BEARISH" in sweep: sell_score += 2
        if "BEARISH" in div: sell_score += 1
        
        if sell_score >= 3:
            sig = "STRONG SELL 🔴"
            sl_base = curr['high'] + (curr['ATR']*1)
            if "BEARISH" in sweep:
                sl_base = m15['high'].tail(5).max() + (curr['ATR']*0.2)
                
            entry = fvg['p'] if (fvg and fvg['type']=='BEARISH') else curr['close']
            type_txt = "Limit FVG" if fvg else "Market (Premium)"
            sl = sl_base
            tp1 = entry - (abs(entry-sl)*2)
            tp2 = entry - (abs(entry-sl)*5)

    # Outros indices
    else:
        # Volatility: Reversão em Sweep ou Tendência em FVG
        if zone_favors == "LONG" and ("BULLISH" in sweep or "BULLISH" in div):
            sig = "BUY REVERSAL"
            entry = curr['close']; sl = m15['low'].tail(10).min()
            type_txt = "Sniper Sweep"
            tp1 = entry + abs(entry-sl)*1.5; tp2 = entry + abs(entry-sl)*3
        elif zone_favors == "SHORT" and ("BEARISH" in sweep or "BEARISH" in div):
            sig = "SELL REVERSAL"
            entry = curr['close']; sl = m15['high'].tail(10).max()
            type_txt = "Sniper Sweep"
            tp1 = entry - abs(entry-sl)*1.5; tp2 = entry - abs(entry-sl)*3
            
    return {
        "ASSET_NAME": name, "MACRO_TREND": bias_h4,
        "SWEEP_DETECTED": sweep, "FIB_ZONE": zone, "FIB_FAVORS": zone_favors,
        "FINAL_DECISION": sig, "ENTRY_TYPE": type_txt,
        "MATH_ENTRY": round(entry,2), "MATH_SL": round(sl,2),
        "MATH_TP1": round(tp1,2), "MATH_TP2": round(tp2,2),
        "WIN_RATE": bt['WR'], "NET_PROFIT": bt['P']
    }

# ==============================================================================
# 7. UI FRONTEND
# ==============================================================================

st.sidebar.title("🗝️ ACCESS KEY")
if "GEMINI_API_KEY" in st.secrets: api = st.secrets["GEMINI_API_KEY"]; st.sidebar.success("Linked")
else: api = st.sidebar.text_input("Enter Key", type="password")

st.sidebar.divider()
st.sidebar.info("V10 ENGINE FEATURES:\n- Liquidity Sweep Hunting\n- Fibonacci Pricing Model\n- Smart SL Protection")

st.title("♟️ SI-APATECO 'BLACK BOX' (V10)")
st.caption("Architecture: SMC Institutional Logic (Sweep + Pricing) + Gemini 3 Pro Vision")

with st.spinner("Inicializando Rede Neural..."):
    assets = get_assets()

if not assets:
    st.error("🔴 REDE DERIV DESCONECTADA. Verifique sua conexão.")
    if st.button("RECONECTAR"): st.rerun()
    st.stop()

col_main, col_data = st.columns([1, 2])

with col_main:
    st.subheader("📡 INPUT STREAM")
    target = st.selectbox("ATIVO", list(assets.keys()))
    st.divider()
    st.caption("UPLOAD CHART TRIAD (M15, H1, H4)")
    u1 = st.file_uploader("M15 (Trigger)", type=['png','jpg'], key='1')
    u2 = st.file_uploader("H1 (Context)", type=['png','jpg'], key='2')
    u3 = st.file_uploader("H4 (Trend)", type=['png','jpg'], key='3')
    
    st.write("")
    run = st.button("EXECUTE ALGORITHM", use_container_width=True)

with col_data:
    if run:
        if not api: st.error("⚠️ KEY REQUIRED"); st.stop()
        imgs = [Image.open(x) for x in [u1,u2,u3] if x]
        if not imgs: st.warning("⚠️ IMAGE REQUIRED (Min: M15)"); st.stop()
        
        status = st.status("⚙️ PROCESSING BLACK BOX DATA...", expanded=True)
        
        status.write(f"1. Fetching Institutional Data for {target}...")
        m15, h4, err = asyncio.run(fetch_data_safe(assets[target]))
        if err: status.update(state="error", label="API ERROR"); st.error(err); st.stop()
        
        status.write("2. Calculating Liquidity Sweeps & Equilibrium Zones...")
        res = black_box_logic(target, m15, h4)
        
        status.write("3. Gemini 3 Pro: Synthesizing Alpha...")
        genai.configure(api_key=api)
        try:
            model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
            payload = [SYSTEM_PROMPT, f"MATH_DATA: {json.dumps(res)}"] + imgs
            resp = model.generate_content(payload)
            txt = resp.text
            status.update(label="EXECUTION READY", state="complete")
        except:
             try: # Fallback silencioso
                 fbm = genai.GenerativeModel("gemini-1.5-pro")
                 payload = [SYSTEM_PROMPT, f"MATH_DATA: {json.dumps(res)}"] + imgs
                 txt = fbm.generate_content(payload).text
                 status.update(label="READY (Fallback)", state="complete")
             except Exception as e: st.error(f"AI ERROR: {e}"); st.stop()

        # DASHBOARD
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Win Rate", f"{res['WIN_RATE']}%")
        k2.metric("Profit Factor", f"{res['NET_PROFIT']}R")
        k3.metric("Bias", res['MACRO_TREND'])
        k4.metric("Sweep", "YES" if "SWEEP" in res['SWEEP_DETECTED'] else "NO")
        
        st.info(f"💎 ZONA DE PREÇO: **{res['FIB_ZONE']}** | DETECÇÃO DE VARREDURA: **{res['SWEEP_DETECTED']}**")
        st.dataframe([res], use_container_width=True)
        
        st.divider()
        st.subheader("🧠 VEREDITO ESTRATÉGICO")
        st.markdown(txt)
