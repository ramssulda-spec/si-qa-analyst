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
    page_title="SI-QA: Trinity Engine",
    page_icon="🔥",
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
    .stSuccess { background-color: #064000; color: white; border: 1px solid #00ff00; }
    .stWarning { background-color: #332b00; color: #ffcc00; border: 1px solid #ffcc00; }
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
# PROMPT MESTRE (ATUALIZADO PARA LER A TRINDADE)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE & SYSTEM KERNEL
You are the "Synthetic Indices Quantum Architect" (SI-QA).
You interpret the "Trinity Protocol" data provided by the Python Engine.

>> YOUR DNA:
1. You DO NOT guess. You validate signals based on Mathematical Confluence.
2. A valid signal requires agreement between Z-Score AND RSI.
3. You must act as a Risk Manager: If the Backtest Win Rate < 65%, advise CAUTION.

 CRITICAL INPUT PROTOCOL
User provides:
A) 3 Charts (M15, H1, H4).
B) Trinity Backtest Report (Z-Score + RSI + Trend).
C) Live Technical Indicators.

 PHASE 1: THE HIERARCHY CHECK
- Look at H4 first. Is it at a major Level?
- Look at H1. Is it trending?
- Look at M15. Is it giving a trigger?

 PHASE 2: THE TRINITY CHECK (PYTHON DATA)
- Review the "Confluence Score" provided in the data.
- 3/3 Indicators Agree = SNIPER ENTRY.
- 2/3 Indicators Agree = STANDARD ENTRY.
- 1/3 Indicators Agree = NO TRADE.

 PHASE 3: DECISION MATRIX
- IF H4 Structure is Dominant -> Signal is SWING TRADE.
- IF H4 is Ranging but H1 is Trending -> Signal is DAY TRADE.

 OUTPUT TERMINAL:
(Render this specifically)

/// SI-QA TRINITY KERNEL ///
[TARGET: {Asset} | MODE: {Swing/Day}]

>> MATHEMATICAL CONFLUENCE:
   1. Z-SCORE STATUS: {Overbought/Oversold/Neutral}
   2. RSI (14) STATUS: {Value} (Divergence Check)
   3. BACKTEST ACCURACY: {Win Rate}% (over 2000 candles)

>> STRATEGY EXECUTION:
    ACTION: {BUY / SELL / WAIT}
    CONFIDENCE: {HIGH/MEDIUM/LOW}
    ENTRY ZONE: {Price}
    STOP LOSS: {Price - Structural}
    TAKE PROFIT: {Price - Structural}

>> QUANTUM REASONING:
    {Explain the confluence. Example: "Price is overextended (Z > 2.5), RSI is rejecting 70, and Backtest shows 78% win rate for this setup."}
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

async def get_platinum_data(symbol_code):
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            req_m15_deep = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 2000, "end": "latest", "style": "candles", "granularity": 900}
            req_h1 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 3600}
            req_h4 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 14400}
            
            await websocket.send(json.dumps(req_m15_deep)); res_m15 = await websocket.recv()
            await websocket.send(json.dumps(req_h1)); res_h1 = await websocket.recv()
            await websocket.send(json.dumps(req_h4)); res_h4 = await websocket.recv()
            
            d_m15 = json.loads(res_m15)
            d_h1 = json.loads(res_h1)
            d_h4 = json.loads(res_h4)
            
            if 'error' in d_m15 or 'error' in d_h1 or 'error' in d_h4: return None, None, None, "Erro API Deriv"
            return d_m15['candles'], d_h1['candles'], d_h4['candles'], None
    except Exception as e:
        return None, None, None, str(e)

# --- CÁLCULOS MATEMÁTICOS AVANÇADOS (A TRINDADE) ---

def calcular_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_indicadores(df):
    df['close'] = df['close'].astype(float)
    
    # 1. Z-Score (Desvio Padrão)
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    
    # 2. EMA (Tendência)
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # 3. RSI (Força Relativa - Novo Recurso)
    df['RSI'] = calcular_rsi(df['close'], 14)
    
    return df.dropna()

