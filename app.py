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
# 1. CONFIGURAÇÕES VISUAIS (QUANTUM V7.0)
# ==============================================================================
st.set_page_config(
    page_title="SI-APATECO QUANTUM V7",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@900&display=swap');
    
    .stApp {
        background-color: #000000;
        background-image: radial-gradient(circle at center, #1a1a1a 0%, #000000 100%);
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        background: linear-gradient(90deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }
    
    /* Upload Areas */
    .stFileUploader {
        border: 1px dashed #444;
        padding: 10px;
        border-radius: 8px;
        background: #111;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: rgba(20, 20, 20, 0.9);
        border: 1px solid #444;
        border-radius: 8px;
        padding: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #00ff41 !important;
        font-family: 'Orbitron', sans-serif;
    }

    /* Action Button */
    .stButton>button {
        background: linear-gradient(90deg, #00ff41, #008f24);
        color: black;
        font-family: 'Orbitron';
        font-weight: 900;
        border: none;
        border-radius: 4px;
        text-transform: uppercase;
        padding: 16px 32px;
        font-size: 18px;
        transition: 0.3s;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 25px rgba(0, 255, 65, 0.6);
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIG DE SEGURANÇA (GEMINI) ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# 2. PROMPT MESTRE (GEMINI 3 PRO PREVIEW SPECIFIC)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE: QUANTUM SMC TRADING ENGINE [Model: Gemini 3 Pro]
You are an advanced Trading Algorithm designed for Deriv Synthetic Indices.
You analyze up to 3 Charts (M15, H1, H4) AND Math Data provided via JSON.

**RULES OF ENGAGEMENT:**
1. **TRUST THE MATH:** The JSON data contains the TRUE Price Action status (RSI, Trend Bias, Backtest stats). Use these numbers as the source of truth.
2. **TRI-FORCE VISUAL:** 
   - H4 Chart = Check Macro Direction (Supply/Demand).
   - H1 Chart = Check Internal Structure (BOS/Chr).
   - M15 Chart = Check Entry Triggers (Candle Patterns).
3. **NO HALLUCINATION:** Do not invent prices. Use the 'MATH_ENTRY', 'MATH_SL', 'MATH_TP' from the provided data packet.

**OUTPUT FORMAT:**

## 💠 QUANTUM V7 DECISION: [ {FINAL_DECISION} ]
**Asset:** {ASSET_NAME} | **Algo-Prob:** {WIN_RATE}% (Backtested)

### 📊 TRI-FORCE ANALYSIS
*   **H4 Bias:** {Describe H4 Trend visually}
*   **H1 Structure:** {Describe recent break of structure}
*   **M15 Trigger:** {Describe candlestick formation at the math entry zone}

### 📉 EXECUTION GRID (GEMINI 3 PRECISION)
| Parameter | Level | Note |
| :--- | :--- | :--- |
| **Action** | **{FINAL_DECISION}** | *{AGGRESSIVE/CONSERVATIVE}* |
| **Entry** | **{MATH_ENTRY}** | *Smart Money Zone* |
| **Stop** | **{MATH_SL}** | *Structural Protection* |
| **TP 1** | **{MATH_TP1}** | *1:2.0 Risk* |
| **TP 2** | **{MATH_TP2}** | *Liquidity Target* |

*Analyst Note:* {Provide a pro-tip for this trade setup based on volatility}
)
"""

# ==============================================================================
# 3. REDE DERIV (ROBUST FAILOVER SERVERS)
# ==============================================================================
DERIV_SERVERS = [
    "wss://ws.binaryws.com/websockets/v3?app_id=1089",      
    "wss://ws.derivws.com/websockets/v3?app_id=1089",       
    "wss://green.binaryws.com/websockets/v3?app_id=1089",
    "wss://blue.binaryws.com/websockets/v3?app_id=1089"
]

async def deriv_connect_attempt(url, message):
    try:
        # Timeout 15s para garantir resposta
        async with websockets.connect(url, ping_interval=None, close_timeout=10) as ws:
            await ws.send(json.dumps(message))
            response = await asyncio.wait_for(ws.recv(), timeout=15.0)
            return json.loads(response)
    except: return None

@st.cache_data(ttl=3600)
def get_deriv_assets():
    req = {"active_symbols": "brief", "product_type": "basic"}
    for url in DERIV_SERVERS:
        data = asyncio.run(deriv_connect_attempt(url, req))
        if data and 'active_symbols' in data:
            ativos = {}
            for x in data['active_symbols']:
                if x['market'] == 'synthetic_index': ativos[x['display_name'].upper()] = x['symbol']
            if ativos: return ativos
    return None 

async def fetch_candles_safe(code):
    # Solicita 1000 velas M15 e 200 H4
    req_m15 = {"ticks_history": code, "style": "candles", "granularity": 900, "count": 1000, "adjust_start_time": 1, "end": "latest"}
    req_h4 = {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 200, "adjust_start_time": 1, "end": "latest"}
    
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=None) as ws:
                await ws.send(json.dumps(req_m15))
                res_m15 = await asyncio.wait_for(ws.recv(), timeout=15.0)
                m15_data = json.loads(res_m15)
                
                await ws.send(json.dumps(req_h4))
                res_h4 = await asyncio.wait_for(ws.recv(), timeout=15.0)
                h4_data = json.loads(res_h4)
                
                if 'candles' in m15_data and 'candles' in h4_data:
                    return m15_data['candles'], h4_data['candles'], None
        except Exception: continue
    return None, None, "Erro Fatal: Não foi possível conectar a nenhum servidor Deriv."

# ==============================================================================
# 4. MATH CORE (V7 FIXED PANDAS)
# ==============================================================================

def prepare_df(data):
    df = pd.DataFrame(data)
    cols = ['open','high','low','close','epoch']
    for c in cols: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def indicators(df):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100/(1+rs))
    
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift())
    df['tr2'] = abs(df['low'] - df['close'].shift())
    df['ATR'] = df[['tr0', 'tr1', 'tr2']].max(axis=1).rolling(14).mean()
    
    df.dropna(inplace=True)
    return df

def find_swings(df, window=5):
    """
    Função Corrigida para Pandas 2.0+ (ValueError Fix)
    """
    roll_min = df['low'].rolling(window=2*window+1, center=True).min()
    roll_max = df['high'].rolling(window=2*window+1, center=True).max()
    
    # Compara a série completa alinhada
    df['is_low'] = df['low'] == roll_min
    df['is_high'] = df['high'] == roll_max
    
    last_low = df[df['is_low']].iloc[-1]['low'] if df['is_low'].any() else df['low'].min()
    last_high = df[df['is_high']].iloc[-1]['high'] if df['is_high'].any() else df['high'].max()
    return last_low, last_high

def detect_valid_fvg(df):
    fvgs = []
    recent = df.tail(40).reset_index(drop=True)
    for i in range(len(recent)-2, 2, -1):
        # Bearish
        if recent.iloc[i-2]['low'] > recent.iloc[i]['high']:
            top = recent.iloc[i-2]['low']; bot = recent.iloc[i]['high']
            is_open = True
            for j in range(i+1, len(recent)):
                if recent.iloc[j]['high'] >= bot: is_open = False; break
            if is_open: fvgs.append({'type': 'BEARISH', 'price': (top+bot)/2}); break
        # Bullish
        elif recent.iloc[i-2]['high'] < recent.iloc[i]['low']:
            top = recent.iloc[i]['low']; bot = recent.iloc[i-2]['high']
            is_open = True
            for j in range(i+1, len(recent)):
                 if recent.iloc[j]['low'] <= top: is_open = False; break
            if is_open: fvgs.append({'type': 'BULLISH', 'price': (top+bot)/2}); break
    return fvgs[0] if fvgs else None

# ==============================================================================
# 5. BACKTEST ENGINE (V7)
# ==============================================================================

def run_quantum_backtest(df, asset_name):
    trades = 0; wins = 0; profit_r = 0.0
    total = len(df)
    
    for i in range(100, total - 50):
        row = df.iloc[i]
        signal_bt = None
        trend_bull = row['close'] > row['EMA_200']
        trend_bear = row['close'] < row['EMA_200']
        rsi = row['RSI']
        
        # LOGICA DO BACKTEST ADAPTADA
        if "BOOM" in asset_name:
             if trend_bull and rsi < 40: signal_bt = 'BUY'
        elif "CRASH" in asset_name:
             if trend_bear and rsi > 60: signal_bt = 'SELL'
        else:
             if trend_bull and rsi < 35: signal_bt = 'BUY'
             if trend_bear and rsi > 65: signal_bt = 'SELL'
        
        if signal_bt:
            entry = row['close']; atr = row['ATR']
            sl = entry - (atr*2) if signal_bt == 'BUY' else entry + (atr*2)
            tp = entry + (atr*4) if signal_bt == 'BUY' else entry - (atr*4)
            
            res = "OPEN"
            for f in range(i+1, min(i+60, total)):
                nxt = df.iloc[f]
                if signal_bt == 'BUY':
                    if nxt['low'] <= sl: res = "LOSS"; break
                    if nxt['high'] >= tp: res = "WIN"; break
                else:
                    if nxt['high'] >= sl: res = "LOSS"; break
                    if nxt['low'] <= tp: res = "WIN"; break
            
            if res != "OPEN":
                trades+=1
                if res == "WIN": wins+=1; profit_r+=2.0 # Reward maior
                else: profit_r-=1.0
                i = f
                
    wr = (wins/trades*100) if trades>0 else 0
    return {"WIN_RATE": round(wr,1), "TOTAL_TRADES": trades, "NET_PROFIT": round(profit_r,2)}

# ==============================================================================
# 6. PROCESSADOR CENTRAL
# ==============================================================================

def quantum_processor(name, m15_data, h4_data):
    df_m15 = indicators(prepare_df(m15_data))
    df_h4 = indicators(prepare_df(h4_data))
    bt = run_quantum_backtest(df_m15, name)
    
    curr_p = df_m15.iloc[-1]['close']
    rsi = df_m15.iloc[-1]['RSI']
    atr = df_m15.iloc[-1]['ATR']
    h4_bias = "BULLISH" if df_h4.iloc[-1]['close'] > df_h4.iloc[-1]['EMA_50'] else "BEARISH"
    s_low, s_high = find_swings(df_m15)
    fvg = detect_valid_fvg(df_m15)
    
    sig = "WAIT"; entry = curr_p; sl = curr_p; tp1 = curr_p; tp2 = curr_p; fvg_txt="NONE"

    # CONFLUENCE CHECK
    bull_confluence = (h4_bias == "BULLISH" and ((fvg and fvg['type']=='BULLISH') or rsi < 45))
    bear_confluence = (h4_bias == "BEARISH" and ((fvg and fvg['type']=='BEARISH') or rsi > 55))
    
    # --- PROTOCOLOS ESPECIFICOS ---
    if "BOOM" in name:
        if bull_confluence:
            sig = "STRONG BUY"
            entry = fvg['price'] if (fvg and fvg['type']=='BULLISH') else curr_p
            fvg_txt = f"Open FVG {entry:.2f}" if fvg else "No FVG"
            sl = s_low - (atr*0.5)
            # Risco Protegido
            risk = entry - sl
            if risk < atr: sl = entry - (atr*1.5); risk = entry-sl
            tp1 = entry + risk*2.0; tp2 = entry + risk*4.0
            
    elif "CRASH" in name:
        if bear_confluence:
            sig = "STRONG SELL"
            entry = fvg['price'] if (fvg and fvg['type']=='BEARISH') else curr_p
            fvg_txt = f"Open FVG {entry:.2f}" if fvg else "No FVG"
            sl = s_high + (atr*0.5)
            risk = sl - entry
            if risk < atr: sl = entry + (atr*1.5); risk = sl-entry
            tp1 = entry - risk*2.0; tp2 = entry - risk*4.0
            
    else: # Volatility Indices
        if bull_confluence:
            sig = "BUY"
            entry = fvg['price'] if (fvg and fvg['type']=='BULLISH') else curr_p
            sl = s_low; tp1 = entry + abs(entry-sl)*1.5; tp2 = entry + abs(entry-sl)*3.0
        elif bear_confluence:
            sig = "SELL"
            entry = fvg['price'] if (fvg and fvg['type']=='BEARISH') else curr_p
            sl = s_high; tp1 = entry - abs(sl-entry)*1.5; tp2 = entry - abs(sl-entry)*3.0

    return {
        "ASSET_NAME": name, "MACRO_TREND": h4_bias, "RSI_VAL": round(rsi,2),
        "FVG_DETECTED": fvg_txt, "FINAL_DECISION": sig,
        "MATH_ENTRY": round(entry,2), "MATH_SL": round(sl,2),
        "MATH_TP1": round(tp1,2), "MATH_TP2": round(tp2,2),
        "WIN_RATE": bt['WIN_RATE'], "TOTAL_TRADES": bt['TOTAL_TRADES'], "NET_PROFIT": bt['NET_PROFIT']
    }

# ==============================================================================
# 7. INTERFACE V7 (TRI-FORCE + GEMINI 3 EXCLUSIVE)
# ==============================================================================

st.sidebar.title("🔐 CHAVE GEMINI")
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ Chave Segura Detectada")
else:
    api_key = st.sidebar.text_input("Cole sua Chave Aqui", type="password")

st.sidebar.divider()
st.sidebar.markdown("""
### 🧠 INTELLIGENCE
**Model:** `gemini-3-pro-preview`
**Logic:** Tri-Force (M15/H1/H4)
**Engine:** Python Quantum
""")

st.title("💠 SI-APATECO QUANTUM V7")
st.caption("Using **models/gemini-3-pro-preview** | Data Stream: **Deriv Robust**")

with st.spinner("Conectando Rede Neural..."):
    assets = get_deriv_assets()

if not assets:
    st.error("❌ ERRO FATAL: Servidores Deriv indisponíveis no momento. Tente recarregar.")
    if st.button("♻️ Recarregar"): st.rerun()
    st.stop()

col_u, col_r = st.columns([1, 2])

with col_u:
    st.subheader("1. Configuração")
    target = st.selectbox("Selecione Ativo", list(assets.keys()))
    
    st.markdown("---")
    st.markdown("**📸 TRI-FORCE UPLOAD (Melhor Precisão)**")
    u_m15 = st.file_uploader("1. M15 (Gatilho)", type=['png', 'jpg'], key="u1")
    u_h1 = st.file_uploader("2. H1 (Estrutura)", type=['png', 'jpg'], key="u2")
    u_h4 = st.file_uploader("3. H4 (Direção)", type=['png', 'jpg'], key="u3")
    
    st.markdown("---")
    run = st.button("🚀 INICIAR GEMINI 3 PRO", use_container_width=True)

with col_r:
    if run:
        if not api_key: st.error("⚠️ FALTA API KEY."); st.stop()
        
        # Validar Uploads (Pelo menos 1)
        valid_images = []
        if u_m15: valid_images.append(Image.open(u_m15))
        if u_h1: valid_images.append(Image.open(u_h1))
        if u_h4: valid_images.append(Image.open(u_h4))
        
        if not valid_images:
            st.warning("⚠️ Você precisa enviar pelo menos o print do M15.")
            st.stop()
            
        st.divider()
        status = st.status("💎 PROCESSANDO CORE...", expanded=True)
        
        status.write(f"📡 API: Obtendo dados reais de {target}...")
        m15_raw, h4_raw, err = asyncio.run(fetch_candles_safe(assets[target]))
        
        if err:
            status.update(label="Falha API", state="error")
            st.error(f"Erro: {err}")
            st.stop()
            
        status.write("🧮 PYTHON: Calculando Matemática do Preço (Pandas V2 Fix)...")
        # Processamento Vetorial
        res = quantum_processor(target, m15_raw, h4_raw)
        
        status.write(f"🧠 IA: Chamando **gemini-3-pro-preview** ({len(valid_images)} imagens)...")
        
        # --- GEMINI 3 PRO PREVIEW CALL ---
        genai.configure(api_key=api_key)
        final_text = ""
        
        try:
            # CHAMADA ESPECÍFICA DO MODELO PEDIDO
            model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
            
            # Monta Payload (Prompt + JSON + Imagens)
            payload = [SYSTEM_PROMPT, f"DATA_JSON: {json.dumps(res)}"] + valid_images
            
            response = model.generate_content(payload)
            final_text = response.text
            status.update(label="ANÁLISE CONCLUÍDA", state="complete")
            
        except Exception as e:
            # Se der erro no 3-pro, mostramos o erro mas tentamos salvar com o 1.5 PRO (Fallback oculto para não travar app)
            # Mas a prioridade foi o 3-PRO
            st.warning(f"Erro no 'gemini-3-pro-preview': {e}. Tentando fallback...")
            try:
                 fallback = genai.GenerativeModel("gemini-1.5-pro", safety_settings=SAFETY_SETTINGS)
                 payload = [SYSTEM_PROMPT, f"DATA_JSON: {json.dumps(res)}"] + valid_images
                 response = fallback.generate_content(payload)
                 final_text = response.text
                 status.update(label="ANÁLISE (VIA FALLBACK)", state="complete")
            except:
                 st.error("Erro Crítico de IA.")
                 st.stop()

        # RENDERIZAR RESULTADOS
        
        # 1. Backtest Box
        st.subheader("📊 DESEMPENHO ALGORÍTMICO")
        m1, m2, m3 = st.columns(3)
        m1.metric("Backtest (Win%)", f"{res['WIN_RATE']}%")
        m2.metric("Saldo Líquido (R)", f"{res['NET_PROFIT']}R")
        m3.metric("Trade Bias", res['FINAL_DECISION'])
        
        # 2. Math Table
        st.dataframe([res], use_container_width=True)
        
        # 3. Gemini Response
        st.divider()
        st.subheader("🤖 VEREDITO TRI-FORCE (Gemini 3)")
        st.markdown(final_text)
