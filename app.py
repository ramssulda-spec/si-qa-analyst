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

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="SI-QA: Tri-Force Analyst",
    page_icon="⚡",
    layout="wide"
)

# --- ESTILO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #00ff00; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #004d00; color: #ffffff; border: 1px solid #00ff00; font-weight: bold; width: 100%; }
    div[data-testid="stExpander"] { border: 1px solid #00ff00; background-color: #0a0a0a; }
    h1, h2, h3 { color: #00ff00 !important; }
    .stFileUploader>div>div>button { color: #000; background-color: #00ff00; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO DE SEGURANÇA (Para evitar bloqueios em gráficos vermelhos) ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# PROMPT MESTRE ORIGINAL (100% INTACTO)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE & SYSTEM KERNEL
You are the "Synthetic Indices Quantum Architect" (SI-QA).
You exist solely to decode the PRNG (Pseudo-Random Number Generator) algorithms of the Deriv Synthetic Market.

>> YOUR DNA:
1. You DO NOT guess. You DO NOT predict. You CALCULATE probability densities.
2. Synthetic Indices are non-sentimental; they are mathematically bound by specific algorithms.
3. Your analysis must rely on Volatility Cycles, Mathematical Deviation (Z-Score), and Fractal Algorithm Defects.

 CRITICAL INPUT PROTOCOL (MANDATORY)
Since you function as a text/vision processing engine, you require INPUT to execute the code.
User MUST provide either:
A) A High-Definition Screenshot of the chart (Timeframes: M15, H1, H4).
B) A Data Array of the last 30-50 Candles (OHLC Values).
**IF NO DATA IS PROVIDED: State "AWAITING DATA INJECTION" and Pause.**

 PHASE 0: INDEX-SPECIFIC SUB-ROUTINE LOADING
First, Identify the Asset and Load its specific Logic:

[SUB-ROUTINE A: VOLATILITY INDICES (V75, V10, V100)]
Focus: Standard Deviation Expansions, Mean Reversion to Moving Averages (EMA 20/50), Accumulation/Distribution.
Triggers: Breakers + ATR expansion > 2.0.

[SUB-ROUTINE B: SPIKE INDICES (BOOM & CRASH)]
Focus: Tick Counting, Drop/Spike Rejection zones, "N" Pattern formation.
Rule: AGAINST the Spike trading is BANNED unless Structure Shift is confirmed on H1.
Rule: WITH the Spike trading requires 'Golden Pocket' Retracement (61.8% - 78.6%).

[SUB-ROUTINE C: DISCRETE INDICES (STEP & JUMP)]
Focus: Level Ladders, Support breaks.
Triggers: Only Break & Retest of flat levels.

 PHASE 1: PRNG ALGORITHMIC DECODER (THE QUANTUM SCAN)

1.1. ALGORITHMIC REGIME DETECTION
Calculate current state relative to recent history:
- [0] Dead Zone: Low volatility/ATR < Historical Mean. (ACTION: IDLE)
- [1] Pump/Dump: Volatility > 3 Sigma. (ACTION: FADE/REVERSION)
- [2] Flow State: Consistent HH/HL sequence w/ Displacement. (ACTION: TREND FOLLOWING)

1.2. FRACTAL NOISE CANCELLATION
Identify and DISCARD "Noise Candles":
- Candles with >50% Wicks relative to Body.
- Candles strictly inside previous candle range (Harami/Inside Bar).
*Target only "Power Candles" (Body > 70% of Range).*

 PHASE 2: THE "MATH-FIRST" VALIDATION GATES
The setup is valid ONLY if the Boolean Logic is TRUE for ALL:

1. [DISPLACEMENT VELOCITY]: Did price move away from the zone faster (fewer candles) than it took to get there? [T/F]
2. [LIQUIDITY EXTRACTION]: Did the move initiate AFTER clearing a fractal High/Low? (The Judas Swing) [T/F]
3. [PREMIUM/DISCOUNT ARRAY]: Is the entry in the correct Quadrant (Above 50% for Sell, Below 50% for Buy)? [T/F]
4. [IMBALANCE PRESENCE]: Is there an unmitigated FVG or Algorithm Gap clearly visible? [T/F]

If ANY is "False" => STATUS: ABORT_NO_EDGE.

 PHASE 3: REAL-TIME BACKTEST SIMULATION (VIRTUAL)
*Mental Simulation:*
"Scan the visible chart history. Look for the EXACT same pattern setup. How many times did it appear? How many times did it fail?"
- Pattern Frequency Score (1-10)
- Failure Rate estimation.
*If Failure Rate in simulation > 40% -> ABORT.*

 PHASE 4: EXECUTION MATRIX (SURGICAL PRECISION)

>> ENTRY ZONES (Choose One Best Match):
1. **The Origin (Extreme):** Order Block Body Open (Precision Entry).
2. **The Equilibrium (Fair Value):** 50% of the FVG.
3. **The Spike Limit (Boom/Crash):** Previous Spike Base + Spread.

>> RISK PARAMETERS (Dynamic):
- Stop Loss: MUST be protected by a structural Invalidity Point (ATR Buffer added).
- Risk Reward Ratio: STRICTLY > 1:3. No exceptions.

 PHASE 5: PROBABILITY & OUTPUT GENERATION

Compute final score "Win Probability" (WP) based on Confluences/Regime.
Output formatted specifically for trader execution.

---
 OUTPUT TERMINAL:
(Render this specifically when you analyze the data)

/// SYNTHETIC QUANTUM DECODER ///
[TIMESTAMP: Current | ASSET: {Symbol}]

SYSTEM STATE: {CALCULATING...}
>> REGIME DETECTED: [ {Type} | STRENGTH: {0-100}% ]
   *Mathematical Context: (e.g. 2 SD Expansion, Range Bound)*

>> PRNG DECODING:
   [1] Structure Break: {YES/NO/PENDING}
   [2] Algorithm Trap (Fakeout): {DETECTED/CLEAN}
   [3] Momentum Velocity: {ACCELERATING / DECELERATING}

>> VIRTUAL BACKTEST CHECK:
   "Similar structures in current view have yielded positive reactions X out of Y times."

>> STRATEGY EXECUTION:
    ACTION: {BUY LIMIT / SELL LIMIT / BUY NOW / SELL NOW / STAY OUT}
    ENTRY PRICE (Specific): {1234.56}
    STOP LOSS (Hard Deck): {1230.00}
    TAKE PROFIT 1 (Liq pool): {1250.00}
    TAKE PROFIT 2 (Extension): {1280.00}

>> FINAL CONFIDENCE RATING:
    PROBABILITY: {XX.X%}
    CRITICAL WARNING: {Example: "Against Trend," "Approaching Key Level"}
    ADVICE: {One precise tactical instruction}

---------------------------------------------------
COMMAND: WAITING FOR CHART IMAGE OR OHLC DATA ARRAY TO INITIATE DECODING.
)
"""

# --- FUNÇÕES DE API ---

@st.cache_data(ttl=3600)
def buscar_lista_ativos_deriv():
    async def _fetch():
        uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
        try:
            async with websockets.connect(uri) as ws:
                req = {"active_symbols": "brief", "product_type": "basic"}
                await ws.send(json.dumps(req))
                res = await ws.recv()
                data = json.loads(res)
                if 'error' in data: return None
                ativos_dict = {}
                for item in data['active_symbols']:
                    if item['market'] == 'synthetic_index':
                        ativos_dict[item['display_name'].upper()] = item['symbol']
                return ativos_dict
        except: return None
    return asyncio.run(_fetch())

async def get_triple_data(symbol_code):
    """
    BAIXA DADOS DE M15, H1 e H4 SIMULTANEAMENTE
    """
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            # Solicitações
            req_m15 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 50, "end": "latest", "style": "candles", "granularity": 900}
            req_h1 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 100, "end": "latest", "style": "candles", "granularity": 3600}
            req_h4 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 14400}
            
            # Envia e Recebe M15
            await websocket.send(json.dumps(req_m15))
            res_m15 = await websocket.recv()
            
            # Envia e Recebe H1
            await websocket.send(json.dumps(req_h1))
            res_h1 = await websocket.recv()
            
            # Envia e Recebe H4
            await websocket.send(json.dumps(req_h4))
            res_h4 = await websocket.recv()
            
            d_m15 = json.loads(res_m15)
            d_h1 = json.loads(res_h1)
            d_h4 = json.loads(res_h4)
            
            if 'error' in d_m15 or 'error' in d_h1 or 'error' in d_h4: return None, None, None, "Erro API"
            
            return d_m15['candles'], d_h1['candles'], d_h4['candles'], None
    except Exception as e:
        return None, None, None, str(e)

# --- CÁLCULOS MATEMÁTICOS ---

def calcular_indicadores(df):
    df['close'] = df['close'].astype(float)
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean() # Tendência Mestra
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    return df.dropna()

def analisar_imagem(img, model, lista_ativos):
    prompt = "Identify Asset Name ONLY. Return: ASSET_NAME"
    try:
        response = model.generate_content([prompt, img])
        nome_raw = response.text.upper().strip().replace("INDEX", "").strip()
        nome_ativo = None
        codigo_ativo = None
        for k, v in lista_ativos.items():
            k_clean = k.replace("INDEX", "").strip()
            if nome_raw in k_clean or k_clean in nome_raw:
                nome_ativo = k; codigo_ativo = v; break
        return nome_ativo, codigo_ativo
    except: return None, None

# --- INTERFACE ---
st.sidebar.header("⚙️ SI-QA CONFIG")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.title("⚡ SI-QA: Tri-Force Analyst")
st.markdown("### Análise Fractal Simultânea (M15 + H1 + H4)")
st.info("O sistema analisará os 3 tempos gráficos e decidirá automaticamente se o melhor trade é **Day Trade** ou **Swing Trade**.")

with st.spinner("Conectando..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ÁREA DE UPLOAD TRIPLO
col1, col2, col3 = st.columns(3)
with col1: img_m15 = st.file_uploader("1. M15 (Micro)", type=['png', 'jpg'])
with col2: img_h1 = st.file_uploader("2. H1 (Tendência)", type=['png', 'jpg'])
with col3: img_h4 = st.file_uploader("3. H4 (Macro)", type=['png', 'jpg'])

if st.button("ANALISAR E DECIDIR MELHOR SINAL"):
    if not api_key: st.error("Falta API Key."); st.stop()
    
    # Pega qualquer imagem para identificar o ativo
    img_p = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
    if not img_p: st.error("Envie pelo menos uma imagem."); st.stop()
        
    status = st.status("Iniciando Análise Tri-Dimensional...", expanded=True)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
    
    # 1. Identificação
    status.write("👁️ Identificando Ativo...")
    nome, codigo = analisar_imagem(Image.open(img_p), model, LISTA_ATIVOS)
    
    if not nome: status.update(label="Erro Visão", state="error"); st.stop()
    status.write(f"✅ Ativo: {nome}")
    
    # 2. Dados Triplos
    status.write("📡 Baixando dados matemáticos de M15, H1 e H4...")
    c_m15, c_h1, c_h4, erro = asyncio.run(get_triple_data(codigo))
    if erro: st.error(erro); st.stop()
    
    df_m15 = calcular_indicadores(pd.DataFrame(c_m15))
    df_h1 = calcular_indicadores(pd.DataFrame(c_h1))
    df_h4 = calcular_indicadores(pd.DataFrame(c_h4))
    
    # 3. Prompt de Injeção Inteligente
    inputs_gemini = [SYSTEM_PROMPT]
    contexto = "IMAGES PROVIDED:\n"
    if img_m15: inputs_gemini.append(Image.open(img_m15)); contexto+="- IMAGE 1: M15 (Gatilho Curto)\n"
    if img_h1: inputs_gemini.append(Image.open(img_h1)); contexto+="- IMAGE 2: H1 (Estrutura Média)\n"
    if img_h4: inputs_gemini.append(Image.open(img_h4)); contexto+="- IMAGE 3: H4 (Tendência Macro)\n"
    
    # Dados matemáticos resumidos para não estourar o prompt
    prompt_injecao = f"""
    TARGET: {nome}
    
    {contexto}
    
    === TRIPLE TIMEFRAME MATHEMATICS ===
    [H4 - MACRO]
    Price: {df_h4.iloc[-1]['close']}
    EMA 200 (Long Trend): {df_h4.iloc[-1]['EMA_200']:.2f}
    Z-Score: {df_h4.iloc[-1]['Z_Score']:.2f}
    Trend Status: {"BULLISH" if df_h4.iloc[-1]['close'] > df_h4.iloc[-1]['EMA_200'] else "BEARISH"}
    
    [H1 - STRUCTURE]
    Price: {df_h1.iloc[-1]['close']}
    Z-Score: {df_h1.iloc[-1]['Z_Score']:.2f}
    
    [M15 - ENTRY]
    Price: {df_m15.iloc[-1]['close']}
    Z-Score: {df_m15.iloc[-1]['Z_Score']:.2f}
    
    === CRITICAL TASK: AUTO-DECISION ===
    1. Compare H4 Trend vs M15 Entry.
    2. DECIDE THE BEST TRADE TYPE:
       - IF H4 structure is dominant (e.g. hitting major support) -> CALL "SWING TRADE".
       - IF H4 is flat but H1 is trending -> CALL "DAY TRADE".
    3. Output the single best high-probability signal based on this confluence.
    4. IGNORE M15 scalping signals that conflict with H4 trend.
    """
    
    inputs_gemini.append(prompt_injecao)
    
    try:
        status.write("🧠 Cruzando dados e decidindo estratégia...")
        resp = model.generate_content(inputs_gemini)
        status.update(label="Análise Pronta", state="complete")
        st.divider()
        st.markdown(resp.text)
        
        # Mostra os dados técnicos para você conferir
        with st.expander("Ver Dados Técnicos (Raio-X)"):
            c1, c2, c3 = st.columns(3)
            with c1: st.write("**M15 Z-Score:**", f"{df_m15.iloc[-1]['Z_Score']:.2f}")
            with c2: st.write("**H1 Z-Score:**", f"{df_h1.iloc[-1]['Z_Score']:.2f}")
            with c3: st.write("**H4 Trend:**", "ALTA" if df_h4.iloc[-1]['close'] > df_h4.iloc[-1]['EMA_200'] else "BAIXA")
            
    except Exception as e:
        st.error(f"Erro na geração: {e}")