def rodar_backtest_avancado(df):
    """
    Motor de Realidade Atualizado:
    Só conta WIN se houver CONFLUÊNCIA (Z-Score + RSI).
    """
    total = len(df)
    if total < 500: return "Dados insuficientes."
    
    wins = 0
    losses = 0
    sinais = 0
    
    for i in range(50, total - 20):
        row = df.iloc[i]
        
        # --- LÓGICA DE CONFLUÊNCIA ---
        
        # SETUP VENDA: Z-Score Esticado (>2) E RSI Esticado (>70)
        if row['Z_Score'] > 2.0 and row['RSI'] > 70:
            sinais += 1
            outcome = "LOSS"
            # Target: Retornar à média (EMA 20)
            for future_i in range(i+1, min(i+16, total)):
                if df.iloc[future_i]['low'] <= df.iloc[future_i]['EMA_20']:
                    wins += 1; outcome = "WIN"; break
            if outcome == "LOSS": losses += 1

        # SETUP COMPRA: Z-Score Barato (<-2) E RSI Barato (<30)
        elif row['Z_Score'] < -2.0 and row['RSI'] < 30:
            sinais += 1
            outcome = "LOSS"
            for future_i in range(i+1, min(i+16, total)):
                if df.iloc[future_i]['high'] >= df.iloc[future_i]['EMA_20']:
                    wins += 1; outcome = "WIN"; break
            if outcome == "LOSS": losses += 1
            
    win_rate = (wins / sinais * 100) if sinais > 0 else 0
    
    return f"""
    [TRINITY ENGINE REPORT]
    - TIMEFRAME: M15 (Last {total} candles)
    - STRATEGY: Confluence (Z-Score + RSI 14)
    - HIGH QUALITY SIGNALS FOUND: {sinais}
    - WINS: {wins} | LOSSES: {losses}
    - ACCURACY (WIN RATE): {win_rate:.1f}%
    """

def tentar_ler_ativo(img, model, lista_ativos):
    prompt = "Read the Asset Name exactly. Return ONLY the name."
    try:
        response = model.generate_content([prompt, img])
        nome_raw = response.text.upper().strip().replace("INDEX", "").strip()
        for k, v in lista_ativos.items():
            k_clean = k.replace("INDEX", "").strip()
            if nome_raw in k_clean or k_clean in nome_raw:
                return k, v
        return None, None
    except: return None, None

# --- FUNÇÕES TELEGRAM ---
def enviar_telegram(token, chat_id, msg):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                     json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- INTERFACE ---
st.sidebar.header("⚙️ SI-QA TRINITY")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.divider()
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

st.sidebar.divider()
modo_operacao = st.sidebar.radio(
    "Selecionar Módulo:",
    ["Análise Trinity (Visual)", "Radar Confluência (Auto)"]
)

