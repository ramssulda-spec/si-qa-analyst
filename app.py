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
    page_title="SI-APATECO PRO",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL (NEXT-GEN UI / CSS AVANÇADO) ---
st.markdown("""
<style>
    /* Importando Fonte Futurista */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@300;400;700&display=swap');

    /* Animação de Entrada */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Fundo Global */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 0%, #1a2e1a 0%, #050505 60%);
        font-family: 'Roboto', sans-serif;
    }

    /* Títulos Principais */
    h1 {
        font-family: 'Orbitron', sans-serif !important;
        background: linear-gradient(90deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        font-weight: 700 !important;
    }
    
    h2, h3 {
        color: #e0e0e0 !important;
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1px;
    }

    /* Cards e Containers (Glassmorphism) */
    div[data-testid="stExpander"], div.stFileUploader {
        background: rgba(20, 20, 25, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease;
        animation: fadeIn 0.6s ease-out;
    }
    
    div[data-testid="stExpander"]:hover {
        border-color: rgba(0, 255, 136, 0.3);
    }

    /* BOTÃO DE AÇÃO (MODERNO E ANIMADO) */
    .stButton>button {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        color: #000;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 16px 32px;
        font-size: 16px;
        text-transform: uppercase;
        letter-spacing: 2px;
        width: 100%;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.2);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        position: relative;
        overflow: hidden;
    }

    .stButton>button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 255, 136, 0.5);
        background: linear-gradient(135deg, #00d4bb, #aee04d);
    }

    .stButton>button:active {
        transform: translateY(1px) scale(0.98);
        box-shadow: 0 2px 10px rgba(0, 255, 136, 0.3);
    }

    /* Inputs e Selects */
    .stSelectbox>div>div>div, .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
    }

    /* Sidebar Customizada */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Status Messages */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 8px;
        backdrop-filter: blur(5px);
        font-weight: 500;
        animation: fadeIn 0.4s ease-out;
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
# PROMPT MESTRE (TITAN PROTOCOLS)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE & SYSTEM KERNEL
You are the "SI-QA TITAN", an Institutional Algorithm designed for the Deriv Synthetic Markets.
You operate on a "Hierarchy of Truth":
1. MATH (Python Data & Backtest) is the absolute truth.
2. MACRO STRUCTURE (H4 Chart) is the map.
3. MICRO TRIGGER (M15 Chart) is the timing.

>> DYNAMIC ASSET PROTOCOLS (YOU MUST OBEY THE DETECTED CLASS):

<PROTOCOL_A: SPIKE_INDICES>
(Target: Crash 300/500/1000 & Boom 300/500/1000)
- PHYSICS: Asymmetric volatility. Drops/Spikes happen in 1 tick.
- RULE 1: NEVER trust "Overbought/Oversold" oscillators blindly. A Crash index can stay "Oversold" for 50 candles while trending down.
- RULE 2: Trend Following (H4) is the only safe path.
- TRIGGER: Look for "N" Patterns (Spike -> Small Retracement -> Spike) or Key Support levels on H4.

<PROTOCOL_B: DISCRETE_INDICES>
(Target: Step Index, Jump Indices)
- PHYSICS: Price moves in rigid blocks/steps. EMAs are less effective here.
- FOCUS: Horizontal Levels (Support/Resistance) and Breakouts.
- TRIGGER: Wait for a candle to BREAK and CLOSE outside a consolidation box.

<PROTOCOL_C: FLUID_INDICES>
(Target: Volatility 10/25/50/75/100, Range Break)
- PHYSICS: Standard Brownian Motion. Technical Analysis works perfectly here.
- TRIGGER: Z-Score deviation + RSI Divergence is the strongest signal.

 CRITICAL INPUT PROTOCOL
User provides:
A) 3 Charts (M15, H1, H4).
B) ASSET CLASS (Detected by Python).
C) BACKTEST DATA (Win Rate of the strategy).

 OUTPUT TERMINAL (Strict Format):

/// SI-APATECO ANALYSIS ///
[ASSET: {Asset} | PROTOCOL: {Protocol A/B/C}]

>> HIERARCHY CHECK:
   1. MACRO (H4): {Describe Structure}
   2. BACKTEST REALITY: {Win Rate}% (Is this safe?)
   3. MICRO (M15): {Describe pattern}

>> VERDICT MATRIX:
   - TREND ALIGNMENT: {Strong/Weak/Against}
   - STATISTICAL EDGE: {High/Medium/Low}

>> EXECUTION ORDER:
    ACTION: {BUY / SELL / WAIT}
    TYPE: {SCALP / SWING / DAY}
    ENTRY ZONE: {Price Area}
    SL: {Invalidation Price}
    TP: {Target Price}

>> INSTITUTIONAL NOTE:
    {Why? "Backtest confirms 70% edge + H4 Support."}
)
"""

# --- FUNÇÕES API COM TIMEOUT ---

@st.cache_data(ttl=3600)
def buscar_lista_ativos_deriv():
    async def _fetch():
        uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
        try:
            async with websockets.connect(uri) as ws:
                req = {"active_symbols": "brief", "product_type": "basic"}
                await ws.send(json.dumps(req))
                res = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(res)
                if 'error' in data: return None
                ativos_dict = {}
                for item in data['active_symbols']:
                    if item['market'] == 'synthetic_index':
                        ativos_dict[item['display_name'].upper()] = item['symbol']
                return ativos_dict
        except: return None
    return asyncio.run(_fetch())

async def get_raw_data(symbol_code):
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            # Baixa 2000 velas de M15 para o Backtest Robusto
            req_m15 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 2000, "end": "latest", "style": "candles", "granularity": 900}
            req_h4 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 14400}
            
            await websocket.send(json.dumps(req_m15))
            res_m15 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            
            await websocket.send(json.dumps(req_h4))
            res_h4 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            
            d_m15 = json.loads(res_m15)
            d_h4 = json.loads(res_h4)
            
            if 'error' in d_m15 or 'error' in d_h4: return None, None, "Erro API Deriv (Dados inválidos)"
            return d_m15['candles'], d_h4['candles'], None
            
    except asyncio.TimeoutError:
        return None, None, "Erro: Deriv demorou muito para responder (Timeout)."
    except Exception as e: 
        return None, None, str(e)

