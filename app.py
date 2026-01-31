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
# 1. CONFIGURAÇÃO (SNIPER MODE)
# ==============================================================================
st.set_page_config(
    page_title="SI-APATECO V13 SNIPER",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Teko:wght@300;600&family=Share+Tech+Mono&display=swap');
    
    .stApp {
        background-color: #0c0c0c;
        background-image: linear-gradient(0deg, #000 0%, #111 100%);
        color: #d4d4d4;
        font-family: 'Share Tech Mono', monospace;
    }
    
    h1, h2, h3 {
        font-family: 'Teko', sans-serif !important;
        text-transform: uppercase;
        color: #eab308;
        letter-spacing: 2px;
    }
    
    div[data-testid="stMetric"] {
        background-color: #1a1a1a;
        border-right: 4px solid #eab308;
        padding: 15px;
    }
    
    .stButton>button {
        background: #eab308; /* GOLDEN */
        color: black;
        font-weight: 900;
        text-transform: uppercase;
        padding: 15px;
        border-radius: 2px;
        width: 100%;
        transition: 0.4s;
    }
    .stButton>button:hover {
        background: #facc15;
        box-shadow: 0 0 25px rgba(234, 179, 8, 0.4);
    }
    
    /* Risk Reward Highlights */
    .win-tag { color: #4ade80; font-weight: bold; }
    .loss-tag { color: #f87171; font-weight: bold; }
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
# 2. PROMPT SWING (ALTA AMPLITUDE)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE: SWING TRADING SPECIALIST (1:3+ R:R)
You analyze synthetic indices for EXPANSION MOVES.
Ignore scalps. Ignore noise. Focus on H4 Trend Continuation from Deep Pullbacks.

INPUTS:
1. **Trend Context (H4/H1):** Determines direction.
2. **Deep Pullback (Valuation):** Entry logic.
3. **Execution Data:** Provided in JSON.

**RULES:**
- TARGET: Minimum 1:3 Reward. If price structure doesn't allow a tight SL, warn about position size.
- LOGIC: Buy LOW in an Uptrend (Discount). Sell HIGH in a Downtrend (Premium).
- MARKET TYPE: 
  - Boom/Crash = Swing logic applies (Wait for Trend Resume).
  - Volatility = Breakout/Retest logic.

OUTPUT FORMAT (Markdown):

## 🔭 SWING SETUP: [ {FINAL_DECISION} ]
**Asset:** {ASSET_NAME} | **Potential Payoff:** 1:{RR_RATIO}

### 📐 STRUCTURAL MAP
*   **Major Trend (H4):** {BIAS_H4}
*   **Current Action:** {MARKET_STATE} (Trend or Correction?)
*   **Volume Status:** {ADX_STATUS}

### 🎯 EXECUTION (HIGH PAYOFF)
| Order | Level | Distance |
| :--- | :--- | :--- |
| **ENTRY** | **{MATH_ENTRY}** | *{ENTRY_TYPE}* |
| **STOP** | **{MATH_SL}** | *{SL_DIST} pts* |
| **TP 1 (Base)** | **{MATH_TP3}** | *1:3 RR* |
| **TP 2 (Moon)** | **{MATH_TP5}** | *1:5 RR* |

*Rationale:* {Why this swing trade offers high probability at this price level.}
)
"""

# ==============================================================================
# 3. REDE DERIV
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
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 200, "end": "latest"},  # H1 (Primário)
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 200, "end": "latest"}, # H4 (Macro)
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 500, "end": "latest"}    # M15 (Refino)
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
    return None, None, None, "API CONNECTION FAIL."

# ==============================================================================
# 4. SWING MATH KERNEL (V13)
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def indicators(df):
    # Tendencia
    df['EMA_20'] = df['close'].ewm(span=20).mean() # Média Rápida
    df['EMA_50'] = df['close'].ewm(span=50).mean() # "Zona de Valor" (Suporte Dinâmico)
    df['EMA_200'] = df['close'].ewm(span=200).mean() # Viés Maior
    
    # Oscilador para "Dip"
    delta = df['close'].diff()
    rs = (delta.where(delta>0,0).rolling(14).mean()) / (-delta.where(delta<0,0).rolling(14).mean() + 1e-9)
    df['RSI'] = 100 - (100/(1+rs))
    
    # Volatilidade p/ Stop
    df['tr'] = df[['high','low','close']].apply(lambda x: max(x['high']-x['low'], abs(x['high']-x['close']), abs(x['low']-x['close'])), axis=1)
    df['ATR'] = df['tr'].rolling(14).mean()
    
    # Força da Tendencia (ADX Simples)
    df['ADX'] = abs(df['close'] - df['close'].shift(14)) / df['ATR'] * 100
    
    df.dropna(inplace=True)
    return df

def detect_swing_level(df, direction):
    """
    Encontra um Stop Loss "Técnico" no fundo anterior (Buy) ou topo anterior (Sell).
    Fundamental para trades 1:5.
    """
    if direction == "BUY":
        # Pega a mínima das ultimas 10 velas H1 que seja menor que a atual
        recent_lows = df['low'].tail(15)
        # O Stop ideal é no fundo da estrutura ("Pivot")
        sl_level = recent_lows.min() 
        return sl_level
        
    elif direction == "SELL":
        recent_highs = df['high'].tail(15)
        sl_level = recent_highs.max()
        return sl_level
    
    return df.iloc[-1]['close']

# ==============================================================================
# 5. PROFITABILITY BACKTEST (FOCADO EM PAYOFF)
# ==============================================================================

def run_payoff_sim(df, trend_dir):
    """
    Calcula: Quantas vezes conseguimos bater 1:3 vs Quantas vezes fomos estopados?
    Foca no R:R (Risco/Retorno)
    """
    trades = 0; wins_1_3 = 0; wins_1_5 = 0; losses = 0
    balance_r = 0 # Acumulador de 'R'
    
    for i in range(100, len(df)-80):
        row = df.iloc[i]
        sig = False
        
        # Simula a entrada de Swing: A favor da Média Longa + Correção na Curta
        is_bull = row['close'] > row['EMA_200']
        pullback_buy = row['low'] <= row['EMA_20'] # Preço tocou na média rapida
        
        is_bear = row['close'] < row['EMA_200']
        pullback_sell = row['high'] >= row['EMA_20']
        
        if trend_dir == "BULLISH" and is_bull and pullback_buy: sig = "BUY"
        elif trend_dir == "BEARISH" and is_bear and pullback_sell: sig = "SELL"
        
        if sig:
            entry = row['close']; atr = row['ATR']
            
            # Setup SNIPER
            sl = entry - (1.5 * atr) if sig=="BUY" else entry + (1.5 * atr)
            risk = abs(entry - sl)
            
            target_3 = entry + (3*risk) if sig=="BUY" else entry - (3*risk)
            target_5 = entry + (5*risk) if sig=="BUY" else entry - (5*risk)
            
            outcome = "OPEN"
            for f in range(i+1, min(i+80, len(df))): # Deixa rolar (Swing)
                nx = df.iloc[f]
                if sig=="BUY":
                    if nx['low'] <= sl: outcome="LOSS"; break
                    if nx['high'] >= target_5: outcome="WIN_5"; break
                    if nx['high'] >= target_3 and outcome != "WIN_5": outcome="WIN_3" # Partial check
                else:
                    if nx['high'] >= sl: outcome="LOSS"; break
                    if nx['low'] <= target_5: outcome="WIN_5"; break
                    if nx['low'] <= target_3 and outcome != "WIN_5": outcome="WIN_3"
            
            if outcome != "OPEN":
                trades += 1
                if "WIN" in outcome:
                    if outcome == "WIN_5": balance += 5.0; wins_1_5 += 1
                    else: balance += 3.0; wins_1_3 += 1
                else:
                    balance -= 1.0; losses += 1
                i = f + 5 # Pula algumas velas apos trade
    
    total_wins = wins_1_3 + wins_1_5
    wr = (total_wins / trades * 100) if trades > 0 else 0
    return {"WR": round(wr,1), "PAYOFF": round(balance,1), "HITS_1_5": wins_1_5}

# ==============================================================================
# 6. KERNEL (LÓGICA V13)
# ==============================================================================

def sniper_core(name, h1_raw, h4_raw, m15_raw):
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    # Usamos H1 como mestre para o Backtest Swing
    
    curr = h1.iloc[-1]
    
    # 1. H4 Trend (The River)
    trend_h4 = "BULLISH" if h4.iloc[-1]['close'] > h4.iloc[-1]['EMA_200'] else "BEARISH"
    adx_h4 = h4.iloc[-1]['ADX']
    adx_stat = "TRENDING 🚀" if adx_h4 > 25 else "WEAK/RANGE 💤"
    
    # 2. H1 Swing (The Wave)
    # Detectamos se o preço está "Barato" (Discount) ou "Caro" (Premium) relativo à tendência
    on_value_zone = False
    
    sig = "MONITORING"
    entry = curr['close']
    sl = curr['close']
    
    if trend_h4 == "BULLISH":
        # Se preço recuou perto da EMA50 ou RSI H1 esfriou
        dist_to_mean = abs(curr['close'] - curr['EMA_50'])
        is_close_mean = dist_to_mean < (curr['ATR']*1.0)
        
        if is_close_mean or curr['RSI'] < 50:
            sig = "LONG (SWING)"
            sl = detect_swing_level(h1, "BUY")
            # Proteção: SL nunca deve ser maior que 3x ATR (gestão)
            if (entry - sl) > (3*curr['ATR']): sl = entry - (2*curr['ATR'])
            
    elif trend_h4 == "BEARISH":
        dist_to_mean = abs(curr['close'] - curr['EMA_50'])
        is_close_mean = dist_to_mean < (curr['ATR']*1.0)
        
        if is_close_mean or curr['RSI'] > 50:
            sig = "SHORT (SWING)"
            sl = detect_swing_level(h1, "SELL")
            if (sl - entry) > (3*curr['ATR']): sl = entry + (2*curr['ATR'])

    # 3. BACKTEST REALITY CHECK (Validando a direção)
    # Se o sinal é BUY, rodamos simulação de COMPRA neste ativo. Se for negativo, alertamos.
    sim = run_payoff_sim(h1, trend_h4)
    
    if sim['PAYOFF'] <= 0:
        sig = "BLOCKED (NEGATIVE PAYOFF)" # Estatística não compensa
    
    # Targets 1:3 e 1:5
    risk = abs(entry - sl)
    if risk == 0: risk = curr['ATR']
    
    if "LONG" in sig or "BUY" in sig:
        tp3 = entry + (risk * 3.0)
        tp5 = entry + (risk * 5.0)
        direction = "BUY"
    else:
        tp3 = entry - (risk * 3.0)
        tp5 = entry - (risk * 5.0)
        direction = "SELL"

    return {
        "ASSET_NAME": name, "BIAS_H4": trend_h4, "ADX_STATUS": adx_stat,
        "MARKET_STATE": "Correction/Value Zone" if "SWING" in sig else "Expansion",
        "FINAL_DECISION": sig, "ENTRY_TYPE": "Pullback/Trend Rejoin",
        "WIN_RATE": sim['WR'], "NET_PROFIT": sim['PAYOFF'], "HITS_1_5": sim['HITS_1_5'],
        "MATH_ENTRY": round(entry,2), "MATH_SL": round(sl,2), "SL_DIST": round(risk,2),
        "MATH_TP3": round(tp3,2), "MATH_TP5": round(tp5,2),
        "RR_RATIO": "5.0"
    }

# ==============================================================================
# 7. INTERFACE V13
# ==============================================================================

st.sidebar.title("🔐 ACCESS KEY")
if "GEMINI_API_KEY" in st.secrets: api = st.secrets["GEMINI_API_KEY"]; st.sidebar.success("SECURE")
else: api = st.sidebar.text_input("Enter Key", type="password")

st.sidebar.divider()
st.sidebar.info("""
**V13 SNIPER SPECS:**
- 🎯 **Target:** 1:3 & 1:5 R:R
- ⏳ **Frequency:** Medium/Low
- 📊 **Precision:** High Probability Swing
- 🚫 **Scalp:** Disabled
""")

st.title("🔭 SI-APATECO SNIPER SWING (V13)")
st.caption("Strategic Trend Following. High Reward Targeting. Bi-Directional Logic.")

with st.spinner("Aligning Satellites..."):
    assets = get_assets()

if not assets: st.error("Link Failure."); st.stop()

c1, c2 = st.columns([1, 2])

with c1:
    target = st.selectbox("MISSION TARGET", list(assets.keys()))
    st.markdown("---")
    st.caption("VISUAL CONFIRMATION (OPTIONAL)")
    u1 = st.file_uploader("Upload H4/H1 Chart", type=['png','jpg'])
    run = st.button("CALCULATE VECTOR", use_container_width=True)

with c2:
    if run:
        if not api: st.error("⚠️ KEY REQUIRED"); st.stop()
        
        status = st.status("🛸 CALCULATING TRAJECTORY...", expanded=True)
        
        status.write("1. Pulling Macro & Micro Structure...")
        # A ordem aqui muda: H1, H4, M15 (M15 é só p/ refino, nao crítico)
        h1, h4, m15, err = asyncio.run(fetch_tri_force(assets[target]))
        if err: status.update(state='error', label="FAIL"); st.error(err); st.stop()
        
        status.write("2. Running Risk/Reward Simulation (1000 candles)...")
        data = sniper_core(target, h1, h4, m15)
        
        status.write("3. Generating Briefing...")
        genai.configure(api_key=api)
        try:
            model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
            i_list = [Image.open(u1)] if u1 else []
            txt = model.generate_content([SYSTEM_PROMPT, f"MATH: {json.dumps(data)}"] + i_list).text
            status.update(label="TRAJECTORY LOCKED", state="complete")
        except:
             txt = "⚠️ AI Unavailable. Data Only."
             status.update(label="DATA ONLY", state="complete")

        # DASHBOARD
        # Mostra o Payoff
        if data['NET_PROFIT'] > 10: st.balloons()
        
        st.subheader("💰 POTENCIAL FINANCEIRO (ÚLTIMO CICLO)")
        m1, m2, m3 = st.columns(3)
        m1.metric("Payoff Total", f"{data['NET_PROFIT']}R")
        m2.metric("Acertos 1:5", f"{data['HITS_1_5']} Trades")
        m3.metric("Probabilidade", f"{data['WIN_RATE']}%")
        
        # Decisão
        res_col = "green" if "SWING" in data['FINAL_DECISION'] else "red"
        st.markdown(f"### ORDER: :{res_col}[{data['FINAL_DECISION']}]")
        
        if "BLOCKED" in data['FINAL_DECISION']:
            st.error("🛑 TRADE BLOQUEADO: Risco Matemático muito alto. O ativo está lateral ou Payoff é negativo.")
        else:
            if "SWING" in data['FINAL_DECISION']:
                st.success(f"🎯 **ALVO 1:3 CONFIRMADO.** SL protegido por estrutura H1.")
        
        st.dataframe([data], use_container_width=True)
        st.divider()
        st.markdown(txt)
