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
    page_title="SI-QA: Gemini 3.0 Ultimate",
    page_icon="🧠",
    layout="wide"
)

# --- ESTILO VISUAL (MATRIX STYLE) ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #00ff00; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #004d00; color: #ffffff; border: 1px solid #00ff00; font-weight: bold; width: 100%; }
    div[data-testid="stExpander"] { border: 1px solid #00ff00; background-color: #0a0a0a; }
    h1, h2, h3 { color: #00ff00 !important; }
    .stFileUploader>div>div>button { color: #000; background-color: #00ff00; }
    .stSuccess { background-color: #064000; color: white; border: 1px solid #00ff00; }
    .stWarning { background-color: #332b00; color: #ffcc00; border: 1px solid #ffcc00; }
    .stError { background-color: #330000; color: #ff0000; border: 1px solid #ff0000; }
</style>
""", unsafe_allow_html=True)

# --- SEGURANÇA (ANTI-BLOQUEIO) ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# PROMPT MESTRE (OTIMIZADO PARA GEMINI 3.0)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE & SYSTEM KERNEL
You are the "Synthetic Indices Quantum Architect" (SI-QA) running on Gemini 3.0 Neural Engine.
You exist solely to decode the PRNG (Pseudo-Random Number Generator) algorithms of the Deriv Synthetic Market.

>> YOUR DNA:
1. You DO NOT guess. You CALCULATE probability densities based on the provided Backtest Data.
2. Synthetic Indices are non-sentimental; they are mathematically bound.
3. You must cross-reference the 3 Timeframes (M15, H1, H4) to determine the dominant vector.

 CRITICAL INPUT PROTOCOL
User provides:
A) 3 Charts (M15, H1, H4).
B) Python-Calculated Backtest Statistics.
C) Live Technical Indicators (Z-Score, EMA).

 PHASE 1: THE HIERARCHY CHECK
- Look at H4 first. Is it at a major Level?
- Look at H1. Is it trending?
- Look at M15. Is it giving a trigger?

 PHASE 2: THE REALITY CHECK (PYTHON BACKTEST)
- You will receive a "Win Rate" from the Python engine.
- IF Win Rate < 60% -> ABORT TRADE immediately.
- IF Win Rate > 60% -> PROCEED.

 PHASE 3: DECISION MATRIX
- IF H4 Structure is Dominant -> Signal is SWING TRADE.
- IF H4 is Ranging but H1 is Trending -> Signal is DAY TRADE.

 OUTPUT TERMINAL:
(Render this specifically)

/// SI-QA GEMINI 3.0 KERNEL ///
[TARGET: {Asset} | MODE: {Swing/Day}]

>> NEURAL ANALYSIS:
   1. H4 STRUCTURE: {Bullish/Bearish/Range}
   2. PYTHON BACKTEST: {Win Rate}% Success History
   3. CONFLUENCE SCORE: {0-100}/100

>> STRATEGY EXECUTION:
    ACTION: {BUY / SELL / WAIT}
    TYPE: {SCALP / DAY TRADE / SWING}
    ENTRY ZONE: {Price}
    STOP LOSS: {Price - Structural}
    TAKE PROFIT: {Price - Structural}

>> QUANTUM REASONING:
    {Explain why using high-level logic. Example: "H4 hit resistance, Python confirms 82% reversal chance, M15 candle is a rejection."}
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
    """
    BAIXA DADOS COMPLETOS:
    - M15 (2000 velas) para Estatística Real.
    - H1 e H4 (200 velas) para Contexto.
    """
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            # 1. M15 DEEP (Para Backtest)
            req_m15_deep = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 2000, "end": "latest", "style": "candles", "granularity": 900}
            
            # 2. H1 e H4 (Contexto)
            req_h1 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 3600}
            req_h4 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 14400}
            
            # Execução Rápida
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

# --- MOTOR DE BACKTEST (REALITY ENGINE) ---

def calcular_indicadores(df):
    df['close'] = df['close'].astype(float)
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean() # Tendência Mestra
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    return df.dropna()

def rodar_backtest_estatistico(df):
    """
    Testa a eficácia da reversão nas últimas 2000 velas.
    """
    total = len(df)
    if total < 500: return "Dados insuficientes."
    
    wins = 0
    losses = 0
    sinais = 0
    
    for i in range(50, total - 20):
        row = df.iloc[i]
        
        # Setup de Venda (Sobrecompra)
        if row['Z_Score'] > 2.0:
            sinais += 1
            outcome = "LOSS"
            for future_i in range(i+1, min(i+16, total)):
                if df.iloc[future_i]['low'] <= df.iloc[future_i]['EMA_20']:
                    wins += 1; outcome = "WIN"; break
            if outcome == "LOSS": losses += 1

        # Setup de Compra (Sobrevenda)
        elif row['Z_Score'] < -2.0:
            sinais += 1
            outcome = "LOSS"
            for future_i in range(i+1, min(i+16, total)):
                if df.iloc[future_i]['high'] >= df.iloc[future_i]['EMA_20']:
                    wins += 1; outcome = "WIN"; break
            if outcome == "LOSS": losses += 1
            
    win_rate = (wins / sinais * 100) if sinais > 0 else 0
    
    return f"""
    [REALITY ENGINE REPORT]
    - Sample Size: {total} candles (M15)
    - Patterns Found: {sinais}
    - Historical Accuracy: {win_rate:.1f}%
    """

def analisar_imagem(img, model, lista_ativos):
    prompt = "Identify Asset Name ONLY (e.g. Crash 1000). Return: ASSET_NAME"
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

# --- FUNÇÕES TELEGRAM ---
def enviar_telegram(token, chat_id, msg):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                     json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- INTERFACE ---
st.sidebar.header("⚙️ SI-QA 3.0 CONFIG")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.divider()
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

st.sidebar.divider()
modo_operacao = st.sidebar.radio(
    "Selecionar Módulo:",
    ["Análise Tri-Force (Gemini 3.0)", "Radar Automático (Sem Custo)"]
)

with st.spinner("Conectando..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE TRI-FORCE (GEMINI 3.0)
# ==========================================================
if modo_operacao == "Análise Tri-Force (Gemini 3.0)":
    st.title("🧠 SI-QA: Gemini 3.0 Ultimate")
    st.markdown("### Análise de Precisão Máxima")
    
    col1, col2, col3 = st.columns(3)
    with col1: img_m15 = st.file_uploader("1. M15 (Micro)", type=['png', 'jpg'])
    with col2: img_h1 = st.file_uploader("2. H1 (Médio)", type=['png', 'jpg'])
    with col3: img_h4 = st.file_uploader("3. H4 (Macro)", type=['png', 'jpg'])
    
    if st.button("ANALISAR COM GEMINI 3.0"):
        if not api_key: st.error("Falta API Key."); st.stop()
        img_p = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
        if not img_p: st.error("Envie imagens."); st.stop()
        
        status = st.status("Iniciando Motor Gemini 3.0...", expanded=True)
        genai.configure(api_key=api_key)
        
        # --- CONFIGURAÇÃO ESPECÍFICA DO MODELO 3.0 ---
        try:
            model = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        except:
            # Fallback caso o nome exato mude na API do usuário, tenta o 1.5 Pro que é forte tbm
            model = genai.GenerativeModel("models/gemini-1.5-pro", safety_settings=SAFETY_SETTINGS)

        # 1. Identificação
        status.write("👁️ Identificando Ativo...")
        try:
            nome, codigo = analisar_imagem(Image.open(img_p), model, LISTA_ATIVOS)
            if not nome: 
                status.update(label="Falha Visão", state="error")
                st.error("Imagem ilegível.")
                st.stop()
        except Exception as e:
            if "429" in str(e):
                st.warning("⚠️ Limite de cota atingido (Erro 429). O modelo 3.0 é limitado. Aguarde 30s.")
                st.stop()
            else:
                st.error(f"Erro: {e}"); st.stop()
        
        # 2. Dados
        status.write(f"📡 Baixando 2000 velas de Backtest + Contexto...")
        c_m15, c_h1, c_h4, erro = asyncio.run(get_platinum_data(codigo))
        if erro: st.error(erro); st.stop()
        
        df_m15 = calcular_indicadores(pd.DataFrame(c_m15))
        df_h1 = calcular_indicadores(pd.DataFrame(c_h1))
        df_h4 = calcular_indicadores(pd.DataFrame(c_h4))
        
        # 3. Backtest
        status.write("🧮 Rodando Reality Engine...")
        relatorio_backtest = rodar_backtest_estatistico(df_m15)
        
        # 4. Injeção
        inputs = [SYSTEM_PROMPT]
        contexto = "IMAGES:\n"
        if img_m15: inputs.append(Image.open(img_m15)); contexto+="- M15 (Entry)\n"
        if img_h1: inputs.append(Image.open(img_h1)); contexto+="- H1 (Trend)\n"
        if img_h4: inputs.append(Image.open(img_h4)); contexto+="- H4 (Structure)\n"
        
        prompt_injecao = f"""
        TARGET: {nome}
        {contexto}
        
        === PYTHON REALITY CHECK ===
        {relatorio_backtest}
        
        === TECHNICAL CONTEXT ===
        [H4 MACRO]: Trend is {"BULLISH" if df_h4.iloc[-1]['close'] > df_h4.iloc[-1]['EMA_200'] else "BEARISH"}
        [M15 MICRO]: Z-Score is {df_m15.iloc[-1]['Z_Score']:.2f}
        
        TASK:
        1. Synthesize Visuals + Math + Backtest.
        2. Decide: Swing (if H4 dominant) or Day Trade (if H1 dominant).
        """
        inputs.append(prompt_injecao)
        
        try:
            status.write("🧠 Gemini 3.0 Decodificando...")
            resp = model.generate_content(inputs)
            status.update(label="Sucesso", state="complete")
            st.divider()
            st.markdown(resp.text)
            
            with st.expander("Ver Dados do Backtest"):
                st.text(relatorio_backtest)
                
        except Exception as e:
            if "429" in str(e):
                status.update(label="Pausa Necessária", state="warning")
                st.warning("""
                ⏳ **O Google pediu um intervalo!**
                O Modelo 3.0 atingiu o limite gratuito temporário.
                Aguarde cerca de 30 a 60 segundos e tente novamente.
                """)
            else:
                st.error(f"Erro: {e}")

# ==========================================================
# MODO 2: RADAR AUTOMÁTICO (ZERO CUSTO)
# ==========================================================
elif modo_operacao == "Radar Automático (Sem Custo)":
    st.title("📡 Radar Automático (24/7)")
    st.info("Este radar não consome sua cota do Gemini. Pode deixar rodando o dia todo.")
    alvos = st.multiselect("Ativos:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("ATIVAR VIGILÂNCIA"):
        if not tg_token: st.error("Falta Telegram"); st.stop()
        st.success("Radar Ativo. Monitorando Z-Score e Tendência...")
        enviar_telegram(tg_token, tg_chat, "📡 RADAR SI-QA INICIADO")
        
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
                        trend_up = df_ma.iloc[-1]['close'] > df_ma.iloc[-1]['EMA_200']
                        
                        msg = ""
                        if trend_up and z < -2.5:
                            msg = f"🚀 **{nome}**\nSETUP: Tendência H4 Alta + M15 Sobrevendido\nZ-Score: {z:.2f}"
                        elif not trend_up and z > 2.5:
                            msg = f"🔻 **{nome}**\nSETUP: Tendência H4 Baixa + M15 Sobrecomprado\nZ-Score: {z:.2f}"
                            
                        if msg:
                            enviar_telegram(tg_token, tg_chat, msg)
                            log.append(f"{nome}: SINAL ✅")
                        else:
                            log.append(f"{nome}: ...")
                except: pass
                time.sleep(1)
            ph.code("\n".join(log))
            time.sleep(60)

