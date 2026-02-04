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
import matplotlib.pyplot as plt
import io

# ==============================================================================
# 1. VISUAL SETUP (SNIPER TRI-VISION V14.0)
# ==============================================================================
st.set_page_config(
    page_title="SI-APATECO SNIPER V14.0",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url(\'https://fonts.googleapis.com/css2?family=Teko:wght@300;600&family=Share+Tech+Mono&display=swap\');
    
    .stApp {
        background-color: #050505;
        background-image: linear-gradient(0deg, #000 0%, #0a0a0a 100%);
        color: #d4d4d4;
        font-family: \'Share Tech Mono\', monospace;
    }
    
    h1, h2, h3 {
        font-family: \'Teko\', sans-serif !important;
        text-transform: uppercase;
        color: #fbbf24; /* Amber-400 */
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(251, 191, 36, 0.3);
    }
    
    /* Upload Boxes Style */
    .stFileUploader {
        border: 1px dashed #fbbf24;
        border-radius: 5px;
        padding: 10px;
        background: rgba(251, 191, 36, 0.05);
    }
    
    div[data-testid="stMetric"] {
        background-color: #111;
        border-right: 4px solid #fbbf24;
        padding: 15px;
    }
    
    .stButton>button {
        background: linear-gradient(45deg, #d97706, #fbbf24);
        color: black;
        font-weight: 900;
        text-transform: uppercase;
        padding: 20px;
        font-size: 20px;
        border-radius: 0px;
        width: 100%;
        border: 1px solid #fbbf24;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 30px rgba(251, 191, 36, 0.6);
        transform: scale(1.02);
    }
    
    .dataframe {
        border: 1px solid #333;
        font-family: \'Share Tech Mono\', monospace;
    }
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
# 2. PROMPT DE CORRELAÇÃO VISUAL (H4 -> H1 -> M15) - OTIMIZADO
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE: HIGH PAYOFF TRADE ANALYST (V14.0) [Gemini 3 Pro]
Your Goal: Identify Multi-Timeframe Confluence for Swings (Targets 1:3 to 1:5).
Você ignora scalps. Você está procurando reversões estruturais ou pullbacks profundos alinhados com a Tendência.

**INPUT DATA:**
1. **Math Core:** Determina a Direção da Tendência, Força da Tendência (ADX) e Parâmetros de Risco.
2. **Visual Triad (M15, H1, H4):** Usado para confirmar o timing de entrada e a estrutura de mercado.

**ANALYSIS PROTOCOL (ALINHAMENTO FRACTAL):**
1. **Olhe para a Imagem H4:** Onde está a principal Oferta/Demanda? Estamos em uma Tendência de Alta ou Baixa? A tendência é forte (ADX > 20)?
2. **Olhe para a Imagem H1:** A estrutura interna está alinhada com o H4? Existem níveis de suporte/resistência claros? O preço está numa zona de valor (perto da EMA 50)?
3. **Olhe para a Imagem M15:** Você vê um gatilho de entrada (Rejeição de Pavio, Engolfo, Pin Bar) no Nível de ENTRADA calculado pelo MATH CORE? O volume está a confirmar?

**OUTPUT FORMAT:**

## 🔭 SNIPER VERDICT: [ {FINAL_DECISION} ]
**Ativo:** {ASSET_NAME} | **Payoff Ratio:** 1:5 (Targeting {MATH_TP5})

### 👁️ ANÁLISE VISUAL TRI-FORCE
*   **H4 (Macro):** {Análise do gráfico H4 - Tendência, Força da Tendência (ADX), Zonas de Oferta/Demanda}
*   **H1 (Estrutura):** {Análise do gráfico H1 - Pontos de Pivô, Níveis de Suporte/Resistência, Zona de Valor}
*   **M15 (Gatilho):** {Análise do gráfico M15 - Ação do Preço, Padrões de Candlestick, Volume}

### 🎯 PLANO DE EXECUÇÃO
| Ordem | Nível | Notas |
| :--- | :--- | :--- |
| **ENTRADA** | **{MATH_ENTRY}** | *{ENTRY_TYPE}* |
| **STOP** | **{MATH_SL}** | *{SL_REASON}* |
| **TP 1** | **{MATH_TP3}** | *Banco 50% aqui (1:3)* |
| **TP 2** | **{MATH_TP5}** | *Deixe correr (1:5 com Trailing Stop)* |

*Sniper Insight:* {Por que o alinhamento fractal permite um rácio Risco:Recompensa tão alto aqui? Qual é a sua confiança nesta operação?}
)
"""

# ==============================================================================
# 3. REDE DERIV ROBUSTA - OTIMIZADA
# ==============================================================================
DERIV_SERVERS = [
    "wss://ws.binaryws.com/websockets/v3?app_id=1089",      
    "wss://ws.derivws.com/websockets/v3?app_id=1089",       
    "wss://green.binaryws.com/websockets/v3?app_id=1089"
]

async def socket_req(url, req):
    try:
        async with websockets.connect(url, ping_interval=20, close_timeout=15) as ws:
            await ws.send(json.dumps(req))
            response = await asyncio.wait_for(ws.recv(), timeout=15.0)
            return json.loads(response)
    except asyncio.TimeoutError:
        st.error(f"Timeout ao comunicar com {url}")
        return None
    except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidURI) as e:
        st.error(f"Erro de conexão WebSocket com {url}: {e}")
        return None
    except json.JSONDecodeError:
        st.error(f"Erro ao descodificar a resposta JSON de {url}.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado com {url}: {e}")
        return None

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
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 300, "end": "latest"},  # H1
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 200, "end": "latest"}, # H4
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 1000, "end": "latest"}   # M15
    ]
    
    data_h1, data_h4, data_m15 = None, None, None
    
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=20, close_timeout=15) as ws:
                # Fetch H1
                await ws.send(json.dumps(reqs[0]))
                raw_h1 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                if 'candles' in raw_h1: data_h1 = raw_h1['candles']
                
                # Fetch H4
                await ws.send(json.dumps(reqs[1]))
                raw_h4 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                if 'candles' in raw_h4: data_h4 = raw_h4['candles']
                
                # Fetch M15
                await ws.send(json.dumps(reqs[2]))
                raw_m15 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                if 'candles' in raw_m15: data_m15 = raw_m15['candles']
                
                if data_h1 and data_h4 and data_m15: 
                    return data_h1, data_h4, data_m15, None
                
        except asyncio.TimeoutError:
            st.warning(f"Timeout ao buscar dados de {url}. Tentando o próximo servidor...")
            continue
        except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidURI) as e:
            st.warning(f"Erro de conexão WebSocket com {url}: {e}. Tentando o próximo servidor...")
            continue
        except json.JSONDecodeError:
            st.warning(f"Erro ao descodificar a resposta JSON de {url}. Tentando o próximo servidor...")
            continue
        except Exception as e:
            st.warning(f"Ocorreu um erro inesperado com {url}: {e}. Tentando o próximo servidor...")
            continue
            
    return None, None, None, "CONNECTION LOST: Não foi possível obter dados de nenhum servidor."

# ==============================================================================
# 4. SWING MATH CORE (V14.0) - OTIMIZADO
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']: df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

def calculate_adx(df, window=14):
    # Calculate True Range (TR)
    df['trh'] = df['high'] - df['low']
    df['trc'] = abs(df['high'] - df['close'].shift())
    df['trl'] = abs(df['low'] - df['close'].shift())
    df['TR'] = df[['trh', 'trc', 'trl']].max(axis=1)
    
    # Calculate Directional Movement (DM)
    df['+DM'] = np.where((df['high'] > df['high'].shift()) & (df['low'] <= df['low'].shift()), 
                         df['high'] - df['high'].shift(), 0)
    df['-DM'] = np.where((df['low'] < df['low'].shift()) & (df['high'] >= df['high'].shift()), 
                         df['low'].shift() - df['low'], 0)
    
    df['+DM'] = np.where(df['+DM'] > df['-DM'], df['+DM'], 0)
    df['-DM'] = np.where(df['-DM'] > df['+DM'], df['-DM'], 0)
    
    # Calculate Smoothed TR, +DM, -DM
    df['TR_EMA'] = df['TR'].ewm(span=window, adjust=False).mean()
    df['+DM_EMA'] = df['+DM'].ewm(span=window, adjust=False).mean()
    df['-DM_EMA'] = df['-DM'].ewm(span=window, adjust=False).mean()
    
    # Calculate DI
    df['+DI'] = (df['+DM_EMA'] / df['TR_EMA']) * 100
    df['-DI'] = (df['-DM_EMA'] / df['TR_EMA']) * 100
    
    # Calculate DX
    df['DX'] = (abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])) * 100
    
    # Calculate ADX
    df['ADX'] = df['DX'].ewm(span=window, adjust=False).mean()
    
    df.drop(columns=['trh', 'trc', 'trl', 'TR', '+DM', '-DM', 'TR_EMA', '+DM_EMA', '-DM_EMA', '+DI', '-DI', 'DX'], inplace=True)
    return df

def indicators(df):
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean() 
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean() # Value Zone
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean() # Trend Filter

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(span=14, adjust=False).mean()
    avg_loss = loss.ewm(span=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['tr'] = df[['high','low','close']].apply(lambda x: max(x['high']-x['low'], abs(x['high']-x['close']), abs(x['low']-x['close'].shift())), axis=1)
    df['ATR'] = df['tr'].ewm(span=14, adjust=False).mean()
    
    df = calculate_adx(df)
    
    df.dropna(inplace=True)
    return df

def detect_swing_level(df, direction, atr_multiplier=1.5):
    """Encontra Swing Low/High real no H1 para SL protegido com buffer ATR"""
    if direction == "BUY":
        # Encontra o swing low mais recente que não foi quebrado
        swing_lows = df[df['low'] == df['low'].rolling(window=5, center=True).min()]['low']
        if not swing_lows.empty:
            # Pega o último swing low válido e adiciona um buffer ATR
            last_swing_low = swing_lows.iloc[-1]
            return last_swing_low - (df['ATR'].iloc[-1] * atr_multiplier)
        return df['low'].tail(20).min() - (df['ATR'].iloc[-1] * atr_multiplier) # Fallback
    elif direction == "SELL":
        # Encontra o swing high mais recente que não foi quebrado
        swing_highs = df[df['high'] == df['high'].rolling(window=5, center=True).max()]['high']
        if not swing_highs.empty:
            # Pega o último swing high válido e adiciona um buffer ATR
            last_swing_high = swing_highs.iloc[-1]
            return last_swing_high + (df['ATR'].iloc[-1] * atr_multiplier)
        return df['high'].tail(20).max() + (df['ATR'].iloc[-1] * atr_multiplier) # Fallback
    return df.iloc[-1]['close']

# ==============================================================================
# 5. PROFITABILITY BACKTEST (FOCADO EM R:R 1:5) - OTIMIZADO
# ==============================================================================

def run_payoff_sim(df, trend_dir):
    """
    Backtest: Só aprova o ativo se ele tiver costume de pagar trades 1:5 a favor da tendência.
    Inclui métricas adicionais e trailing stop.
    """
    trades = 0
    hits_5R = 0
    balance = 0.0
    max_balance = 0.0
    min_balance = 0.0
    drawdown = 0.0
    total_wins = 0
    total_losses = 0
    
    # Ajustar o range para garantir dados suficientes para indicadores
    start_idx = max(200, df.first_valid_index().row if isinstance(df.first_valid_index(), pd.Timestamp) else df.first_valid_index())
    
    for i in range(start_idx, len(df) - 80):
        row = df.iloc[i]

        # Lógica: Pullback Profundo (Preço volta na Média ou RSI Extremo) + Trend + ADX
        sig = None
        is_adx_strong = row['ADX'] > 20 # ADX para força da tendência

        if trend_dir == "BULLISH" and is_adx_strong:
            # Preço está "Barato" (Desconto) se tocar EMA50 ou RSI < 45
            if row['close'] > row['EMA_200'] and (row['low'] <= row['EMA_50'] or row['RSI'] < 45):
                sig = "BUY"
        elif trend_dir == "BEARISH" and is_adx_strong:
            # Preço está "Caro" (Prêmio) se tocar EMA50 ou RSI > 55
            if row['close'] < row['EMA_200'] and (row['high'] >= row['EMA_50'] or row['RSI'] > 55):
                sig = "SELL"

        if sig:
            entry = row['close']
            atr = row['ATR']
            
            # SL baseado em estrutura com buffer ATR, limitado a 3x ATR
            sl_candidate = detect_swing_level(df.iloc[:i+1], sig)
            if sig == "BUY":
                sl = max(entry - (3 * atr), sl_candidate) # Garante que SL não é muito longe
            else:
                sl = min(entry + (3 * atr), sl_candidate) # Garante que SL não é muito longe
            
            risk_per_trade = abs(entry - sl)
            if risk_per_trade == 0: risk_per_trade = atr # Evitar divisão por zero

            tp_3R = entry + (3 * risk_per_trade) if sig == "BUY" else entry - (3 * risk_per_trade)
            tp_5R = entry + (5 * risk_per_trade) if sig == "BUY" else entry - (5 * risk_per_trade)

            res = "OPEN"
            current_tp2 = tp_5R # Para trailing stop
            
            for f in range(i + 1, min(i + 80, len(df))): # Deixa correr bastante
                nx = df.iloc[f]
                
                if sig == "BUY":
                    if nx['low'] <= sl: res = "LOSS"; break
                    if nx['high'] >= tp_3R: # Atingiu TP1, move SL para BE e ativa trailing para TP2
                        sl = entry # Move SL para Break-Even
                        # Trailing Stop: Mantém o TP2 a uma distância de 2 ATR do high mais alto
                        current_tp2 = max(current_tp2, nx['high'] - (2 * atr)) 
                    if nx['high'] >= current_tp2: res = "WIN"; break
                else:
                    if nx['high'] >= sl: res = "LOSS"; break
                    if nx['low'] <= tp_3R: # Atingiu TP1, move SL para BE e ativa trailing para TP2
                        sl = entry # Move SL para Break-Even
                        # Trailing Stop: Mantém o TP2 a uma distância de 2 ATR do low mais baixo
                        current_tp2 = min(current_tp2, nx['low'] + (2 * atr))
                    if nx['low'] <= current_tp2: res = "WIN"; break

            if res != "OPEN":
                trades += 1
                if res == "WIN": 
                    hits_5R += 1
                    balance += 5.0 # Assume 5R de ganho
                    total_wins += 1
                else: 
                    balance -= 1.0 # Assume 1R de perda
                    total_losses += 1
                
                max_balance = max(max_balance, balance)
                drawdown = max(drawdown, max_balance - balance)
                
                i = f + 10 # Pula para não repetir trade na mesma congestão

    wr = (hits_5R / trades * 100) if trades > 0 else 0
    profit_factor = (total_wins * 5.0) / (total_losses * 1.0) if total_losses > 0 else (5.0 if total_wins > 0 else 0.0)
    
    return {"WR": round(wr, 1), "NET": round(balance, 1), "DD": round(drawdown, 1), "PF": round(profit_factor, 2)}

# ==============================================================================
# 6. SNIPER PROCESSOR - OTIMIZADO
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp3=None, tp5=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Candlesticks
    for i in range(len(df)):
        color = 'green' if df['open'].iloc[i] < df['close'].iloc[i] else 'red'
        ax.plot([df.index[i], df.index[i]], [df['low'].iloc[i], df['high'].iloc[i]], color=color)
        ax.plot([df.index[i], df.index[i]], [df['open'].iloc[i], df['close'].iloc[i]], color=color, linewidth=4)

    # EMAs
    ax.plot(df.index, df['EMA_20'], label='EMA 20', color='blue', linestyle='--')
    ax.plot(df.index, df['EMA_50'], label='EMA 50', color='orange', linestyle='--')
    ax.plot(df.index, df['EMA_200'], label='EMA 200', color='purple', linestyle='--')

    # Entry, SL, TP
    if entry: ax.axhline(y=entry, color='cyan', linestyle='-', label='Entry')
    if sl: ax.axhline(y=sl, color='red', linestyle='-', label='Stop Loss')
    if tp3: ax.axhline(y=tp3, color='lime', linestyle='--', label='TP 1 (1:3)')
    if tp5: ax.axhline(y=tp5, color='green', linestyle='-', label='TP 2 (1:5)')

    ax.set_title(title)
    ax.legend()
    ax.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

def sniper_core(name, h1_raw, h4_raw, m15_raw):
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = indicators(prep_df(m15_raw))
    
    curr_h1 = h1.iloc[-1]
    curr_h4 = h4.iloc[-1]
    curr_m15 = m15.iloc[-1]

    # 1. Bias H4 (Mandatory) - Com ADX para força da tendência
    bias_h4 = "BULLISH" if curr_h4['close'] > curr_h4['EMA_200'] else "BEARISH"
    adx_h4_strong = curr_h4['ADX'] > 20
    
    sl_reason = "Structural Pivot"

    # 2. Setup (Deep Value Check) - Refinado
    sig = "MONITORING"
    entry = curr_h1['close']
    sl = curr_h1['close']
    entry_type = "Wait"

    if bias_h4 == "BULLISH" and adx_h4_strong:
        # Preço está "Barato" (Desconto) se tocar EMA50 ou RSI < 45
        dist = abs(curr_h1['close'] - curr_h1['EMA_50'])
        is_value = dist < (curr_h1['ATR'] * 1.2) # Dentro de 1.2 ATR da EMA50
        if is_value or curr_h1['RSI'] < 45:
            sig = "LONG (SWING)"
            sl = detect_swing_level(h1, "BUY", atr_multiplier=1.5) # SL com buffer ATR
            entry_type = "Trend Defense (Discount)"
            # Safety: Limit Max SL distance to 3 ATR
            if (entry - sl) > (3 * curr_h1['ATR']): 
                sl = entry - (2.5 * curr_h1['ATR'])
                sl_reason = "Max ATR Limit"

    elif bias_h4 == "BEARISH" and adx_h4_strong:
        dist = abs(curr_h1['close'] - curr_h1['EMA_50'])
        is_value = dist < (curr_h1['ATR'] * 1.2)
        if is_value or curr_h1['RSI'] > 55:
            sig = "SHORT (SWING)"
            sl = detect_swing_level(h1, "SELL", atr_multiplier=1.5) # SL com buffer ATR
            entry_type = "Trend Defense (Premium)"
            if (sl - entry) > (3 * curr_h1['ATR']): 
                sl = entry + (2.5 * curr_h1['ATR'])
                sl_reason = "Max ATR Limit"

    # 3. Probability Check - Backtest Aprimorado
    sim = run_payoff_sim(h1, bias_h4)
    if sim['NET'] <= 0 or sim['PF'] < 1.5: # Adiciona Profit Factor como filtro
        sig = "BLOCKED (STATISTICS)" # Negative historical edge ou PF baixo

    # Targets Calculation (Hardfixed 1:3 & 1:5)
    risk = abs(entry - sl)
    if risk == 0: risk = curr_h1['ATR'] # Evitar divisão por zero

    if "LONG" in sig or "BUY" in sig:
        tp3 = entry + (3 * risk)
        tp5 = entry + (5 * risk)
    else:
        tp3 = entry - (3 * risk)
        tp5 = entry - (5 * risk)
        
    # Geração das imagens dos gráficos
    img_h4 = plot_candles(h4, f"{name} - H4 Chart (Trend)", entry=entry if "SWING" in sig else None, sl=sl if "SWING" in sig else None, tp3=tp3 if "SWING" in sig else None, tp5=tp5 if "SWING" in sig else None)
    img_h1 = plot_candles(h1, f"{name} - H1 Chart (Structure)", entry=entry if "SWING" in sig else None, sl=sl if "SWING" in sig else None, tp3=tp3 if "SWING" in sig else None, tp5=tp5 if "SWING" in sig else None)
    img_m15 = plot_candles(m15, f"{name} - M15 Chart (Trigger)", entry=entry if "SWING" in sig else None, sl=sl if "SWING" in sig else None, tp3=tp3 if "SWING" in sig else None, tp5=tp5 if "SWING" in sig else None)

    return {
        "MARKET_STATE": "Accumulation" if "SWING" in sig else "Trending",
        "FINAL_DECISION": sig, "ENTRY_TYPE": entry_type,
        "WIN_RATE": sim['WR'], "NET_PROFIT": sim['NET'], "MAX_DRAWDOWN": sim['DD'], "PROFIT_FACTOR": sim['PF'],
        "MATH_ENTRY": round(entry,2), "MATH_SL": round(sl,2), "SL_DIST": round(risk,2),
        "MATH_TP3": round(tp3,2), "MATH_TP5": round(tp5,2),
        "RR_RATIO": "5.0",
        "SL_REASON": sl_reason,
        "IMAGES": [img_h4, img_h1, img_m15]
    }

# ==============================================================================
# 7. INTERFACE TRI-VISION - OTIMIZADA
# ==============================================================================

st.sidebar.title("🔐 SI-APATECO KEY")
if "GEMINI_API_KEY" in st.secrets: api = st.secrets["GEMINI_API_KEY"]; st.sidebar.success("ACCESS GRANTED")
else: api = st.sidebar.text_input("ENTER API KEY", type="password")

st.sidebar.divider()
st.sidebar.info("""
**V14.0 MISSION PROFILE:**
- 🎯 **Targets:** 1:3 & 1:5 Only (com Trailing Stop)
- 📡 **Análise:** H4/H1/M15 (Automática)
- 📊 **Precisão:** Zonas de Valor + Força da Tendência (ADX)
- 📈 **Backtest:** Métricas Avançadas (PF, DD)
""")

st.title("🔭 SI-APATECO SNIPER (V14.0)")
st.caption("Deep Multi-Timeframe Analysis | Institutional Payoff Logic")

with st.spinner("Locking on Targets..."):
    assets = get_assets()

if not assets: st.error("SIGNAL LOST."); st.stop()

# Layout
c1, c2 = st.columns([1, 1.5])

with c1:
    target = st.selectbox("MISSION TARGET", list(assets.keys()))

    st.markdown("### 📸 TRI-FORCE VISUALIZAÇÃO AUTOMÁTICA")
    st.caption("A IA irá gerar e analisar os 3 tempos gráficos automaticamente.")

    st.write("")
    run = st.button("CALCULATE VECTOR", use_container_width=True)

with c2:
    if run:
        if not api: st.error("⚠️ KEY REQUIRED"); st.stop()

        status = st.status("🛸 ENGAGING QUANTUM CORES...", expanded=True)

        status.write("1. Retrieving Full History (M15 / H1 / H4)...")
        h1, h4, m15, err = asyncio.run(fetch_tri_force(assets[target]))
        if err: status.update(state='error', label="NET FAIL"); st.error(err); st.stop()

        status.write("2. Running Risk/Reward Simulation (1000 candles)...")
        data = sniper_core(target, h1, h4, m15)
        
        # Extrai as imagens geradas
        generated_images = data.pop("IMAGES")

        status.write(f"3. Gemini Pro Analyzing Charts...")
        genai.configure(api_key=api)
        try:
            model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
            txt = model.generate_content([SYSTEM_PROMPT, f"MATH: {json.dumps(data)}"] + generated_images).text
            status.update(label="CALCULATION COMPLETE", state="complete")
        except Exception as e:
             st.error(f"AI Error: {e}. Tentando fallback...")
             try: 
                 fb = genai.GenerativeModel("gemini-1.5-pro")
                 txt = fb.generate_content([SYSTEM_PROMPT, f"MATH: {json.dumps(data)}"] + generated_images).text
                 status.update(label="COMPLETE (FALLBACK)", state="complete")
             except Exception as fb_e: 
                 st.error(f"AI Fallback Error: {fb_e}"); st.stop()

        # DASHBOARD
        st.subheader("💰 POTENCIAL DE RETORNO (HISTÓRICO)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Payoff Acum.", f"{data['NET_PROFIT']}R")
        m2.metric("Acertos Swing", f"{data['WIN_RATE']}%")
        m3.metric("Max Drawdown", f"{data['MAX_DRAWDOWN']}R")
        m4.metric("Profit Factor", f"{data['PROFIT_FACTOR']}")

        if "SWING" in data['FINAL_DECISION']:
            st.balloons()
            st.success(f"🎯 **CONFIRMADO:** Oportunidade de Swing Trade detectada. Payoff Histórico Positivo.")
        elif "BLOCKED" in data['FINAL_DECISION']:
            st.error("🛑 **TRADE CANCELADO:** Backtest negativo ou Profit Factor baixo. Este par não está respeitando setups 1:5 hoje.")

        # Grid Execução
        res_col = "green" if "SWING" in data['FINAL_DECISION'] else "red"
        st.markdown(f"#### SIGNAL: :{res_col}[{data['FINAL_DECISION']}]")
        st.dataframe([data], use_container_width=True)

        st.divider()
        st.markdown("### 📊 Gráficos Gerados para Análise da IA")
        st.image(generated_images[0], caption=f"{target} - H4 Chart (Trend)", use_column_width=True)
        st.image(generated_images[1], caption=f"{target} - H1 Chart (Structure)", use_column_width=True)
        st.image(generated_images[2], caption=f"{target} - M15 Chart (Trigger)", use_column_width=True)
        
        st.divider()
        st.markdown(txt)
