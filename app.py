import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import numpy as np
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="SI-QA: Auto-Decision Kernel",
    page_icon="🧠",
    layout="wide"
)

# --- ESTILO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #00ff00; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #004d00; color: #ffffff; border: 1px solid #00ff00; font-weight: bold; }
    div[data-testid="stExpander"] { border: 1px solid #00ff00; background-color: #0a0a0a; }
    h1, h2, h3 { color: #00ff00 !important; }
</style>
""", unsafe_allow_html=True)

# --- PROMPT MESTRE ORIGINAL (INALTERADO) ---
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

# --- FUNÇÕES ---

@st.cache_data(ttl=3600)
def buscar_lista_ativos_deriv():
    """Baixa lista oficial da Deriv"""
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

async def get_deriv_history_hybrid(symbol_code):
    """
    Baixa dados de H1 (1 Hora) com profundidade de 500 velas.
    Isso cobre tanto Day Trade (últimas 24h) quanto Swing (últimos 20 dias).
    """
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            req = {
                "ticks_history": symbol_code,
                "adjust_start_time": 1,
                "count": 500, 
                "end": "latest",
                "style": "candles",
                "granularity": 3600 # 3600s = H1 (Timeframe Híbrido)
            }
            await websocket.send(json.dumps(req))
            res = await websocket.recv()
            data = json.loads(res)
            if 'error' in data: return None, data['error']['message']
            return data['candles'], None
    except Exception as e:
        return None, str(e)

def calcular_indicadores_hibridos(df):
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    
    # EMAs
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()   # Day Trade Trend
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()   # Medium Trend
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean() # Swing Trade Trend
    
    # Bollinger & Z-Score
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    
    # ATR
    df['tr'] = np.maximum((df['high'] - df['low']), 
                          np.maximum(abs(df['high'] - df['close'].shift()), 
                                     abs(df['low'] - df['close'].shift())))
    df['ATR'] = df['tr'].rolling(window=14).mean()
    
    return df.dropna()

def executar_backtest_estatistico(df):
    total = len(df)
    # Analise de Força de Tendência (Para decidir se é Swing)
    candles_acima_ema200 = len(df[df['close'] > df['EMA_200']])
    forca_tendencia = (candles_acima_ema200 / total) * 100 # % do tempo acima da média longa
    
    return f"""
    [HYBRID DATA ANALYSIS - LAST {total} HOURS]
    - EMA 200 (Long Term Trend): {df['EMA_200'].iloc[-1]:.2f}
    - Trend Stability Score: {forca_tendencia:.1f}% ( > 50% implies Bullish Macro)
    - Current Volatility (ATR): {df['ATR'].iloc[-1]:.4f}
    """

def identificar_ativo_via_ia(img, model, lista_oficial_ativos):
    prompt = "Extract the ASSET NAME from the chart header exactly. Return ONLY the name."
    try:
        response = model.generate_content([prompt, img])
        texto_detectado = response.text.upper().strip()
        texto_limpo = texto_detectado.replace("INDEX", "").strip()
        melhor_match = None
        codigo_match = None
        for nome_oficial, codigo in lista_oficial_ativos.items():
            nome_oficial_limpo = nome_oficial.replace("INDEX", "").strip()
            if texto_limpo in nome_oficial_limpo or nome_oficial_limpo in texto_limpo:
                melhor_match = nome_oficial
                codigo_match = codigo
                if texto_limpo == nome_oficial_limpo: break
        return melhor_match, codigo_match, texto_detectado
    except Exception as e:
        return None, None, str(e)

# --- INTERFACE ---

st.sidebar.header("⚙️ SI-QA CONFIG")
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ Conectado")
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.title("🧠 SI-QA: Autonomous Analyst")
st.markdown("### Detector Automático: Day Trade & Swing Trade")

with st.spinner("Carregando Ativos Deriv..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()

if not LISTA_ATIVOS:
    st.error("Sem conexão com a Deriv.")
    st.stop()

col1, col2 = st.columns(2)
with col1: img_main = st.file_uploader("Gráfico (Qualquer Timeframe)", type=['png', 'jpg'])
with col2: st.info("O sistema decidirá automaticamente se o sinal é para Day Trade ou Swing baseando-se na estrutura fractal encontrada.")

if st.button("ANALISAR MERCADO", type="primary"):
    if not api_key or not img_main:
        st.error("API ou Imagem faltando.")
        st.stop()
        
    status = st.status("Iniciando Módulo de Inteligência Híbrida...", expanded=True)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-3-flash-preview")
    
    # 1. VISÃO
    status.write("👁️ Identificando Ativo...")
    nome_ativo, codigo, txt = identificar_ativo_via_ia(Image.open(img_main), model, LISTA_ATIVOS)
    
    if not nome_ativo:
        status.update(label="Falha de Visão", state="error")
        st.error(f"Não reconhecido: {txt}")
        st.stop()
        
    status.write(f"✅ Ativo: {nome_ativo}")
    
    # 2. DADOS (H1 - Híbrido)
    status.write("📡 Baixando dados H1 (Contexto Amplo)...")
    candles, erro = asyncio.run(get_deriv_history_hybrid(codigo))
    if erro: st.error(erro); st.stop()
    
    # 3. CÁLCULOS
    df = pd.DataFrame(candles)
    df['epoch'] = pd.to_datetime(df['epoch'], unit='s')
    df_full = calcular_indicadores_hibridos(df)
    stats = executar_backtest_estatistico(df_full)
    
    # 4. INJEÇÃO DE TAREFA (AQUI A MÁGICA ACONTECE)
    # Pedimos para a IA decidir o estilo
    prompt_injecao = f"""
    TARGET ASSET: {nome_ativo}
    CURRENT PRICE: {df_full.iloc[-1]['close']}
    
    === HYBRID MATH DATA (H1 TIMEFRAME - 500 CANDLES) ===
    Last 15 Candles:
    {df_full.tail(15).to_string()}
    
    === STATISTICAL CONTEXT ===
    {stats}
    
    === TASK: DECISION MODE ===
    1. Analyze the Visual Structure + Math Data.
    2. DETERMINE THE BEST STRATEGY: 
       - If structure is huge (Weekly/Daily levels) -> SWING TRADE.
       - If structure is intraday flow -> DAY TRADE.
    3. Explicitly state the "TRADING STYLE CHOSEN" in the output.
    4. Execute SI-QA Logic normally.
    """
    
    inputs = [SYSTEM_PROMPT, prompt_injecao, Image.open(img_main)]
    
    status.write("🧠 Decidindo melhor abordagem (Day vs Swing)...")
    response = model.generate_content(inputs)
    
    status.update(label="Decisão Tomada", state="complete", expanded=False)
    st.divider()
    st.markdown(response.text)