# --- NÚCLEOS MATEMÁTICOS ADAPTATIVOS ---

def math_common(df):
    df['close'] = df['close'].astype(float)
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean() # Usado no Backtest
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    return df

def math_volatility_step(df):
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    
    delta = df['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def math_boom_crash(df, tipo):
    df['body_size'] = df['close'] - df['open']
    threshold = df['body_size'].std() * 2
    if "CRASH" in tipo: df['is_spike'] = df['body_size'] < -threshold
    else: df['is_spike'] = df['body_size'] > threshold
    return df

# --- MOTOR DE BACKTEST (REALITY ENGINE) ---

def rodar_backtest(df, classe_ativo):
    total = len(df)
    if total < 500: return "Dados insuficientes para Backtest."
    wins = 0; losses = 0; sinais = 0
    for i in range(50, total - 20):
        row = df.iloc[i]
        if "PROTOCOL B" in classe_ativo or "PROTOCOL C" in classe_ativo:
            if 'Z_Score' in row and row['Z_Score'] > 2.0:
                sinais += 1; outcome = "LOSS"
                for future_i in range(i+1, min(i+16, total)):
                    if df.iloc[future_i]['low'] <= df.iloc[future_i]['EMA_20']:
                        wins += 1; outcome = "WIN"; break
                if outcome == "LOSS": losses += 1
            elif 'Z_Score' in row and row['Z_Score'] < -2.0:
                sinais += 1; outcome = "LOSS"
                for future_i in range(i+1, min(i+16, total)):
                    if df.iloc[future_i]['high'] >= df.iloc[future_i]['EMA_20']:
                        wins += 1; outcome = "WIN"; break
                if outcome == "LOSS": losses += 1
        elif "PROTOCOL A" in classe_ativo:
            trend_up = row['close'] > row['EMA_200']
            pullback = abs(row['close'] - row['EMA_20']) < (row['close'] * 0.001)
            if trend_up and pullback:
                sinais += 1; outcome = "LOSS"
                if df.iloc[min(i+5, total-1)]['close'] > row['close']:
                    wins += 1; outcome = "WIN" 
                else: losses += 1
    win_rate = (wins / sinais * 100) if sinais > 0 else 0
    return f"""
    [REALITY ENGINE REPORT]
    - Strategy Tested: {'Mean Reversion' if 'PROTOCOL A' not in classe_ativo else 'Trend Following'}
    - Sample: {total} candles
    - Signals Found: {sinais}
    - Historical Win Rate: {win_rate:.1f}%
    """

def processar_dados_inteligentes(nome_ativo, df_m15):
    df_m15 = math_common(df_m15)
    info_extra = ""
    classe = ""
    if "CRASH" in nome_ativo or "BOOM" in nome_ativo:
        classe = "PROTOCOL A: SPIKE INDICES"
        df_final = math_boom_crash(df_m15, nome_ativo)
        total_spikes = df_final['is_spike'].sum()
        trend = "BEARISH" if df_final.iloc[-1]['close'] < df_final.iloc[-1]['EMA_200'] else "BULLISH"
        info_extra = f"[SPIKE DATA]\nTrend: {trend}\nSpikes (Last 1000): {total_spikes}"
    elif "STEP" in nome_ativo or "JUMP" in nome_ativo:
        classe = "PROTOCOL B: DISCRETE INDICES"
        df_final = math_volatility_step(df_m15)
        df_final['tr'] = np.maximum((df_final['high'] - df_final['low']), abs(df_final['high'] - df_final['close'].shift()))
        atr = df_final['tr'].rolling(14).mean().iloc[-1]
        info_extra = f"[DISCRETE DATA]\nATR: {atr:.4f}\nRSI: {df_final.iloc[-1]['RSI']:.2f}"
    else: 
        classe = "PROTOCOL C: FLUID INDICES"
        df_final = math_volatility_step(df_m15)
        info_extra = f"[MEAN REVERSION DATA]\nZ-Score: {df_final.iloc[-1]['Z_Score']:.2f}\nRSI: {df_final.iloc[-1]['RSI']:.2f}"
    relatorio_backtest = rodar_backtest(df_final, classe)
    return info_extra, classe, relatorio_backtest

def tentar_ler_ativo(img, model, lista_ativos):
    prompt = "Read the Asset Name exactly from the chart header (e.g., Crash 1000 Index). Return ONLY the name."
    try:
        response = model.generate_content([prompt, img])
        nome_raw = response.text.upper().strip().replace("INDEX", "").strip()
        for k, v in lista_ativos.items():
            k_clean = k.replace("INDEX", "").strip()
            if nome_raw in k_clean or k_clean in nome_raw: return k, v
        return None, None
    except: return None, None

def enviar_telegram(token, chat_id, msg):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                     json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

# --- INTERFACE PRINCIPAL (VISUAL SI-APATECO) ---
st.sidebar.markdown("## ⚙️ Configuração")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password")

st.sidebar.divider()
st.sidebar.markdown("## 📡 Telegram")
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

st.sidebar.divider()
st.sidebar.markdown("## 🚀 Módulo")
modo_operacao = st.sidebar.radio(
    "Escolha o modo:",
    ["Análise Visual (SI-APATECO)", "Radar Auto (Telegram)"]
)

with st.spinner("🔄 Conectando aos servidores Deriv..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE VISUAL SI-APATECO
# ==========================================================
if modo_operacao == "Análise Visual (SI-APATECO)":
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>💠 SI-APATECO</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("### 📤 Upload dos Gráficos (Tri-Force)")
        col1, col2, col3 = st.columns(3)
        with col1: img_m15 = st.file_uploader("📸 1. M15 (Gatilho)", type=['png', 'jpg'])
        with col2: img_h1 = st.file_uploader("📸 2. H1 (Tendência)", type=['png', 'jpg'])
        with col3: img_h4 = st.file_uploader("📸 3. H4 (Macro)", type=['png', 'jpg'])
    
    st.divider()
    
    col_sel, col_btn = st.columns([2, 1])
    with col_sel:
        ativo_manual = st.selectbox("🛡️ Seletor de Segurança (Caso IA falhe):", ["Automático (IA)"] + list(LISTA_ATIVOS.keys()))
    
    with col_btn:
        st.write("") # Espaçamento
        st.write("") 
        start_btn = st.button("🚀 INICIAR ANÁLISE")
    
    if start_btn:
        if not api_key: st.error("⚠️ Falta API Key."); st.stop()
        img_p = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
        if not img_p: st.error("⚠️ Envie pelo menos uma imagem."); st.stop()
        
        status = st.status("🧠 Inicializando Neural Engine (G3)...", expanded=True)
        genai.configure(api_key=api_key)
        
        # 1. Identificação - USANDO GEMINI 3 FLASH PARA VISÃO
        nome_ativo = None; codigo_ativo = None
        if ativo_manual != "Automático (IA)":
            nome_ativo = ativo_manual; codigo_ativo = LISTA_ATIVOS[ativo_manual]
            status.write(f"🛡️ Modo Manual Ativado: **{nome_ativo}**")
        else:
            # AQUI ESTÁ A MUDANÇA: Usando 3-flash-preview para visão
            try: model_vision = genai.GenerativeModel("models/gemini-3-flash-preview")
            except: model_vision = genai.GenerativeModel("models/gemini-3-flash-preview")
            
            status.write("👁️ Vision AI (G3) lendo gráfico...")
            try:
                nome_ativo, codigo_ativo = tentar_ler_ativo(Image.open(img_p), model_vision, LISTA_ATIVOS)
            except Exception: pass
            
            if not nome_ativo: status.update(label="Erro de Leitura", state="warning"); st.warning("⚠️ IA não leu o nome. Use o seletor manual acima."); st.stop()
        
        status.write(f"✅ Ativo Confirmado: **{nome_ativo}**")
        
        # 2. Dados
        status.write("📡 Baixando dados institucionais (Deriv API)...")
        c_m15, c_h4, erro = asyncio.run(get_raw_data(codigo_ativo))
        if erro: 
            status.update(label="Erro Conexão", state="error")
            st.error(f"❌ Erro de Rede: {erro}"); st.stop()
        
        # 3. Processamento
        status.write("🧮 Executando 'Reality Engine' (Backtest)...")
        df_m15 = pd.DataFrame(c_m15)
        relatorio_math, classe_ativo, relatorio_backtest = processar_dados_inteligentes(nome_ativo, df_m15)
        
        status.write(f"🧬 Protocolo Detectado: **{classe_ativo}**")
        
        # 4. Prompt Gemini - USANDO APENAS GEMINI 3
        try: model_logic = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
        except: model_logic = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        
        inputs = [SYSTEM_PROMPT]
        contexto = "CHARTS PROVIDED:\n"
        if img_m15: inputs.append(Image.open(img_m15)); contexto+="- M15\n"
        if img_h1: inputs.append(Image.open(img_h1)); contexto+="- H1\n"
        if img_h4: inputs.append(Image.open(img_h4)); contexto+="- H4\n"
        
        prompt_injecao = f"""
        TARGET: {nome_ativo}
        DETECTED CLASS: {classe_ativo}
        {contexto}
        
        === ADAPTIVE MATH DATA ===
        {relatorio_math}
        
        === BACKTEST REALITY CHECK ===
        {relatorio_backtest}
        
        TASK: Execute analysis using ONLY the rules for {classe_ativo}.
        """
        inputs.append(prompt_injecao)
        
        try:
            status.write("🤖 Gerando Veredito Final (Gemini 3.0)...")
            resp = model_logic.generate_content(inputs)
            status.update(label="Análise Concluída", state="complete")
            
            st.divider()
            st.markdown(resp.text)
            
            with st.expander("📊 Ver Dados Matemáticos (Raio-X)"):
                st.code(relatorio_backtest, language="text")
                st.code(relatorio_math, language="text")
                
        except Exception as e:
            if "429" in str(e): st.warning("⚠️ Limite de cota Gemini atingido. Aguarde 30s."); status.update(label="Pausa", state="warning")
            else: st.error(f"❌ Erro IA: {e}")

# ==========================================================
# MODO 2: RADAR AUTOMÁTICO
# ==========================================================
elif modo_operacao == "Radar Auto (Telegram)":
    st.markdown("<h1 style='text-align: center;'>📡 Radar Adaptativo (24/7)</h1>", unsafe_allow_html=True)
    st.info("Este módulo monitora o mercado em tempo real e envia alertas no Telegram.")
    
    alvos = st.multiselect("🎯 Selecione os ativos para monitorar:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("🟢 ATIVAR VIGILÂNCIA"):
        if not tg_token: st.error("Falta Telegram Token."); st.stop()
        st.success("Radar Ativo! Pode minimizar esta aba.")
        enviar_telegram(tg_token, tg_chat, "📡 RADAR TITAN INICIADO")
        
        ph = st.empty()
        log_container = []
        
        while True:
            for nome in alvos:
                try:
                    codigo = LISTA_ATIVOS[nome]
                    c_m15, c_h4, _ = asyncio.run(get_raw_data(codigo))
                    
                    if c_m15:
                        df_m15 = pd.DataFrame(c_m15)
                        math_report, classe, _ = processar_dados_inteligentes(nome, df_m15)
                        
                        msg = ""
                        if "SPIKE" in classe:
                            if "Trend: BULLISH" in math_report and "BOOM" in nome:
                                msg = f"🚀 **{nome}**\nProtocolo A: Tendência de Alta (Boom)"
                            elif "Trend: BEARISH" in math_report and "CRASH" in nome:
                                msg = f"🔻 **{nome}**\nProtocolo A: Tendência de Baixa (Crash)"
                        elif "Z-Score" in math_report: 
                            if "Extreme" in math_report:
                                msg = f"⚡ **{nome}**\nProtocolo C: Z-Score Extremo"
                        
                        timestamp = time.strftime("%H:%M:%S")
                        if msg:
                            enviar_telegram(tg_token, tg_chat, msg)
                            log_container.insert(0, f"[{timestamp}] {nome}: 🚨 ALERTA ENVIADO")
                        else:
                            log_container.insert(0, f"[{timestamp}] {nome}: Monitorando...")
                            
                except: pass
                time.sleep(1) # Delay anti-spam
            
            # Mantém apenas as últimas 10 linhas de log
            if len(log_container) > 10: log_container = log_container[:10]
            ph.code("\n".join(log_container))
            time.sleep(30)







