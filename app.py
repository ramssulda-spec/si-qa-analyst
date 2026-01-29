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
# 1. CONFIGURAÇÕES VISUAIS (SYNTHETIC ORACLE V9.0)
# ==============================================================================
st.set_page_config(
    page_title="SI-APATECO ORACLE V9",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Orbitron:wght@900&display=swap');
    
    .stApp {
        background-color: #020202;
        background-image: linear-gradient(180deg, #0a0f1c 0%, #000000 100%);
        color: #d1d5db;
        font-family: 'Space Mono', monospace;
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        background: linear-gradient(to right, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }
    
    /* Metrics Custom */
    div[data-testid="stMetric"] {
        background-color: #0f1115;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif;
        color: #e5e7eb !important;
    }
    
    .stFileUploader { background: #080808; border: 1px dashed #374151; }

    /* Button Gradient */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%);
        color: white;
        font-family: 'Orbitron';
        font-weight: 800;
        border: none;
        padding: 16px 32px;
        text-transform: uppercase;
        border-radius: 6px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(147, 51, 234, 0.4);
    }
    
    .dataframe { font-family: 'Space Mono', monospace !important; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# --- CONFIG SEGURANÇA ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# 2. PROMPT SPECALISTA EM SINTÉTICOS (V9)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE: SI-APATECO ORACLE V9 [Model: Gemini 3 Pro]
You are a Specialist in DERIV SYNTHETIC INDICES.
You ignore fundamental news. You focus ONLY on Algorithmic Price Action.

INPUTS:
1. **MATH JSON (THE LAW):** 
   - Trends, RSI Divergences (Critical), FVGs, Backtest Stats.
2. **VISUAL TRI-FORCE:** M15 (Entry), H1 (Structure), H4 (Trend).

**SYNTHETIC MARKET RULES:**
1. **BOOM/CRASH:**
   - Look for "SPIKE" setups based on Divergence or FVG Support/Resistance.
   - Ignore standard candlestick patterns; look for rejection wicks at math levels.
2. **VOLATILITY/STEP:**
   - Respect RSI Divergence strictly.
   - Trend is Valid only if H4 and M15 align.

**OUTPUT PROTOCOL:**

## 🔮 ORACLE V9 VERDICT: [ {FINAL_DECISION} ]
**Asset:** {ASSET_NAME} | **Probability:** {WIN_RATE}%

### 🌀 ALGORITHMIC CONFLUENCE
*   **Trend Matrix:** H4 is {MACRO_TREND}. Structure is {STRUCTURE_BIAS}.
*   **RSI Divergence:** {DIVERGENCE_STATUS} (Significant reversal signal if present).
*   **Trigger:** Price is at **{FVG_DETECTED}**.

### 📉 EXECUTION BLOCK
| Parameter | Price Level | Type |
| :--- | :--- | :--- |
| **Action** | **{FINAL_DECISION}** | *{AGGRESSIVE/CONSERVATIVE}* |
| **Entry** | **{MATH_ENTRY}** | *FVG/Imbalance* |
| **Stop Loss** | **{MATH_SL}** | *Struct Low/High - Volatility Adjusted* |
| **TP 1** | **{MATH_TP1}** | *Scalp (1:1.5)* |
| **TP 2** | **{MATH_TP2}** | *Swing (1:3.0)* |

*Synthesis:* {Briefly explain why the Math (Divergence/Structure) confirms the visual setup}.
)
"""

# ==============================================================================
# 3. REDE DERIV ROBUSTA (MÚLTIPLOS SERVIDORES)
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
            # Timeout estendido para evitar falha em redes lentas
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=20.0))
    except: return None

@st.cache_data(ttl=3600)
def get_assets_list():
    req = {"active_symbols": "brief", "product_type": "basic"}
    for url in DERIV_SERVERS:
        data = asyncio.run(connect_socket(url, req))
        if data and 'active_symbols' in data:
            return {x['display_name'].upper(): x['symbol'] for x in data['active_symbols'] if x['market']=='synthetic_index'}
    return None

async def fetch_data_safe(code):
    req_m15 = {"ticks_history": code, "style": "candles", "granularity": 900, "count": 1000, "adjust_start_time": 1, "end": "latest"}
    req_h4 = {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 300, "adjust_start_time": 1, "end": "latest"}
    
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=None) as ws:
                await ws.send(json.dumps(req_m15)); m15 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                await ws.send(json.dumps(req_h4)); h4 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                if 'candles' in m15 and 'candles' in h4: return m15['candles'], h4['candles'], None
        except: continue
    return None, None, "FALHA CRÍTICA DE REDE: Nenhum servidor respondeu."

# ==============================================================================
# 4. QUANTUM MATH CORE V9 (SYNTHETIC SPECIALIZED)
# ==============================================================================

def clean_data(data):
    df = pd.DataFrame(data)
    cols = ['open','high','low','close','epoch']
    for c in cols: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def indicators(df):
    # RSI (Index Strength)
    delta = df['close'].diff()
    gain = (delta.where(delta>0,0)).rolling(14).mean()
    loss = (-delta.where(delta<0,0)).rolling(14).mean()
    rs = gain/(loss+1e-9)
    df['RSI'] = 100 - (100/(1+rs))
    
    # Médias Institucionais
    df['EMA_20'] = df['close'].ewm(span=20).mean() # Média Curta (H1 Proxy no H4)
    df['EMA_50'] = df['close'].ewm(span=50).mean()
    df['EMA_200'] = df['close'].ewm(span=200).mean()
    
    # ATR puro (Sem filtro de notícias, apenas Volatilidade do Algoritmo)
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift())
    df['tr2'] = abs(df['low'] - df['close'].shift())
    df['ATR'] = df[['tr0', 'tr1', 'tr2']].max(axis=1).rolling(14).mean()
    
    df.dropna(inplace=True)
    return df

def detect_rsi_divergence(df, window=15):
    """
    DETECTA DIVERGÊNCIAS RSI x PREÇO
    Fundamental para Volatility e Step Indices.
    - Regular Bearish: Preço faz High, RSI faz Lower High (Reversão para Venda)
    - Regular Bullish: Preço faz Low, RSI faz Higher Low (Reversão para Compra)
    """
    price = df['close']
    rsi = df['RSI']
    
    # Pega os ultimos picos
    recent_idx = range(len(df)-window, len(df))
    
    # Simples lógica de comparação de Slope das ultimas 10 velas
    price_slope = price.iloc[-1] - price.iloc[-10]
    rsi_slope = rsi.iloc[-1] - rsi.iloc[-10]
    
    status = "NONE"
    
    # Divergência de Alta (Preço cai, RSI sobe)
    if price_slope < 0 and rsi_slope > 5:
        status = "BULLISH DIVERGENCE (REVERSAL)"
    
    # Divergência de Baixa (Preço sobe, RSI cai)
    elif price_slope > 0 and rsi_slope < -5:
        status = "BEARISH DIVERGENCE (REVERSAL)"
        
    return status

def get_structure_bias(df_m15):
    """Verifica a estrutura local (BOS)"""
    last_low = df_m15['low'].tail(20).min()
    last_high = df_m15['high'].tail(20).max()
    curr = df_m15.iloc[-1]['close']
    
    if curr > last_high: return "BULLISH BREAK"
    if curr < last_low: return "BEARISH BREAK"
    return "RANGING/CONSOLIDATION"

def detect_fvg(df):
    fvgs = []
    # Olha ultimos 50 candles
    rc = df.tail(50).reset_index(drop=True)
    for i in range(len(rc)-2, 2, -1):
        # Bearish
        if rc.iloc[i-2]['low'] > rc.iloc[i]['high']:
            # Verifica se nao foi mitigado
            gap_zone = (rc.iloc[i-2]['low'] + rc.iloc[i]['high']) / 2
            is_valid = True
            for j in range(i+1, len(rc)):
                if rc.iloc[j]['high'] >= gap_zone: is_valid=False; break
            if is_valid: fvgs.append({'type':'BEARISH', 'price': gap_zone})

        # Bullish
        elif rc.iloc[i-2]['high'] < rc.iloc[i]['low']:
            gap_zone = (rc.iloc[i-2]['high'] + rc.iloc[i]['low']) / 2
            is_valid = True
            for j in range(i+1, len(rc)):
                if rc.iloc[j]['low'] <= gap_zone: is_valid=False; break
            if is_valid: fvgs.append({'type':'BULLISH', 'price': gap_zone})
    
    # Retorna o mais proximo do preço atual
    return fvgs[-1] if fvgs else None

# ==============================================================================
# 5. BACKTEST ENGINE V9 (SYNTHETIC PENALTY SYSTEM)
# ==============================================================================
def backtest_v9(df, asset_name):
    trades=0; wins=0; balance=0
    
    for i in range(150, len(df)-60):
        row = df.iloc[i]
        
        # Filtros de Indicies
        # Em indices sinteticos, "Mean Reversion" no Bollinger funciona muito bem
        # Trend Following funciona em quebra de EMA200
        
        sig = None
        
        trend_up = row['close'] > row['EMA_200']
        trend_down = row['close'] < row['EMA_200']
        
        if "BOOM" in asset_name:
            # Boom só opera Compra
            if trend_up and row['RSI'] < 40: sig='BUY' # Pullback Trend
            
        elif "CRASH" in asset_name:
            # Crash só opera Venda
            if trend_down and row['RSI'] > 60: sig='SELL' # Pullback Trend
            
        else:
            # Volatility: Segue a tendencia ou RSI Divergence (simulado aqui por niveis extremos)
            if trend_up and row['RSI'] < 30: sig='BUY'
            if trend_down and row['RSI'] > 70: sig='SELL'

        if sig:
            ent = row['close']
            atr = row['ATR']
            
            # SL Adaptativo V9 (Sem noticias, apenas Volatilidade Pura)
            # Para Indices, SL fixo de 2.0x ATR costuma ser seguro para evitar stop hunting pequeno
            sl_dist = atr * 2.0
            tp_dist = atr * 4.0 # 1:2 Risk Reward padrão institucional
            
            sl = ent - sl_dist if sig=='BUY' else ent + sl_dist
            tp = ent + tp_dist if sig=='BUY' else ent - tp_dist
            
            outcome = "OPEN"
            for f in range(i+1, min(i+60, len(df))): # Verifica proxima hora
                nx = df.iloc[f]
                if sig=='BUY':
                    if nx['low'] <= sl: outcome='LOSS'; break
                    if nx['high'] >= tp: outcome='WIN'; break
                else:
                    if nx['high'] >= sl: outcome='LOSS'; break
                    if nx['low'] <= tp: outcome='WIN'; break
            
            if outcome != 'OPEN':
                trades+=1
                if outcome=='WIN': wins+=1; balance+=2.0 # Ganhou 2R
                else: balance-=1.0 # Perdeu 1R
                i=f 
                
    wr = (wins/trades*100) if trades>0 else 0
    return {"WR": round(wr,1), "N": trades, "P": round(balance,2)}

# ==============================================================================
# 6. NEURAL ORACLE (PROCESSAMENTO)
# ==============================================================================
def run_oracle_v9(name, m15_raw, h4_raw):
    m15 = indicators(clean_data(m15_raw))
    h4 = indicators(clean_data(h4_raw))
    bt = backtest_v9(m15, name)
    
    curr = m15.iloc[-1]
    
    # 1. H4 Bias (Macro)
    h4_bias = "BULLISH" if h4.iloc[-1]['close'] > h4.iloc[-1]['EMA_50'] else "BEARISH"
    
    # 2. Local Structure
    struct_bias = get_structure_bias(m15)
    div_status = detect_rsi_divergence(m15)
    fvg = detect_fvg(m15)
    
    sig="HOLD"; entry=curr['close']; sl=curr['close']; tp1=curr['close']; tp2=curr['close']
    fvg_msg = "No Clean FVG"

    # LOGICA DE CONFLUENCIA FINAL
    
    # Lógica Boom/Crash
    if "BOOM" in name or "CRASH" in name:
        if "BOOM" in name:
            # Só compra se: H4 for Alta, ou H4 for Baixa mas tiver Divergência Bullish clara
            valid_buy = (h4_bias == "BULLISH") or ("BULLISH" in div_status)
            if valid_buy and curr['RSI'] < 50:
                sig = "BUY (SPIKE)"
                entry = fvg['price'] if (fvg and fvg['type']=='BULLISH') else curr['close']
                sl = entry - (curr['ATR']*1.5) # ATR Padding
                if fvg: fvg_msg = f"FVG Support @ {entry:.2f}"
                
        if "CRASH" in name:
            valid_sell = (h4_bias == "BEARISH") or ("BEARISH" in div_status)
            if valid_sell and curr['RSI'] > 50:
                sig = "SELL (DROP)"
                entry = fvg['price'] if (fvg and fvg['type']=='BEARISH') else curr['close']
                sl = entry + (curr['ATR']*1.5)
                if fvg: fvg_msg = f"FVG Resist @ {entry:.2f}"
                
    # Lógica Volatility
    else:
        # Tendência Pura + FVG
        if h4_bias == "BULLISH" and struct_bias != "BEARISH BREAK":
            if fvg and fvg['type'] == 'BULLISH':
                sig = "BUY (TREND)"
                entry = fvg['price']; fvg_msg = f"Order Block @ {entry:.2f}"
                sl = entry - (curr['ATR']*2.0)
            elif "BULLISH" in div_status:
                sig = "BUY (REVERSAL)"
                sl = curr['low'] - curr['ATR']

        elif h4_bias == "BEARISH" and struct_bias != "BULLISH BREAK":
            if fvg and fvg['type'] == 'BEARISH':
                sig = "SELL (TREND)"
                entry = fvg['price']; fvg_msg = f"Order Block @ {entry:.2f}"
                sl = entry + (curr['ATR']*2.0)
            elif "BEARISH" in div_status:
                sig = "SELL (REVERSAL)"
                sl = curr['high'] + curr['ATR']

    # Targets (RR 1.5 e 3.0)
    risk = abs(entry - sl)
    if risk < (curr['ATR']*0.1): risk = curr['ATR'] # Evitar SL Zero
    
    if "BUY" in sig: tp1=entry+(risk*1.5); tp2=entry+(risk*3.0)
    elif "SELL" in sig: tp1=entry-(risk*1.5); tp2=entry-(risk*3.0)

    return {
        "ASSET_NAME": name, "MACRO_TREND": h4_bias,
        "STRUCTURE_BIAS": struct_bias, "DIVERGENCE_STATUS": div_status,
        "FVG_DETECTED": fvg_msg, "FINAL_DECISION": sig,
        "MATH_ENTRY": round(entry, 2), "MATH_SL": round(sl, 2),
        "MATH_TP1": round(tp1, 2), "MATH_TP2": round(tp2, 2),
        "WIN_RATE": bt['WR'], "NET_PROFIT": bt['P']
    }

# ==============================================================================
# 7. FRONTEND V9
# ==============================================================================

st.sidebar.title("🔐 CHAVE ORACLE")
if "GEMINI_API_KEY" in st.secrets: api = st.secrets["GEMINI_API_KEY"]; st.sidebar.success("✅ Segura (Secrets)")
else: api = st.sidebar.text_input("Cole API Gemini", type="password")

st.sidebar.divider()
st.sidebar.info("""
**ORACLE ENGINE V9.0**
- 🛡️ **No Fundamentals:** Pure Tech.
- 📐 **RSI Divergence:** Auto-Detect.
- 🧱 **Structure Lock:** H4+M15 Sync.
""")

st.title("🔮 SI-APATECO ORACLE (V9)")
st.caption("Focus: Synthetic Indices Pure Algorithmic Patterns (No News Noise)")

with st.spinner("Sincronizando com RNG da Deriv..."):
    assets = get_assets_list()

if not assets:
    st.error("❌ ERRO: Servidores Deriv inacessíveis. Sua rede pode estar bloqueando WebSockets.")
    if st.button("♻️ Tentar Novamente"): st.rerun()
    st.stop()

# Main UI
c_in, c_res = st.columns([1, 2])

with c_in:
    target = st.selectbox("Selecione o Índice", list(assets.keys()))
    st.markdown("---")
    st.write("📸 **SMC Tri-Force Prints:**")
    u1 = st.file_uploader("1. M15 (Entry)", type=['png','jpg'], key='1')
    u2 = st.file_uploader("2. H1 (Struct)", type=['png','jpg'], key='2')
    u3 = st.file_uploader("3. H4 (Trend)", type=['png','jpg'], key='3')
    st.markdown("---")
    run = st.button("👁️ CONSULTAR ORÁCULO", use_container_width=True)

with c_res:
    if run:
        if not api: st.error("⚠️ API Key ausente."); st.stop()
        imgs = [Image.open(x) for x in [u1,u2,u3] if x]
        if not imgs: st.warning("⚠️ Mínimo 1 print (M15) necessário."); st.stop()

        box = st.status("🔮 ORÁCULO CALCULANDO...", expanded=True)
        
        box.write(f"📡 API: Extraindo dados algorítmicos de {target}...")
        m15, h4, err = asyncio.run(fetch_data_safe(assets[target]))
        if err: box.update(state='error', label='Erro'); st.error(err); st.stop()
        
        box.write("🧮 MATH: Detectando Divergências RSI & Order Blocks...")
        data = run_oracle_v9(target, m15, h4)
        
        box.write("🧠 AI: Sintetizando Padrões (Gemini 3 Pro)...")
        genai.configure(api_key=api)
        try:
            model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
            resp = model.generate_content([SYSTEM_PROMPT, f"MATH_JSON: {json.dumps(data)}"] + imgs)
            ai_out = resp.text
            box.update(label="PREVISÃO CONCLUÍDA", state="complete")
        except Exception as e:
             st.warning(f"Erro AI Principal: {e}. Tentando fallback...")
             try:
                 fallback = genai.GenerativeModel("gemini-1.5-pro", safety_settings=SAFETY_SETTINGS)
                 resp = fallback.generate_content([SYSTEM_PROMPT, f"MATH_JSON: {json.dumps(data)}"] + imgs)
                 ai_out = resp.text
                 box.update(label="PREVISÃO (FALLBACK)", state="complete")
             except: st.error("Erro Fatal IA"); st.stop()
             
        # DASHBOARD
        st.subheader(f"📊 PROBABILIDADE: {data['WIN_RATE']}%")
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Bias H4", data['MACRO_TREND'])
        k2.metric("RSI Div", "DETECTADA" if "DIVERGENCE" in data['DIVERGENCE_STATUS'] else "---")
        k3.metric("Trigger", data['FVG_DETECTED'].split('@')[0])
        k4.metric("Exp. Profit", f"{data['NET_PROFIT']}R")
        
        st.success(f"DECISÃO TÉCNICA: **{data['FINAL_DECISION']}**")
        st.dataframe([data], use_container_width=True)
        st.divider()
        st.markdown(ai_out)
