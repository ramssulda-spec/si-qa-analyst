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
    page_title="SI-QA: Universal Auto-Detect",
    page_icon="🧬",
    layout="wide"
)

# --- CSS ESTILO "MATRIX" ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #00ff00; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #003300; color: #00ff00; border: 1px solid #00ff00; }
    .stButton>button:hover { background-color: #00ff00; color: black; }
    div[data-testid="stExpander"] { border: 1px solid #00ff00; background-color: #050505; }
    h1, h2, h3 { color: #00ff00 !important; }
    .stTextInput>div>div>input { color: #00ff00; background-color: #111; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- PROMPT MESTRE (SI-QA - INTEGRA) ---
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

# --- FUNÇÕES DE API DINÂMICA (SEM MAPA FIXO) ---

@st.cache_data(ttl=3600) # Cache por 1 hora para não pesar
def buscar_lista_ativos_deriv():
    """Conecta na Deriv e baixa a lista OFICIAL de todos os ativos existentes."""
    async def _fetch():
        uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
        try:
            async with websockets.connect(uri) as ws:
                # Pede todos os símbolos ativos
                req = {"active_symbols": "brief", "product_type": "basic"}
                await ws.send(json.dumps(req))
                res = await ws.recv()
                data = json.loads(res)
                
                if 'error' in data: return None
                
                # Cria um dicionário { "NOME LEGÍVEL": "CÓDIGO API" }
                ativos_dict = {}
                for item in data['active_symbols']:
                    # Filtra apenas sintéticos (geralmente market 'synthetic_index')
                    if item['market'] == 'synthetic_index':
                        ativos_dict[item['display_name'].upper()] = item['symbol']
                return ativos_dict
        except:
            return None
            
    return asyncio.run(_fetch())

async def get_deriv_history(symbol_code):
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            req = {
                "ticks_history": symbol_code,
                "adjust_start_time": 1,
                "count": 500, # 500 velas para Backtest
                "end": "latest",
                "style": "candles",
                "granularity": 900
            }
            await websocket.send(json.dumps(req))
            res = await websocket.recv()
            data = json.loads(res)
            if 'error' in data: return None, data['error']['message']
            return data['candles'], None
    except Exception as e:
        return None, str(e)

# --- FUNÇÕES DE CÁLCULO (O MOTOR) ---

def calcular_indicadores_avancados(df):
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    
    # EMAs
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # Bollinger & Z-Score
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
    df['Lower'] = df['SMA_20'] - (df['STD_20'] * 2)
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    
    # ATR
    df['tr'] = np.maximum((df['high'] - df['low']), 
                          np.maximum(abs(df['high'] - df['close'].shift()), 
                                     abs(df['low'] - df['close'].shift())))
    df['ATR'] = df['tr'].rolling(window=14).mean()
    
    return df.dropna()

def executar_backtest_estatistico(df):
    total = len(df)
    if total < 50: return "Insufficient Data for Backtest"
    
    # Lógica de Backtest Simplificada para Prompt
    # Conta quantas vezes o preço tocou na EMA e respeitou a tendência
    toques = 0
    respeitos = 0
    
    for i in range(1, total-1):
        ema = df['EMA_20'].iloc[i]
        low = df['low'].iloc[i]
        high = df['high'].iloc[i]
        
        # Se tocou na EMA
        if low <= ema <= high:
            toques += 1
            # Verifica candle seguinte (Exemplo: se close > ema anterior e próximo close > close anterior)
            if df['close'].iloc[i+1] > df['close'].iloc[i]:
                respeitos += 1
                
    rate = (respeitos / toques * 100) if toques > 0 else 0
    sigma_events = len(df[abs(df['Z_Score']) > 3])
    
    return f"""
    [BACKTEST REPORT - 500 CANDLES]
    - EMA 20 Interaction Events: {toques}
    - Bounce/Trend Continuation Rate: {rate:.1f}%
    - Extreme Volatility Events (Z>3): {sigma_events}
    - Current Volatility (ATR): {df['ATR'].iloc[-1]:.4f}
    """

def identificar_ativo_via_ia(img, model, lista_oficial_ativos):
    """
    1. IA lê o texto da imagem.
    2. Python compara o texto com a lista oficial da Deriv para achar o match.
    """
    prompt = "Extract the ASSET NAME from the chart header exactly as written (e.g. 'Crash 1000 Index'). Return ONLY the name."
    try:
        response = model.generate_content([prompt, img])
        texto_detectado = response.text.upper().strip()
        
        # Algoritmo de Busca Fuzzy (Encontrar o ativo na lista oficial)
        # Removemos 'INDEX' para facilitar a comparação
        texto_limpo = texto_detectado.replace("INDEX", "").strip()
        
        melhor_match = None
        codigo_match = None
        
        # Varre a lista dinâmica que baixamos da API
        for nome_oficial, codigo in lista_oficial_ativos.items():
            nome_oficial_limpo = nome_oficial.replace("INDEX", "").strip()
            
            # Se o texto da IA estiver contido no nome oficial (ou vice versa)
            if texto_limpo in nome_oficial_limpo or nome_oficial_limpo in texto_limpo:
                melhor_match = nome_oficial
                codigo_match = codigo
                # Prioridade máxima para matches exatos (especialmente os '1s')
                if texto_limpo == nome_oficial_limpo:
                    break
        
        return melhor_match, codigo_match, texto_detectado
        
    except Exception as e:
        return None, None, str(e)

# --- INTERFACE ---

# --- GESTÃO DE CHAVES DE SEGURANÇA ---
st.sidebar.header("🔐 SI-QA KEY")

# Tenta pegar a chave dos segredos do sistema (Nuvem ou Local)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ Chave API Integrada (Modo Seguro)")
else:
    # Se não achar, pede manualmente (Fallback)
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.title("🧬 SI-QA: Universal Detector")
st.markdown("### Sistema Autônomo de Reconhecimento e Análise")

# Carrega a lista de ativos assim que abre o app (silenciosamente)
with st.spinner("Atualizando banco de dados de ativos da Deriv..."):
    LISTA_ATIVOS_DINAMICA = buscar_lista_ativos_deriv()

if not LISTA_ATIVOS_DINAMICA:
    st.error("Erro ao conectar na Deriv para baixar lista de ativos. Verifique internet.")
    st.stop()
else:
    st.sidebar.success(f"Banco de Dados Atualizado: {len(LISTA_ATIVOS_DINAMICA)} ativos sintéticos carregados.")

col1, col2, col3 = st.columns(3)
with col1: img_m15 = st.file_uploader("M15 (Scan Target)", type=['png', 'jpg'])
with col2: img_h1 = st.file_uploader("H1 (Structure)", type=['png', 'jpg'])
with col3: img_h4 = st.file_uploader("H4 (Trend)", type=['png', 'jpg'])

if st.button("INICIAR VARREDURA UNIVERSAL", type="primary"):
    if not api_key or not img_m15:
        st.error("Preciso da API Key e do gráfico M15.")
        st.stop()
        
    status = st.status("Iniciando Protocolo...", expanded=True)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-3-flash-preview")
    
    # 1. IDENTIFICAÇÃO (USANDO LISTA DINÂMICA)
    status.write("👁️ Analisando imagem e cruzando com banco de dados Deriv...")
    nome_ativo, codigo_ativo, texto_lido = identificar_ativo_via_ia(Image.open(img_m15), model, LISTA_ATIVOS_DINAMICA)
    
    if nome_ativo:
        status.write(f"✅ Identificado: **{nome_ativo}** (API: {codigo_ativo})")
    else:
        status.update(label="Falha de Identificação", state="error")
        st.error(f"A IA leu '{texto_lido}', mas não encontrei correspondência na lista da Deriv.")
        st.write("Ativos disponíveis:", list(LISTA_ATIVOS_DINAMICA.keys()))
        st.stop()
        
    # 2. DOWNLOAD & BACKTEST
    status.write(f"📡 Baixando histórico profundo ({nome_ativo})...")
    candles, erro = asyncio.run(get_deriv_history(codigo_ativo))
    
    if erro:
        st.error(f"Erro no download: {erro}")
        st.stop()
        
    status.write("🧮 Executando Backtest Estatístico (500 Candles)...")
    df = pd.DataFrame(candles)
    df['epoch'] = pd.to_datetime(df['epoch'], unit='s')
    df_full = calcular_indicadores_avancados(df)
    
    relatorio_backtest = executar_backtest_estatistico(df_full)
    
    # 3. EXECUÇÃO IA
    status.write("🧠 Quantum Architect: Decodificando...")
    
    prompt_injecao = f"""
    TARGET ASSET: {nome_ativo}
    CURRENT PRICE: {df_full.iloc[-1]['close']}
    
    === PHASE 3: VIRTUAL BACKTEST REPORT ===
    {relatorio_backtest}
    
    === PHASE 2: LIVE MATH DATA (LAST 15 CANDLES) ===
    {df_full.tail(15).to_string()}
    
    TASK: Execute SI-QA Logic.
    """
    
    inputs = [SYSTEM_PROMPT, prompt_injecao, Image.open(img_m15)]
    if img_h1: inputs.append(Image.open(img_h1))
    if img_h4: inputs.append(Image.open(img_h4))
    
    response = model.generate_content(inputs)
    status.update(label="Concluído", state="complete", expanded=False)
    
    st.divider()
    st.markdown(response.text)