with st.spinner("Conectando..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE TRINITY (VISUAL)
# ==========================================================
if modo_operacao == "Análise Trinity (Visual)":
    st.title("🔥 SI-QA: Trinity Analysis")
    st.markdown("### Z-Score + RSI + Estrutura de Tendência")
    
    col1, col2, col3 = st.columns(3)
    with col1: img_m15 = st.file_uploader("1. M15 (Micro)", type=['png', 'jpg'])
    with col2: img_h1 = st.file_uploader("2. H1 (Médio)", type=['png', 'jpg'])
    with col3: img_h4 = st.file_uploader("3. H4 (Macro)", type=['png', 'jpg'])
    
    ativo_manual = st.selectbox("Seletor Manual (Caso IA falhe):", ["Automático (IA)"] + list(LISTA_ATIVOS.keys()))
    
    if st.button("RODAR PROTOCOLO TRINITY"):
        if not api_key: st.error("Falta API Key."); st.stop()
        img_p = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
        if not img_p: st.error("Envie imagens."); st.stop()
        
        status = st.status("Iniciando Motor Trinity...", expanded=True)
        genai.configure(api_key=api_key)
        
        # Tenta usar o modelo 3.0, fallback para 1.5
        try:
            model = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        except:
            model = genai.GenerativeModel("models/gemini-1.5-flash", safety_settings=SAFETY_SETTINGS)

        # 1. Identificação
        nome_ativo = None; codigo_ativo = None
        if ativo_manual != "Automático (IA)":
            nome_ativo = ativo_manual; codigo_ativo = LISTA_ATIVOS[ativo_manual]
            status.write(f"⚠️ Manual: {nome_ativo}")
        else:
            status.write("👁️ Lendo Gráfico...")
            nome_ativo, codigo_ativo = tentar_ler_ativo(Image.open(img_p), model, LISTA_ATIVOS)
            if not nome_ativo:
                st.warning("Selecione o ativo manualmente na caixa acima."); st.stop()
        
        status.write(f"✅ Ativo: {nome_ativo}")
        
        # 2. Dados
        status.write(f"📡 Baixando dados para Confluência...")
        c_m15, c_h1, c_h4, erro = asyncio.run(get_platinum_data(codigo_ativo))
        if erro: st.error(erro); st.stop()
        
        df_m15 = calcular_indicadores(pd.DataFrame(c_m15))
        df_h1 = calcular_indicadores(pd.DataFrame(c_h1))
        df_h4 = calcular_indicadores(pd.DataFrame(c_h4))
        
        # 3. Backtest Avançado
        status.write("🧮 Rodando Backtest de Confluência (RSI+ZScore)...")
        relatorio_backtest = rodar_backtest_avancado(df_m15)
        
        # 4. Injeção
        inputs = [SYSTEM_PROMPT]
        contexto = "IMAGES:\n"
        if img_m15: inputs.append(Image.open(img_m15)); contexto+="- M15\n"
        if img_h1: inputs.append(Image.open(img_h1)); contexto+="- H1\n"
        if img_h4: inputs.append(Image.open(img_h4)); contexto+="- H4\n"
        
        prompt_injecao = f"""
        TARGET: {nome_ativo}
        {contexto}
        
        === PYTHON TRINITY CHECK ===
        {relatorio_backtest}
        
        === LIVE INDICATORS ===
        [H4 MACRO]: Trend is {"BULLISH" if df_h4.iloc[-1]['close'] > df_h4.iloc[-1]['EMA_200'] else "BEARISH"}
        [M15 MICRO]: 
           - Z-Score: {df_m15.iloc[-1]['Z_Score']:.2f} (Extreme if >2 or <-2)
           - RSI (14): {df_m15.iloc[-1]['RSI']:.2f} (Overbought >70 / Oversold <30)
        
        TASK: Confirm Confluence. If Z-Score AND RSI agree, Signal is STRONG.
        """
        inputs.append(prompt_injecao)
        
        try:
            status.write("🧠 Decodificando...")
            resp = model.generate_content(inputs)
            status.update(label="Sucesso", state="complete")
            st.divider()
            st.markdown(resp.text)
            with st.expander("Ver Dados Matemáticos"): st.text(relatorio_backtest)
        except Exception as e:
            if "429" in str(e): st.warning("Cota excedida. Aguarde 30s.")
            else: st.error(f"Erro: {e}")

# ==========================================================
# MODO 2: RADAR CONFLUÊNCIA
# ==========================================================
elif modo_operacao == "Radar Confluência (Auto)":
    st.title("📡 Radar Trinity (Z-Score + RSI + Trend)")
    st.info("Este radar só avisa quando TRÊS indicadores se alinham. Menos sinais, mais precisão.")
    
    alvos = st.multiselect("Ativos:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("ATIVAR VIGILÂNCIA"):
        if not tg_token: st.error("Falta Telegram"); st.stop()
        st.success("Radar Trinity Ativo.")
        enviar_telegram(tg_token, tg_chat, "📡 RADAR TRINITY INICIADO")
        
        ph = st.empty()
        while True:
            log = []
            for nome in alvos:
                try:
                    codigo = LISTA_ATIVOS[nome]
                    c_m15, _, c_h4, _ = asyncio.run(get_platinum_data(codigo))
                    if c_m15 and c_h4:
                        df_mi = calcular_indicadores(pd.DataFrame(c_m15))
                        df_ma = calcular_indicadores(pd.DataFrame(c_h4))
                        
                        z = df_mi.iloc[-1]['Z_Score']
                        rsi = df_mi.iloc[-1]['RSI']
                        trend_up = df_ma.iloc[-1]['close'] > df_ma.iloc[-1]['EMA_200']
                        
                        msg = ""
                        # COMPRA FORTE: Trend UP + Z Barato + RSI Barato
                        if trend_up and z < -2.0 and rsi < 30:
                            msg = f"🔥 **{nome}**\nTRINITY BUY!\n- H4: Alta\n- Z-Score: {z:.2f}\n- RSI: {rsi:.0f}"
                        
                        # VENDA FORTE: Trend DOWN + Z Caro + RSI Caro
                        elif not trend_up and z > 2.0 and rsi > 70:
                            msg = f"🧊 **{nome}**\nTRINITY SELL!\n- H4: Baixa\n- Z-Score: {z:.2f}\n- RSI: {rsi:.0f}"
                            
                        if msg:
                            enviar_telegram(tg_token, tg_chat, msg)
                            log.append(f"{nome}: SINAL 🔥")
                        else:
                            log.append(f"{nome}: RSI {rsi:.0f} | Z {z:.1f}")
                except: pass
                time.sleep(1)
            ph.code("\n".join(log))
            time.sleep(60)


