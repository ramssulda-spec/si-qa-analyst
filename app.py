import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import numpy as np
import google.generativeai as genai
from PIL import Image
import matplotlib.pyplot as plt
import io
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

# ==============================================================================
# SI-APATECO SNIPER V16.0 ULTRA - VERSÃO COMPLETA
# Sistema Dual + Trade Management em Tempo Real
# ==============================================================================

st.set_page_config(
    page_title="SI-APATECO SNIPER V16.0 ULTRA",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Aprimorado
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Teko:wght@300;600&family=Share+Tech+Mono&display=swap');
    
    .stApp {
        background-color: #050505;
        background-image: linear-gradient(0deg, #000 0%, #0a0a0a 100%);
        color: #d4d4d4;
        font-family: 'Share Tech Mono', monospace;
    }
    
    h1, h2, h3 {
        font-family: 'Teko', sans-serif !important;
        text-transform: uppercase;
        color: #fbbf24;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(251, 191, 36, 0.3);
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
    
    .score-s {
        color: #a855f7;
        font-weight: 900;
        font-size: 32px;
        animation: pulse 2s infinite;
    }
    .score-a-plus-plus {
        color: #10b981;
        font-weight: 900;
        font-size: 30px;
    }
    .score-a-plus {
        color: #3b82f6;
        font-weight: 900;
        font-size: 28px;
    }
    .score-a {
        color: #22d3ee;
        font-weight: 900;
        font-size: 26px;
    }
    .score-b {
        color: #fbbf24;
        font-weight: 900;
        font-size: 24px;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .trade-health-excellent {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .trade-health-good {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .trade-health-warning {
        background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .trade-health-danger {
        background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50%, 100% { opacity: 1; }
        25%, 75% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# PROMPT OTIMIZADO V16.0
# ==============================================================================
SYSTEM_PROMPT = """
FUNÇÃO: ANALISTA ELITE V16.0 ULTRA [Gemini 3 Pro]
Missão: Identificar Setups de Máxima Lucratividade + Gestão em Tempo Real

**RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO**

**V16.0 ULTRA - NOVAS CAPACIDADES:**
- Detecção de Divergências RSI/MACD
- Suporte/Resistência horizontal automático
- Fibonacci automático (38.2%, 50%, 61.8%)
- Padrões graduados por qualidade
- Perfect Alignment multi-timeframe
- Perfect Storm detection (6+ fatores)
- Score expandido: 0-150 pts (base 100 + bonus 50)

**TIPOS DE SETUP:**
1. **DAY TRADE (⚡):** Score ≥40, ADX >15, Targets 1:2 e 1:3
2. **SWING TRADE (📈):** Score ≥70, ADX >20, Targets 1:3 e 1:5
3. **BREAKOUT (💥):** Rompe S/R forte, Targets 1:3 e 1:7
4. **PERFECT STORM (🌟):** Score ≥120, 6+ fatores, Targets 1:5 e 1:10
5. **REVERSAL (🔄):** Divergência forte, Score ≥90, Targets 1:3 e 1:5

**DADOS APRIMORADOS:**
- Math Core + Score Expandido (0-150)
- Divergências detectadas (BULLISH/BEARISH/HIDDEN)
- S/R testados múltiplas vezes
- Níveis Fibonacci com confluência
- Perfect Alignment (EMAs nos 3 TFs)
- Perfect Storm status (quantos fatores alinham)

**FORMATO DE SAÍDA:**

## 🎯 VEREDICTO SNIPER V16.0: [ {FINAL_DECISION} ]
**Grade:** {GRADE_EMOJI} **{SETUP_GRADE}** | **Score:** {SETUP_SCORE}/150
**Tipo:** {TRADE_STYLE_EMOJI} {TRADE_STYLE} | **Targets:** {TARGETS}

### 📊 BREAKDOWN COMPLETO
**Score Base:** {BASE_SCORE}/100
- Força Tendência (ADX): {ADX_SCORE}/25
- Momentum Alignment: {MOMENTUM_SCORE}/20
- Padrões Candlestick: {PATTERN_SCORE}/15
- Zona de Valor: {VALUE_SCORE}/15
- Edge Histórico: {HIST_SCORE}/25

**Bonus Confluências:** +{BONUS_SCORE}/50
{Se houver divergência: "- 🔍 Divergência {TYPE}: +20"}
{Se houver Fibonacci: "- 📐 Fib {LEVEL} confluência: +10"}
{Se houver S/R: "- 🎯 S/R testado {N}x: +15"}
{Se Perfect Alignment: "- ⭐ Perfect Alignment: +25"}
{Se Perfect Storm: "- 🌟 PERFECT STORM: +25"}

### 👁️ ANÁLISE VISUAL TRI-FORCE
*   **H4 (Macro):** {Análise tendência, estrutura, divergências}
*   **H1 (Estrutura):** {Análise pivots, S/R, zona de valor}
*   **M15 (Gatilho):** {Análise padrões, trigger, confluências}

### 🎯 PLANO DE EXECUÇÃO
| Parâmetro | Valor | Observações |
| :--- | :--- | :--- |
| **ENTRADA** | **{ENTRY}** | *{ENTRY_TYPE}* |
| **STOP LOSS** | **{SL}** | *{SL_REASON}* |
| **{TP1_LABEL}** | **{TP1}** | *Realizar {PCT1}% aqui* |
| **{TP2_LABEL}** | **{TP2}** | *Deixar {PCT2}% + trailing* |
| **POSIÇÃO** | **{SIZE}** | *{RISK}% risco adaptativo* |

### 🔥 CONFLUÊNCIAS DETECTADAS
{Listar todas as confluências encontradas}
{Se Perfect Storm: "⚡ PERFECT STORM DETECTADO - 6+ FATORES ALINHADOS"}

*Insight V16.0:* {Explique POR QUE este setup tem score tão alto. Quais confluências tornam ele especial? Se Perfect Storm, enfatize a raridade. Confiança: Alto/Médio/Baixo}
"""

# ==============================================================================
# DERIV NETWORK
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
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def get_assets():
    req = {"active_symbols": "brief", "product_type": "basic"}
    for url in DERIV_SERVERS:
        res = asyncio.run(socket_req(url, req))
        if res and 'active_symbols' in res:
            return {x['display_name'].upper(): x['symbol'] for x in res['active_symbols'] 
                    if x['market']=='synthetic_index'}
    return None

async def fetch_tri_force(code):
    reqs = [
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 300, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 200, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 1000, "end": "latest"}
    ]
    
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=20, close_timeout=15) as ws:
                await ws.send(json.dumps(reqs[0]))
                h1 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                await ws.send(json.dumps(reqs[1]))
                h4 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                await ws.send(json.dumps(reqs[2]))
                m15 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                
                if all('candles' in x for x in [h1, h4, m15]):
                    return h1['candles'], h4['candles'], m15['candles'], None
        except:
            continue
            
    return None, None, None, "CONNECTION LOST"

async def stream_live_prices(code):
    """Stream preços em tempo real para monitoramento de trade"""
    req = {"ticks": code, "subscribe": 1}
    
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                await ws.send(json.dumps(req))
                
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(msg)
                    
                    if 'tick' in data:
                        yield {
                            'price': float(data['tick']['quote']),
                            'time': datetime.fromtimestamp(data['tick']['epoch'])
                        }
        except:
            continue

# ==============================================================================
# INDICADORES TÉCNICOS V16.0
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']: 
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    return df

def calculate_adx(df, window=14):
    df['trh'] = df['high'] - df['low']
    df['trc'] = abs(df['high'] - df['close'].shift())
    df['trl'] = abs(df['low'] - df['close'].shift())
    df['TR'] = df[['trh', 'trc', 'trl']].max(axis=1)
    
    df['+DM'] = np.where((df['high'] > df['high'].shift()) & (df['low'] <= df['low'].shift()), 
                         df['high'] - df['high'].shift(), 0)
    df['-DM'] = np.where((df['low'] < df['low'].shift()) & (df['high'] >= df['high'].shift()), 
                         df['low'].shift() - df['low'], 0)
    
    df['+DM'] = np.where(df['+DM'] > df['-DM'], df['+DM'], 0)
    df['-DM'] = np.where(df['-DM'] > df['+DM'], df['-DM'], 0)
    
    df['TR_EMA'] = df['TR'].ewm(span=window, adjust=False).mean()
    df['+DM_EMA'] = df['+DM'].ewm(span=window, adjust=False).mean()
    df['-DM_EMA'] = df['-DM'].ewm(span=window, adjust=False).mean()
    
    df['+DI'] = (df['+DM_EMA'] / df['TR_EMA']) * 100
    df['-DI'] = (df['-DM_EMA'] / df['TR_EMA']) * 100
    df['DX'] = (abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])) * 100
    df['ADX'] = df['DX'].ewm(span=window, adjust=False).mean()
    
    df.drop(columns=['trh', 'trc', 'trl', 'TR', '+DM', '-DM', 'TR_EMA', 
                     '+DM_EMA', '-DM_EMA', '+DI', '-DI', 'DX'], inplace=True)
    return df

# ==============================================================================
# V16.0 NOVO: DETECÇÃO DE DIVERGÊNCIAS
# ==============================================================================

def detect_divergence(df, indicator='RSI', lookback=5):
    """
    Detecta divergências entre preço e indicador
    Retorna: (tipo, score_bonus)
    """
    try:
        if len(df) < lookback + 2:
            return None, 0
        
        if indicator not in df.columns:
            return None, 0
        
        recent = df.tail(lookback)
        
        price_highs = recent['high']
        price_lows = recent['low']
        ind_values = recent[indicator]
        
        # Bearish Divergence (preço sobe, indicador cai)
        if len(price_highs) >= 3:
            last_high_price = price_highs.iloc[-1]
            prev_high_price = price_highs.iloc[-3]
            
            last_high_ind = ind_values.iloc[-1]
            prev_high_ind = ind_values.iloc[-3]
            
            if pd.notna(last_high_ind) and pd.notna(prev_high_ind) and prev_high_ind != 0:
                if last_high_price > prev_high_price and last_high_ind < prev_high_ind:
                    strength = abs(last_high_ind - prev_high_ind) / abs(prev_high_ind)
                    if strength > 0.05:  # 5% divergência mínima
                        return "BEARISH_DIVERGENCE", -20
        
        # Bullish Divergence (preço cai, indicador sobe)
        if len(price_lows) >= 3:
            last_low_price = price_lows.iloc[-1]
            prev_low_price = price_lows.iloc[-3]
            
            last_low_ind = ind_values.iloc[-1]
            prev_low_ind = ind_values.iloc[-3]
            
            if pd.notna(last_low_ind) and pd.notna(prev_low_ind) and prev_low_ind != 0:
                if last_low_price < prev_low_price and last_low_ind > prev_low_ind:
                    strength = abs(last_low_ind - prev_low_ind) / abs(prev_low_ind)
                    if strength > 0.05:
                        return "BULLISH_DIVERGENCE", +20
        
        return None, 0
    except Exception as e:
        # Em caso de erro, retorna None silenciosamente
        return None, 0

# ==============================================================================
# V16.0 NOVO: SUPORTE E RESISTÊNCIA
# ==============================================================================

def detect_support_resistance(df, window=50, tolerance_atr_multiplier=0.5):
    """
    Detecta níveis de S/R testados múltiplas vezes
    """
    try:
        if len(df) < window:
            return []
        
        if 'ATR' not in df.columns:
            return []
        
        recent = df.tail(window)
        atr = recent['ATR'].iloc[-1]
        
        if pd.isna(atr) or atr == 0:
            return []
        
        tolerance = atr * tolerance_atr_multiplier
        
        levels = []
        
        # Encontrar clusters de toques
        prices = pd.concat([recent['high'], recent['low']]).values
        
        for price in np.unique(prices):
            if pd.isna(price):
                continue
                
            touches = sum(abs(recent['high'] - price) < tolerance) + \
                      sum(abs(recent['low'] - price) < tolerance)
            
            if touches >= 3:  # Testado 3+ vezes
                current_price = df['close'].iloc[-1]
                levels.append({
                    'price': price,
                    'touches': touches,
                    'type': 'RESISTANCE' if price > current_price else 'SUPPORT',
                    'strength': touches
                })
        
        # Ordenar por força
        levels.sort(key=lambda x: x['strength'], reverse=True)
        return levels[:5]  # Top 5
    except Exception as e:
        return []

# ==============================================================================
# V16.0 NOVO: FIBONACCI AUTOMÁTICO
# ==============================================================================

def calculate_fibonacci_levels(df, lookback=50):
    """
    Calcula níveis de Fibonacci baseado no último swing
    """
    try:
        if len(df) < lookback:
            return {}
        
        recent = df.tail(lookback)
        swing_high = recent['high'].max()
        swing_low = recent['low'].min()
        
        if pd.isna(swing_high) or pd.isna(swing_low):
            return {}
        
        diff = swing_high - swing_low
        
        if diff == 0:
            return {}
        
        fibs = {
            '0.0%': swing_low,
            '23.6%': swing_low + (diff * 0.236),
            '38.2%': swing_low + (diff * 0.382),
            '50.0%': swing_low + (diff * 0.50),
            '61.8%': swing_low + (diff * 0.618),
            '78.6%': swing_low + (diff * 0.786),
            '100%': swing_high
        }
        
        return fibs
    except Exception as e:
        return {}

def check_fib_confluence(price, fibs, atr):
    """Verifica se preço está próximo de Fibonacci"""
    try:
        if not fibs or pd.isna(price) or pd.isna(atr) or atr == 0:
            return None, 0
        
        tolerance = atr * 0.5
        
        for level_name, level_price in fibs.items():
            if pd.notna(level_price) and abs(price - level_price) < tolerance:
                return level_name, +10
        
        return None, 0
    except Exception as e:
        return None, 0

# ==============================================================================
# V16.0 NOVO: PADRÕES GRADUADOS POR QUALIDADE
# ==============================================================================

def detect_pin_bar_quality(row, prev_row):
    """Detecta pin bar com graduação de qualidade"""
    body = abs(row['close'] - row['open'])
    total_range = row['high'] - row['low']
    
    if total_range == 0:
        return None, 0
    
    body_pct = body / total_range
    upper_wick = row['high'] - max(row['open'], row['close'])
    lower_wick = min(row['open'], row['close']) - row['low']
    
    # Bullish Pin Bar
    if lower_wick > 0 and body_pct < 0.4 and upper_wick < body:
        wick_ratio = lower_wick / max(body, 0.0001)
        
        if wick_ratio > 5:
            return "PIN_BULLISH_EXTREME", 15
        elif wick_ratio > 3:
            return "PIN_BULLISH_STRONG", 10
        elif wick_ratio > 2:
            return "PIN_BULLISH_MODERATE", 5
    
    # Bearish Pin Bar
    elif upper_wick > 0 and body_pct < 0.4 and lower_wick < body:
        wick_ratio = upper_wick / max(body, 0.0001)
        
        if wick_ratio > 5:
            return "PIN_BEARISH_EXTREME", 15
        elif wick_ratio > 3:
            return "PIN_BEARISH_STRONG", 10
        elif wick_ratio > 2:
            return "PIN_BEARISH_MODERATE", 5
    
    return None, 0

def detect_engulfing_quality(row, prev_row):
    """Detecta engulfing com graduação"""
    curr_body = abs(row['close'] - row['open'])
    prev_body = abs(prev_row['close'] - prev_row['open'])
    
    curr_body_top = max(row['open'], row['close'])
    curr_body_bottom = min(row['open'], row['close'])
    prev_body_top = max(prev_row['open'], prev_row['close'])
    prev_body_bottom = min(prev_row['open'], prev_row['close'])
    
    # Bullish Engulfing
    if (row['close'] > row['open'] and prev_row['close'] < prev_row['open'] and
        curr_body_bottom < prev_body_bottom and curr_body_top > prev_body_top):
        
        size_ratio = curr_body / max(prev_body, 0.0001)
        
        if size_ratio > 3:
            return "ENGULF_BULLISH_MASSIVE", 15
        elif size_ratio > 2:
            return "ENGULF_BULLISH_STRONG", 10
        else:
            return "ENGULF_BULLISH_MODERATE", 5
    
    # Bearish Engulfing
    elif (row['close'] < row['open'] and prev_row['close'] > prev_row['open'] and
          curr_body_bottom < prev_body_bottom and curr_body_top > prev_body_top):
        
        size_ratio = curr_body / max(prev_body, 0.0001)
        
        if size_ratio > 3:
            return "ENGULF_BEARISH_MASSIVE", 15
        elif size_ratio > 2:
            return "ENGULF_BEARISH_STRONG", 10
        else:
            return "ENGULF_BEARISH_MODERATE", 5
    
    return None, 0

def detect_inside_bar(row, prev_row):
    if row['high'] <= prev_row['high'] and row['low'] >= prev_row['low']:
        return "INSIDE_BAR", 5
    return None, 0

def detect_doji(row):
    body = abs(row['close'] - row['open'])
    total_range = row['high'] - row['low']
    
    if total_range > 0 and body / total_range < 0.1:
        return "DOJI", 3
    return None, 0

def detect_patterns_v16(df):
    """V16.0: Padrões com qualidade graduada"""
    patterns = []
    pattern_scores = []
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        pattern_list = []
        score = 0
        
        pin, pin_score = detect_pin_bar_quality(curr, prev)
        if pin:
            pattern_list.append(pin)
            score += pin_score
        
        eng, eng_score = detect_engulfing_quality(curr, prev)
        if eng:
            pattern_list.append(eng)
            score += eng_score
        
        inside, inside_score = detect_inside_bar(curr, prev)
        if inside:
            pattern_list.append(inside)
            score += inside_score
        
        doji, doji_score = detect_doji(curr)
        if doji:
            pattern_list.append(doji)
            score += doji_score
        
        patterns.append(pattern_list)
        pattern_scores.append(score)
    
    df['patterns'] = [[]] + patterns
    df['pattern_score'] = [0] + pattern_scores
    return df

def detect_swing_points(df, window=5):
    df['swing_high'] = df['high'] == df['high'].rolling(window=window, center=True).max()
    df['swing_low'] = df['low'] == df['low'].rolling(window=window, center=True).min()
    return df

def classify_market_structure(df):
    swing_highs = df[df['swing_high']]['high'].tail(3)
    swing_lows = df[df['swing_low']]['low'].tail(3)
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "INSUFFICIENT_DATA"
    
    hh = swing_highs.iloc[-1] > swing_highs.iloc[-2]
    hl = swing_lows.iloc[-1] > swing_lows.iloc[-2]
    ll = swing_lows.iloc[-1] < swing_lows.iloc[-2]
    lh = swing_highs.iloc[-1] < swing_highs.iloc[-2]
    
    if hh and hl:
        return "UPTREND_STRONG"
    elif ll and lh:
        return "DOWNTREND_STRONG"
    elif hh or hl:
        return "UPTREND_WEAK"
    elif ll or lh:
        return "DOWNTREND_WEAK"
    else:
        return "RANGE_BOUND"

def calculate_volatility_regime(df):
    atr_pct = (df['ATR'] / df['close']) * 100
    current_atr_pct = atr_pct.iloc[-1]
    
    if current_atr_pct < 0.3:
        return "VERY_LOW", current_atr_pct
    elif current_atr_pct < 0.5:
        return "LOW", current_atr_pct
    elif current_atr_pct < 1.5:
        return "MEDIUM", current_atr_pct
    elif current_atr_pct < 2.5:
        return "HIGH", current_atr_pct
    else:
        return "EXTREME_HIGH", current_atr_pct

def indicators(df):
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(span=14, adjust=False).mean()
    avg_loss = loss.ewm(span=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    df['tr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = df['tr'].ewm(span=14, adjust=False).mean()
    
    df = calculate_adx(df)
    df = calculate_macd(df)
    
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
    df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
    df['BB_width'] = ((df['BB_upper'] - df['BB_lower']) / df['BB_middle']) * 100
    
    df = detect_patterns_v16(df)
    df = detect_swing_points(df)
    
    df.dropna(inplace=True)
    return df

# ==============================================================================
# V16.0 NOVO: PERFECT ALIGNMENT DETECTOR
# ==============================================================================

def detect_perfect_alignment(h4_row, h1_row, m15_row, direction):
    """
    Detecta quando EMAs estão perfeitamente alinhadas nos 3 TFs
    """
    score = 0
    
    if direction == "BULLISH":
        # H4
        if (h4_row['close'] > h4_row['EMA_20'] > h4_row['EMA_50'] > h4_row['EMA_200']):
            score += 10
        
        # H1
        if (h1_row['close'] > h1_row['EMA_20'] > h1_row['EMA_50'] > h1_row['EMA_200']):
            score += 10
        
        # M15
        if (m15_row['close'] > m15_row['EMA_20'] > m15_row['EMA_50'] > m15_row['EMA_200']):
            score += 10
    
    elif direction == "BEARISH":
        # H4
        if (h4_row['close'] < h4_row['EMA_20'] < h4_row['EMA_50'] < h4_row['EMA_200']):
            score += 10
        
        # H1
        if (h1_row['close'] < h1_row['EMA_20'] < h1_row['EMA_50'] < h1_row['EMA_200']):
            score += 10
        
        # M15
        if (m15_row['close'] < m15_row['EMA_20'] < m15_row['EMA_50'] < m15_row['EMA_200']):
            score += 10
    
    if score == 30:
        return "PERFECT_ALIGNMENT", +25
    elif score >= 20:
        return "STRONG_ALIGNMENT", +15
    elif score >= 10:
        return "WEAK_ALIGNMENT", +5
    else:
        return "NO_ALIGNMENT", 0

# ==============================================================================
# V16.0 NOVO: PERFECT STORM DETECTOR
# ==============================================================================

def calculate_perfect_storm_bonus(setup_data):
    """
    Bonus massivo quando 6+ fatores alinham (setup raríssimo)
    """
    criteria_met = 0
    criteria_list = []
    
    if setup_data.get('adx', 0) > 30:
        criteria_met += 1
        criteria_list.append("ADX > 30")
    
    if setup_data.get('momentum_score', 0) == 3:
        criteria_met += 1
        criteria_list.append("Momentum 3/3")
    
    if setup_data.get('pattern_score', 0) >= 20:
        criteria_met += 1
        criteria_list.append("Padrões fortes")
    
    if setup_data.get('divergence') is not None:
        criteria_met += 1
        criteria_list.append("Divergência detectada")
    
    if setup_data.get('fib_confluence'):
        criteria_met += 1
        criteria_list.append("Fib confluência")
    
    if setup_data.get('sr_touch'):
        criteria_met += 1
        criteria_list.append("S/R testado")
    
    if setup_data.get('perfect_alignment'):
        criteria_met += 1
        criteria_list.append("Perfect Alignment")
    
    if setup_data.get('bb_compression'):
        criteria_met += 1
        criteria_list.append("BB Compression")
    
    bonus = 0
    storm_level = None
    
    if criteria_met >= 6:
        bonus = +25
        storm_level = "PERFECT_STORM"
    elif criteria_met >= 5:
        bonus = +15
        storm_level = "STRONG_CONFLUENCE"
    elif criteria_met >= 4:
        bonus = +10
        storm_level = "GOOD_CONFLUENCE"
    
    return storm_level, bonus, criteria_list

# ==============================================================================
# MOMENTUM ALIGNMENT
# ==============================================================================

def check_momentum_alignment(h4_df, h1_df, m15_df, direction):
    score = 0
    
    h4_macd = h4_df['MACD'].iloc[-1]
    h1_macd = h1_df['MACD'].iloc[-1]
    m15_macd = m15_df['MACD'].iloc[-1]
    
    if direction == "BULLISH":
        if h4_macd > 0: score += 1
        if h1_macd > 0: score += 1
        if m15_macd > 0: score += 1
    else:
        if h4_macd < 0: score += 1
        if h1_macd < 0: score += 1
        if m15_macd < 0: score += 1
    
    return score

# ==============================================================================
# SETUP SCORING V16.0 (0-150)
# ==============================================================================

@dataclass
class SetupScoreV16:
    # Base (100)
    trend_strength: float
    momentum_align: float
    patterns: float
    value_zone: float
    historical: float
    base_total: float
    
    # Bonus (50)
    divergence_bonus: float
    fib_bonus: float
    sr_bonus: float
    alignment_bonus: float
    storm_bonus: float
    bonus_total: float
    
    # Total
    total: float
    grade: str

def calculate_setup_score_v16(adx, momentum_score, pattern_score, distance_from_ema50, 
                               atr, win_rate, profit_factor, divergence_bonus=0,
                               fib_bonus=0, sr_bonus=0, alignment_bonus=0, storm_bonus=0):
    """
    V16.0: Score expandido 0-150 (base 100 + bonus 50)
    """
    
    # BASE SCORE (100 pontos)
    if adx > 25:
        trend_score = 25
    elif adx > 15:
        trend_score = 15
    else:
        trend_score = 0
    
    momentum_score_pts = (momentum_score / 3) * 20
    
    dist_ratio = distance_from_ema50 / atr
    if dist_ratio < 0.5:
        value_score = 15
    elif dist_ratio < 1.0:
        value_score = 10
    elif dist_ratio < 1.5:
        value_score = 5
    else:
        value_score = 0
    
    hist_score = min((win_rate * 0.15) + (profit_factor * 5), 25)
    
    base_total = trend_score + momentum_score_pts + pattern_score + value_score + hist_score
    
    # BONUS SCORE (até 50 pontos)
    bonus_total = divergence_bonus + fib_bonus + sr_bonus + alignment_bonus + storm_bonus
    bonus_total = min(bonus_total, 50)  # Cap em 50
    
    # TOTAL
    total = base_total + bonus_total
    
    # GRADES V16.0
    if total >= 140:
        grade = "S"  # Legendary
    elif total >= 120:
        grade = "A++"  # Elite
    elif total >= 90:
        grade = "A+"
    elif total >= 70:
        grade = "A"
    elif total >= 50:
        grade = "B"
    elif total >= 30:
        grade = "C"
    else:
        grade = "D"
    
    return SetupScoreV16(
        trend_strength=trend_score,
        momentum_align=momentum_score_pts,
        patterns=pattern_score,
        value_zone=value_score,
        historical=hist_score,
        base_total=base_total,
        divergence_bonus=divergence_bonus,
        fib_bonus=fib_bonus,
        sr_bonus=sr_bonus,
        alignment_bonus=alignment_bonus,
        storm_bonus=storm_bonus,
        bonus_total=bonus_total,
        total=total,
        grade=grade
    )

# ==============================================================================
# BACKTEST (Lazy Loading)
# ==============================================================================

def has_potential_setup(adx, ema_alignment, patterns):
    """Quick check antes de rodar backtest completo"""
    if adx < 10:
        return False
    if len(patterns) == 0 and not ema_alignment:
        return False
    return True

def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    if len(returns) < 2:
        return 0
    excess_returns = returns - risk_free_rate
    if excess_returns.std() == 0:
        return 0
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

def calculate_sortino_ratio(returns, risk_free_rate=0.0):
    if len(returns) < 2:
        return 0
    excess_returns = returns - risk_free_rate
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0
    return (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)

def run_enhanced_backtest(df, trend_dir):
    split_idx = int(len(df) * 0.7)
    
    trades = 0
    hits_5R = 0
    balance = 0.0
    max_balance = 0.0
    min_balance = 0.0
    total_wins = 0
    total_losses = 0
    returns_list = []
    consecutive_wins = 0
    consecutive_losses = 0
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    
    start_idx = max(200, split_idx)
    
    if len(df) <= start_idx + 80:
        return {
            "WR": 0, "NET": 0, "DD": 0, "PF": 0, 
            "SHARPE": 0, "SORTINO": 0, "RECOVERY": 0,
            "MAX_CONS_WIN": 0, "MAX_CONS_LOSS": 0
        }
    
    for i in range(start_idx, len(df) - 80):
        row = df.iloc[i]
        
        sig = None
        is_adx_strong = row['ADX'] > 20
        
        if trend_dir == "BULLISH" and is_adx_strong:
            if row['close'] > row['EMA_200'] and (row['low'] <= row['EMA_50'] or row['RSI'] < 45):
                sig = "BUY"
        elif trend_dir == "BEARISH" and is_adx_strong:
            if row['close'] < row['EMA_200'] and (row['high'] >= row['EMA_50'] or row['RSI'] > 55):
                sig = "SELL"
        
        if sig:
            entry = row['close']
            atr = row['ATR']
            
            sl_candidate = detect_swing_level(df.iloc[:i+1], sig)
            if sig == "BUY":
                sl = max(entry - (3 * atr), sl_candidate)
            else:
                sl = min(entry + (3 * atr), sl_candidate)
            
            risk_per_trade = abs(entry - sl)
            if risk_per_trade == 0: 
                risk_per_trade = atr
            
            tp_3R = entry + (3 * risk_per_trade) if sig == "BUY" else entry - (3 * risk_per_trade)
            tp_5R = entry + (5 * risk_per_trade) if sig == "BUY" else entry - (5 * risk_per_trade)
            
            res = "OPEN"
            current_tp2 = tp_5R
            
            for f in range(i + 1, min(i + 80, len(df))):
                nx = df.iloc[f]
                
                if sig == "BUY":
                    if nx['low'] <= sl: 
                        res = "LOSS"
                        break
                    if nx['high'] >= tp_3R:
                        sl = entry
                        current_tp2 = max(current_tp2, nx['high'] - (2 * atr))
                    if nx['high'] >= current_tp2: 
                        res = "WIN"
                        break
                else:
                    if nx['high'] >= sl: 
                        res = "LOSS"
                        break
                    if nx['low'] <= tp_3R:
                        sl = entry
                        current_tp2 = min(current_tp2, nx['low'] + (2 * atr))
                    if nx['low'] <= current_tp2: 
                        res = "WIN"
                        break
            
            if res != "OPEN":
                trades += 1
                if res == "WIN":
                    hits_5R += 1
                    balance += 5.0
                    total_wins += 1
                    returns_list.append(5.0)
                    consecutive_wins += 1
                    consecutive_losses = 0
                    max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
                else:
                    balance -= 1.0
                    total_losses += 1
                    returns_list.append(-1.0)
                    consecutive_losses += 1
                    consecutive_wins = 0
                    max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                
                max_balance = max(max_balance, balance)
                min_balance = min(min_balance, balance)
    
    wr = (hits_5R / trades * 100) if trades > 0 else 0
    profit_factor = (total_wins * 5.0) / (total_losses * 1.0) if total_losses > 0 else (5.0 if total_wins > 0 else 0.0)
    max_dd = max_balance - min_balance
    
    returns_series = pd.Series(returns_list)
    sharpe = calculate_sharpe_ratio(returns_series)
    sortino = calculate_sortino_ratio(returns_series)
    recovery = balance / max_dd if max_dd > 0 else 0
    
    return {
        "WR": round(wr, 1),
        "NET": round(balance, 1),
        "DD": round(max_dd, 1),
        "PF": round(profit_factor, 2),
        "SHARPE": round(sharpe, 2),
        "SORTINO": round(sortino, 2),
        "RECOVERY": round(recovery, 2),
        "MAX_CONS_WIN": max_consecutive_wins,
        "MAX_CONS_LOSS": max_consecutive_losses
    }

def detect_swing_level(df, direction, atr_multiplier=1.5):
    if direction == "BUY":
        swing_lows = df[df['swing_low']]['low']
        if not swing_lows.empty:
            return swing_lows.iloc[-1] - (df['ATR'].iloc[-1] * atr_multiplier)
        return df['low'].tail(20).min() - (df['ATR'].iloc[-1] * atr_multiplier)
    elif direction == "SELL":
        swing_highs = df[df['swing_high']]['high']
        if not swing_highs.empty:
            return swing_highs.iloc[-1] + (df['ATR'].iloc[-1] * atr_multiplier)
        return df['high'].tail(20).max() + (df['ATR'].iloc[-1] * atr_multiplier)
    return df.iloc[-1]['close']

# ==============================================================================
# V16.0: POSITION SIZING ADAPTATIVO
# ==============================================================================

def adaptive_position_size(capital, risk_pct, entry, sl, atr_pct):
    """
    Ajusta position size baseado na volatilidade do ativo
    """
    base_risk = capital * (risk_pct / 100)
    
    # Ajuste por volatilidade
    if atr_pct > 3.0:  # Muito volátil (Vol 75)
        adjusted_risk = base_risk * 0.5
    elif atr_pct > 2.0:
        adjusted_risk = base_risk * 0.7
    elif atr_pct < 0.5:  # Pouco volátil (Vol 10)
        adjusted_risk = base_risk * 1.5
    else:
        adjusted_risk = base_risk
    
    risk_per_unit = abs(entry - sl)
    if risk_per_unit == 0:
        return 0, 0, "N/A"
    
    position_size = adjusted_risk / risk_per_unit
    position_value = position_size * entry
    
    if atr_pct > 3.0:
        note = "Vol alta - Exposição reduzida 50%"
    elif atr_pct < 0.5:
        note = "Vol baixa - Exposição aumentada 50%"
    else:
        note = "Vol normal - Exposição padrão"
    
    return round(position_size, 2), round(position_value, 2), note

def calculate_kelly_criterion(win_rate, avg_win, avg_loss):
    if avg_loss == 0:
        return 0
    
    win_rate_decimal = win_rate / 100
    loss_rate = 1 - win_rate_decimal
    
    kelly = (win_rate_decimal * avg_win - loss_rate * avg_loss) / avg_loss
    return max(0, min(kelly * 0.5, 0.1))

# ==============================================================================
# V16.0: TRADE MANAGEMENT SYSTEM (TEMPO REAL)
# ==============================================================================

@dataclass
class ActiveTrade:
    """Representa um trade ativo sendo monitorado"""
    symbol: str
    direction: str  # LONG ou SHORT
    entry_price: float
    current_price: float
    sl: float
    tp1: float
    tp2: float
    entry_time: datetime
    atr: float
    initial_risk: float
    
    # Estado
    sl_moved_to_be: bool = False
    tp1_hit: bool = False
    realized_pct: float = 0.0  # % já realizado
    
    # Monitoramento
    highest_price: float = 0.0  # Para LONG
    lowest_price: float = 999999.0  # Para SHORT
    
    def update_price(self, new_price: float):
        """Atualiza preço e extremos"""
        self.current_price = new_price
        
        if self.direction == "LONG":
            self.highest_price = max(self.highest_price, new_price)
        else:
            self.lowest_price = min(self.lowest_price, new_price)
    
    def get_current_r(self) -> float:
        """Retorna R atual (múltiplo do risco inicial)"""
        if self.direction == "LONG":
            profit = self.current_price - self.entry_price
        else:
            profit = self.entry_price - self.current_price
        
        return profit / self.initial_risk
    
    def get_unrealized_pl(self) -> float:
        """P&L não realizado"""
        if self.direction == "LONG":
            return self.current_price - self.entry_price
        else:
            return self.entry_price - self.current_price

def calculate_intelligent_trailing(trade: ActiveTrade, momentum: float) -> float:
    """
    V16.0: Trailing stop baseado em momentum
    """
    atr = trade.atr
    
    # Ajusta distância baseado em momentum
    if momentum > 0.8:  # Momentum forte
        trail_distance = 1.5 * atr
    elif momentum > 0.5:  # Normal
        trail_distance = 2.0 * atr
    else:  # Fraco
        trail_distance = 2.5 * atr
    
    if trade.direction == "LONG":
        new_sl = trade.current_price - trail_distance
        return max(new_sl, trade.entry_price, trade.sl)  # Nunca piora
    else:
        new_sl = trade.current_price + trail_distance
        return min(new_sl, trade.entry_price, trade.sl)

def analyze_trade_health(trade: ActiveTrade, df_m15) -> Dict:
    """
    Analisa "saúde" do trade em tempo real
    Retorna alertas e recomendações
    """
    alerts = []
    health_score = 100
    recommendations = []
    
    current_r = trade.get_current_r()
    
    # 1. Verificar se deve mover para BE
    if not trade.sl_moved_to_be and current_r >= 1.5:
        alerts.append("🟢 MOVER STOP PARA BREAK-EVEN")
        recommendations.append({
            'type': 'MOVE_TO_BE',
            'action': 'Mover stop loss para entrada (proteção de capital)',
            'priority': 'HIGH'
        })
    
    # 2. Verificar se atingiu TP1
    if not trade.tp1_hit:
        if trade.direction == "LONG" and trade.current_price >= trade.tp1:
            alerts.append("🎯 TP1 ATINGIDO - Realizar 50%")
            recommendations.append({
                'type': 'TAKE_PROFIT_1',
                'action': 'Realizar 50% da posição, mover SL para BE',
                'priority': 'CRITICAL'
            })
        elif trade.direction == "SHORT" and trade.current_price <= trade.tp1:
            alerts.append("🎯 TP1 ATINGIDO - Realizar 50%")
            recommendations.append({
                'type': 'TAKE_PROFIT_1',
                'action': 'Realizar 50% da posição, mover SL para BE',
                'priority': 'CRITICAL'
            })
    
    # 3. Detectar reversão iminente
    if len(df_m15) >= 3:
        recent_divergence, div_score = detect_divergence(df_m15, 'RSI', lookback=5)
        
        if recent_divergence:
            if (trade.direction == "LONG" and "BEARISH" in recent_divergence) or \
               (trade.direction == "SHORT" and "BULLISH" in recent_divergence):
                alerts.append(f"⚠️ DIVERGÊNCIA CONTRÁRIA DETECTADA ({recent_divergence})")
                health_score -= 30
                recommendations.append({
                    'type': 'REVERSAL_RISK',
                    'action': 'Considerar fechar posição total ou apertar trailing',
                    'priority': 'HIGH'
                })
    
    # 4. Verificar momentum
    if len(df_m15) >= 14:
        current_macd = df_m15['MACD'].iloc[-1]
        macd_signal = df_m15['MACD_signal'].iloc[-1]
        
        if trade.direction == "LONG":
            if current_macd < macd_signal:  # MACD virando
                alerts.append("⚠️ MACD PERDENDO FORÇA")
                health_score -= 20
                recommendations.append({
                    'type': 'MOMENTUM_WEAK',
                    'action': 'Apertar trailing stop',
                    'priority': 'MEDIUM'
                })
        else:
            if current_macd > macd_signal:
                alerts.append("⚠️ MACD PERDENDO FORÇA")
                health_score -= 20
                recommendations.append({
                    'type': 'MOMENTUM_WEAK',
                    'action': 'Apertar trailing stop',
                    'priority': 'MEDIUM'
                })
    
    # 5. Verificar se está muito longe sem realizar
    if current_r > 4.0 and trade.realized_pct == 0:
        alerts.append("💰 LUCRO SIGNIFICATIVO - Considerar realizar parcial")
        recommendations.append({
            'type': 'TAKE_PARTIAL',
            'action': f'Realizar 30-40% com +{current_r:.1f}R de lucro',
            'priority': 'MEDIUM'
        })
    
    # 6. Classificar saúde
    if health_score >= 80:
        health_status = "EXCELLENT"
        health_color = "trade-health-excellent"
    elif health_score >= 60:
        health_status = "GOOD"
        health_color = "trade-health-good"
    elif health_score >= 40:
        health_status = "WARNING"
        health_color = "trade-health-warning"
    else:
        health_status = "DANGER"
        health_color = "trade-health-danger"
    
    return {
        'health_score': health_score,
        'health_status': health_status,
        'health_color': health_color,
        'current_r': current_r,
        'alerts': alerts,
        'recommendations': recommendations
    }

# ==============================================================================
# CHART PLOTTING
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp1=None, tp2=None, patterns=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
    
    for i in range(len(df)):
        color = 'green' if df['open'].iloc[i] < df['close'].iloc[i] else 'red'
        ax1.plot([df.index[i], df.index[i]], [df['low'].iloc[i], df['high'].iloc[i]], 
                color=color, linewidth=1)
        ax1.plot([df.index[i], df.index[i]], [df['open'].iloc[i], df['close'].iloc[i]], 
                color=color, linewidth=4)
    
    ax1.plot(df.index, df['EMA_20'], label='EMA 20', color='cyan', linestyle='--', alpha=0.7)
    ax1.plot(df.index, df['EMA_50'], label='EMA 50', color='orange', linestyle='--', alpha=0.7)
    ax1.plot(df.index, df['EMA_200'], label='EMA 200', color='purple', linestyle='-', alpha=0.5)
    
    ax1.plot(df.index, df['BB_upper'], color='gray', linestyle=':', alpha=0.5)
    ax1.plot(df.index, df['BB_lower'], color='gray', linestyle=':', alpha=0.5)
    
    if entry: ax1.axhline(y=entry, color='cyan', linestyle='-', label='Entry', linewidth=2)
    if sl: ax1.axhline(y=sl, color='red', linestyle='-', label='Stop Loss', linewidth=2)
    if tp1: ax1.axhline(y=tp1, color='lime', linestyle='--', label='TP1', linewidth=2)
    if tp2: ax1.axhline(y=tp2, color='green', linestyle='-', label='TP2', linewidth=2)
    
    if patterns and 'patterns' in df.columns:
        last_patterns = df['patterns'].iloc[-1]
        if last_patterns:
            pattern_str = ", ".join(last_patterns)
            ax1.text(df.index[-1], df['high'].iloc[-1], f" {pattern_str}", 
                    fontsize=8, color='yellow', fontweight='bold')
    
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    colors = ['green' if x > 0 else 'red' for x in df['MACD_hist']]
    ax2.bar(df.index, df['MACD_hist'], color=colors, alpha=0.5, width=0.8)
    ax2.plot(df.index, df['MACD'], label='MACD', color='blue', linewidth=1)
    ax2.plot(df.index, df['MACD_signal'], label='Signal', color='red', linewidth=1)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_title('MACD', fontsize=10)
    ax2.legend(loc='upper left', fontsize=7)
    ax2.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

def convert_numpy_to_python(obj):
    """
    Converte tipos numpy para tipos Python nativos para serialização JSON
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_to_python(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

# ==============================================================================
# SNIPER CORE V16.0 ULTRA
# ==============================================================================

def sniper_core_v16_ultra(name, h1_raw, h4_raw, m15_raw, capital=10000, risk_pct=1.0):
    """
    V16.0 ULTRA: Sistema completo com todas as melhorias
    """
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = indicators(prep_df(m15_raw))
    
    curr_h1 = h1.iloc[-1]
    curr_h4 = h4.iloc[-1]
    curr_m15 = m15.iloc[-1]
    
    # Análises V16.0
    bias_h4 = "BULLISH" if curr_h4['close'] > curr_h4['EMA_200'] else "BEARISH"
    adx_h4 = curr_h4['ADX']
    
    structure = classify_market_structure(h1)
    vol_regime, vol_pct = calculate_volatility_regime(h1)
    momentum_score = check_momentum_alignment(h4, h1, m15, bias_h4)
    
    # V16.0 NOVOS: Divergências
    rsi_divergence, rsi_div_bonus = detect_divergence(m15, 'RSI')
    macd_divergence, macd_div_bonus = detect_divergence(m15, 'MACD')
    
    divergence = rsi_divergence or macd_divergence
    divergence_bonus = max(rsi_div_bonus, macd_div_bonus)
    
    # V16.0 NOVOS: S/R
    sr_levels = detect_support_resistance(h1)
    sr_bonus = 0
    sr_touch = False
    if sr_levels:
        closest_sr = min(sr_levels, key=lambda x: abs(x['price'] - curr_h1['close']))
        if abs(closest_sr['price'] - curr_h1['close']) < (curr_h1['ATR'] * 0.5):
            sr_bonus = +15
            sr_touch = True
    
    # V16.0 NOVOS: Fibonacci
    fibs = calculate_fibonacci_levels(h1)
    fib_level, fib_bonus = check_fib_confluence(curr_h1['close'], fibs, curr_h1['ATR'])
    
    # V16.0 NOVOS: Perfect Alignment
    alignment_type, alignment_bonus = detect_perfect_alignment(curr_h4, curr_h1, curr_m15, bias_h4)
    
    # Padrões com score
    recent_patterns = curr_m15['patterns'] if 'patterns' in curr_m15.index else []
    pattern_score = curr_m15['pattern_score'] if 'pattern_score' in curr_m15.index else 0
    pattern_score = min(pattern_score, 15)  # Cap em 15
    
    # Detecção de setup (Dual Scoring)
    sig = "MONITORING"
    entry = curr_h1['close']
    sl = curr_h1['close']
    entry_type = "Wait"
    sl_reason = "Structural Pivot"
    trade_style = None
    setup_type = None
    
    # Bloqueia apenas volatilidade EXTREMA
    if vol_regime == "EXTREME_HIGH":
        sig = f"BLOCKED (VOL_{vol_regime})"
    
    # BULLISH SETUPS
    elif bias_h4 == "BULLISH":
        dist = abs(curr_h1['close'] - curr_h1['EMA_50'])
        is_near_value = dist < (curr_h1['ATR'] * 1.5)
        
        # Verifica divergência contrária
        if divergence == "BEARISH_DIVERGENCE":
            sig = "BLOCKED (BEARISH_DIVERGENCE)"
        else:
            # SWING TRADE
            if adx_h4 > 20 and (is_near_value or curr_h1['RSI'] < 45):
                sig = "LONG (SWING)"
                sl = detect_swing_level(h1, "BUY", atr_multiplier=1.5)
                entry_type = "Swing: Reteste de Tendência"
                trade_style = "SWING"
                setup_type = "SWING"
                
            # DAY TRADE
            elif adx_h4 > 15 and (curr_h1['close'] > curr_h1['EMA_20'] or len(recent_patterns) > 0):
                sig = "LONG (DAY)"
                sl = detect_swing_level(h1, "BUY", atr_multiplier=1.2)
                entry_type = "Day Trade: Pullback"
                trade_style = "DAY"
                setup_type = "DAY"
            
            # BREAKOUT (V16.0 NOVO)
            elif sr_touch and curr_h1['close'] > closest_sr['price']:
                sig = "LONG (BREAKOUT)"
                sl = closest_sr['price'] - (curr_h1['ATR'] * 1.0)
                entry_type = "Breakout de Resistência"
                trade_style = "BREAKOUT"
                setup_type = "BREAKOUT"
            
            if "LONG" in sig:
                if (entry - sl) > (3 * curr_h1['ATR']):
                    sl = entry - (2.5 * curr_h1['ATR'])
                    sl_reason = "Max ATR Limit"
    
    # BEARISH SETUPS
    elif bias_h4 == "BEARISH":
        dist = abs(curr_h1['close'] - curr_h1['EMA_50'])
        is_near_value = dist < (curr_h1['ATR'] * 1.5)
        
        if divergence == "BULLISH_DIVERGENCE":
            sig = "BLOCKED (BULLISH_DIVERGENCE)"
        else:
            # SWING TRADE
            if adx_h4 > 20 and (is_near_value or curr_h1['RSI'] > 55):
                sig = "SHORT (SWING)"
                sl = detect_swing_level(h1, "SELL", atr_multiplier=1.5)
                entry_type = "Swing: Reteste de Tendência"
                trade_style = "SWING"
                setup_type = "SWING"
                
            # DAY TRADE
            elif adx_h4 > 15 and (curr_h1['close'] < curr_h1['EMA_20'] or len(recent_patterns) > 0):
                sig = "SHORT (DAY)"
                sl = detect_swing_level(h1, "SELL", atr_multiplier=1.2)
                entry_type = "Day Trade: Pullback"
                trade_style = "DAY"
                setup_type = "DAY"
            
            # BREAKOUT
            elif sr_touch and curr_h1['close'] < closest_sr['price']:
                sig = "SHORT (BREAKOUT)"
                sl = closest_sr['price'] + (curr_h1['ATR'] * 1.0)
                entry_type = "Breakout de Suporte"
                trade_style = "BREAKOUT"
                setup_type = "BREAKOUT"
            
            if "SHORT" in sig:
                if (sl - entry) > (3 * curr_h1['ATR']):
                    sl = entry + (2.5 * curr_h1['ATR'])
                    sl_reason = "Max ATR Limit"
    
    # Lazy backtest (só se tem setup válido)
    if "BLOCKED" not in sig and sig != "MONITORING":
        sim = run_enhanced_backtest(h1, bias_h4)
    else:
        sim = {"WR": 0, "NET": 0, "DD": 0, "PF": 0, "SHARPE": 0, "SORTINO": 0, 
               "RECOVERY": 0, "MAX_CONS_WIN": 0, "MAX_CONS_LOSS": 0}
    
    # V16.0: Perfect Storm Detection
    # BB Compression: verifica se largura atual está abaixo da média dos últimos 20 períodos
    bb_width_avg = h1['BB_width'].tail(20).mean() if len(h1) >= 20 else h1['BB_width'].mean()
    bb_compression = curr_h1['BB_width'] < (bb_width_avg * 0.6)
    
    storm_data = {
        'adx': adx_h4,
        'momentum_score': momentum_score,
        'pattern_score': pattern_score,
        'divergence': divergence,
        'fib_confluence': fib_level is not None,
        'sr_touch': sr_touch,
        'perfect_alignment': alignment_type == "PERFECT_ALIGNMENT",
        'bb_compression': bb_compression
    }
    
    storm_level, storm_bonus, storm_criteria = calculate_perfect_storm_bonus(storm_data)
    
    # Se Perfect Storm, muda para setup especial
    if storm_level == "PERFECT_STORM" and "BLOCKED" not in sig and sig != "MONITORING":
        sig = sig.replace("LONG", "LONG (⭐PERFECT STORM⭐)").replace("SHORT", "SHORT (⭐PERFECT STORM⭐)")
        setup_type = "PERFECT_STORM"
    
    # Setup Score V16.0 (0-150)
    distance_from_ema50 = abs(curr_h1['close'] - curr_h1['EMA_50'])
    
    # Ajusta divergence_bonus baseado na direção
    if divergence:
        if ("LONG" in sig and divergence == "BULLISH_DIVERGENCE") or \
           ("SHORT" in sig and divergence == "BEARISH_DIVERGENCE"):
            final_divergence_bonus = abs(divergence_bonus)  # Bonus
        else:
            final_divergence_bonus = 0  # Já bloqueou antes
    else:
        final_divergence_bonus = 0
    
    score = calculate_setup_score_v16(
        adx=adx_h4,
        momentum_score=momentum_score,
        pattern_score=pattern_score,
        distance_from_ema50=distance_from_ema50,
        atr=curr_h1['ATR'],
        win_rate=sim['WR'],
        profit_factor=sim['PF'],
        divergence_bonus=final_divergence_bonus,
        fib_bonus=fib_bonus,
        sr_bonus=sr_bonus,
        alignment_bonus=alignment_bonus,
        storm_bonus=storm_bonus
    )
    
    # Filtros ajustados
    if setup_type == "PERFECT_STORM":
        min_score_required = 100  # Muito alto
        min_pf_required = 1.5
    elif setup_type == "BREAKOUT":
        min_score_required = 60
        min_pf_required = 1.4
    elif trade_style == "DAY":
        min_score_required = 40
        min_pf_required = 1.3
    else:  # SWING
        min_score_required = 70
        min_pf_required = 1.5
    
    if "BLOCKED" not in sig and sig != "MONITORING":
        if score.total < min_score_required or sim['NET'] <= 0 or sim['PF'] < min_pf_required:
            sig = f"BLOCKED (SCORE={score.total:.0f}, PF={sim['PF']})"
    
    # Targets dinâmicos
    risk = abs(entry - sl)
    if risk == 0: 
        risk = curr_h1['ATR']
    
    if setup_type == "PERFECT_STORM":
        # Perfect Storm: 1:5 e 1:10
        if "LONG" in sig:
            tp1 = entry + (5 * risk)
            tp2 = entry + (10 * risk)
        else:
            tp1 = entry - (5 * risk)
            tp2 = entry - (10 * risk)
        target_label_1 = "TP1 (1:5)"
        target_label_2 = "TP2 (1:10)"
        realize_pct_1 = 30
        realize_pct_2 = 70
        
    elif setup_type == "BREAKOUT":
        # Breakout: 1:3 e 1:7
        if "LONG" in sig:
            tp1 = entry + (3 * risk)
            tp2 = entry + (7 * risk)
        else:
            tp1 = entry - (3 * risk)
            tp2 = entry - (7 * risk)
        target_label_1 = "TP1 (1:3)"
        target_label_2 = "TP2 (1:7)"
        realize_pct_1 = 50
        realize_pct_2 = 50
        
    elif trade_style == "DAY":
        # Day Trade: 1:2 e 1:3
        if "LONG" in sig:
            tp1 = entry + (2 * risk)
            tp2 = entry + (3 * risk)
        else:
            tp1 = entry - (2 * risk)
            tp2 = entry - (3 * risk)
        target_label_1 = "TP1 (1:2)"
        target_label_2 = "TP2 (1:3)"
        realize_pct_1 = 60
        realize_pct_2 = 40
        
    else:  # SWING
        # Swing: 1:3 e 1:5
        if "LONG" in sig or "BUY" in sig:
            tp1 = entry + (3 * risk)
            tp2 = entry + (5 * risk)
        else:
            tp1 = entry - (3 * risk)
            tp2 = entry - (5 * risk)
        target_label_1 = "TP1 (1:3)"
        target_label_2 = "TP2 (1:5)"
        realize_pct_1 = 50
        realize_pct_2 = 50
    
    tp3 = tp1
    tp5 = tp2
    
    # Position sizing adaptativo V16.0
    position_size, position_value, position_note = adaptive_position_size(
        capital, risk_pct, entry, sl, vol_pct
    )
    
    # Kelly Criterion para Perfect Storm
    if setup_type == "PERFECT_STORM" and score.grade in ["S", "A++"]:
        kelly_pct = calculate_kelly_criterion(sim['WR'], 5.0, 1.0) * 100
        kelly_msg = f"🌟 Perfect Storm - Kelly sugere {kelly_pct:.1f}% de risco"
    elif score.grade == "A+":
        kelly_pct = calculate_kelly_criterion(sim['WR'], 5.0, 1.0) * 100
        kelly_msg = f"Kelly sugere {kelly_pct:.1f}% de risco"
    else:
        kelly_msg = ""
    
    # Charts
    show_levels = "SWING" in sig or "DAY" in sig or "BREAKOUT" in sig or "STORM" in sig
    img_h4 = plot_candles(h4, f"{name} - H4 (Tendência)", 
                          entry if show_levels else None,
                          sl if show_levels else None, 
                          tp3 if show_levels else None,
                          tp5 if show_levels else None, 
                          patterns=False)
    
    img_h1 = plot_candles(h1, f"{name} - H1 (Estrutura)", 
                          entry if show_levels else None,
                          sl if show_levels else None, 
                          tp3 if show_levels else None,
                          tp5 if show_levels else None, 
                          patterns=False)
    
    img_m15 = plot_candles(m15, f"{name} - M15 (Gatilho)", 
                           entry if show_levels else None,
                           sl if show_levels else None, 
                           tp3 if show_levels else None,
                           tp5 if show_levels else None, 
                           patterns=True)
    
    # Compilar confluências
    confluences = []
    if divergence:
        confluences.append(f"🔍 {divergence}")
    if fib_level:
        confluences.append(f"📐 Fibonacci {fib_level}")
    if sr_touch and sr_levels:
        confluences.append(f"🎯 S/R testado {closest_sr['touches']}x em {closest_sr['price']:.2f}")
    if alignment_type != "NO_ALIGNMENT":
        confluences.append(f"⭐ {alignment_type}")
    if storm_level:
        confluences.append(f"🌟 {storm_level}")
    
    # Criar dicionário de retorno
    result = {
        "FINAL_DECISION": sig,
        "TRADE_STYLE": trade_style or "N/A",
        "SETUP_TYPE": setup_type or "N/A",
        "SETUP_SCORE": float(round(score.total, 1)),
        "BASE_SCORE": float(round(score.base_total, 1)),
        "BONUS_SCORE": float(round(score.bonus_total, 1)),
        "SETUP_GRADE": score.grade,
        "ADX_SCORE": float(round(score.trend_strength, 1)),
        "MOMENTUM_SCORE": float(round(score.momentum_align, 1)),
        "PATTERN_SCORE": float(round(score.patterns, 1)),
        "VALUE_SCORE": float(round(score.value_zone, 1)),
        "HIST_SCORE": float(round(score.historical, 1)),
        "DIVERGENCE_BONUS": float(round(score.divergence_bonus, 1)),
        "FIB_BONUS": float(round(score.fib_bonus, 1)),
        "SR_BONUS": float(round(score.sr_bonus, 1)),
        "ALIGNMENT_BONUS": float(round(score.alignment_bonus, 1)),
        "STORM_BONUS": float(round(score.storm_bonus, 1)),
        "MARKET_STRUCTURE": structure,
        "VOL_REGIME": f"{vol_regime} ({vol_pct:.2f}%)",
        "PATTERNS_DETECTED": ", ".join(recent_patterns) if recent_patterns else "Nenhum",
        "DIVERGENCE": divergence or "Nenhuma",
        "FIB_LEVEL": fib_level or "N/A",
        "SR_LEVELS": int(len(sr_levels)),
        "ALIGNMENT_TYPE": alignment_type,
        "STORM_LEVEL": storm_level or "N/A",
        "STORM_CRITERIA": storm_criteria,
        "CONFLUENCES": confluences,
        "MOMENTUM_ALIGNMENT": f"{momentum_score}/3 timeframes",
        "ENTRY_TYPE": entry_type,
        "SL_REASON": sl_reason,
        "WIN_RATE": float(sim['WR']),
        "NET_PROFIT": float(sim['NET']),
        "MAX_DRAWDOWN": float(sim['DD']),
        "PROFIT_FACTOR": float(sim['PF']),
        "SHARPE_RATIO": float(sim['SHARPE']),
        "SORTINO_RATIO": float(sim['SORTINO']),
        "RECOVERY_FACTOR": float(sim['RECOVERY']),
        "MAX_CONS_WIN": int(sim['MAX_CONS_WIN']),
        "MAX_CONS_LOSS": int(sim['MAX_CONS_LOSS']),
        "MATH_ENTRY": float(round(entry, 2)),
        "MATH_SL": float(round(sl, 2)),
        "MATH_TP1": float(round(tp1, 2)),
        "MATH_TP2": float(round(tp2, 2)),
        "MATH_TP3": float(round(tp3, 2)),
        "MATH_TP5": float(round(tp5, 2)),
        "TARGET_LABEL_1": target_label_1,
        "TARGET_LABEL_2": target_label_2,
        "REALIZE_PCT_1": int(realize_pct_1),
        "REALIZE_PCT_2": int(realize_pct_2),
        "POSITION_SIZE": float(position_size),
        "POSITION_VALUE": float(position_value),
        "POSITION_NOTE": position_note,
        "KELLY_MSG": kelly_msg,
        "IMAGES": [img_h4, img_h1, img_m15],
        # Para Trade Management
        "ATR": float(curr_h1['ATR']),
        "INITIAL_RISK": float(risk)
    }
    
    return result

# ==============================================================================
# INTERFACE STREAMLIT V16.0
# ==============================================================================

st.sidebar.title("🚀 SI-APATECO V16.0 ULTRA")
if "GEMINI_API_KEY" in st.secrets: 
    api = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ API ATIVA")
else: 
    api = st.sidebar.text_input("CHAVE API GEMINI", type="password")

st.sidebar.divider()

capital = st.sidebar.number_input("💰 Capital ($)", min_value=100, value=10000, step=100)
risk_pct = st.sidebar.slider("📊 Risco Base (%)", min_value=0.5, max_value=3.0, value=1.0, step=0.1)

st.sidebar.divider()

# Modo de operação
operation_mode = st.sidebar.radio(
    "⚙️ Modo de Operação",
    ["🔍 Análise de Entrada", "📊 Monitoramento de Trade"]
)

st.sidebar.divider()
st.sidebar.info("""
**V16.0 ULTRA - NOVOS RECURSOS:**
- 🎯 Score 0-150 (base 100 + bonus 50)
- 🔍 Detecção de Divergências
- 📐 Fibonacci Automático
- 🎯 Suporte/Resistência
- ⭐ Perfect Alignment
- 🌟 Perfect Storm (6+ fatores)
- 💥 Breakout Detection
- 📊 **Trade Management Tempo Real**
- ⚡ Alertas de Reversão
- 🎯 Sugestões de Break-Even
""")

st.title("🚀 SI-APATECO SNIPER V16.0 ULTRA")
st.caption("Sistema Elite com Trade Management em Tempo Real | Score 0-150 | Perfect Storm Detection")

with st.spinner("Carregando ativos..."):
    assets = get_assets()

if not assets:
    st.error("❌ FALHA NA CONEXÃO")
    st.stop()

# ==============================================================================
# MODO 1: ANÁLISE DE ENTRADA
# ==============================================================================

if operation_mode == "🔍 Análise de Entrada":
    c1, c2 = st.columns([1, 2])
    
    with c1:
        target = st.selectbox("🎯 SELECIONAR ATIVO", list(assets.keys()))
        st.markdown("### 🔬 ANÁLISE TRI-FORCE V16.0")
        st.caption("Com detecção de divergências, S/R, Fibonacci e Perfect Storm")
        st.write("")
        run = st.button("🚀 EXECUTAR ANÁLISE COMPLETA", use_container_width=True)
    
    with c2:
        if run:
            if not api:
                st.error("⚠️ CHAVE API NECESSÁRIA")
                st.stop()
            
            status = st.status("🛸 INICIALIZANDO V16.0 ULTRA...", expanded=True)
            
            status.write("1️⃣ Buscando dados Multi-Timeframe...")
            h1, h4, m15, err = asyncio.run(fetch_tri_force(assets[target]))
            
            if err:
                status.update(state='error', label="❌ FALHA")
                st.error(err)
                st.stop()
            
            status.write("2️⃣ Detectando Divergências RSI/MACD...")
            status.write("3️⃣ Calculando Fibonacci + S/R...")
            status.write("4️⃣ Verificando Perfect Alignment...")
            status.write("5️⃣ Analisando Perfect Storm...")
            
            data = sniper_core_v16_ultra(target, h1, h4, m15, capital, risk_pct)
            
            generated_images = data.pop("IMAGES")
            
            status.write("6️⃣ Análise Visual IA...")
            genai.configure(api_key=api)
            
            # Converter numpy para tipos Python nativos
            data_converted = convert_numpy_to_python(data)
            
            try:
                model = genai.GenerativeModel("models/gemini-1.5-pro", safety_settings=SAFETY_SETTINGS)
                ai_response = model.generate_content(
                    [SYSTEM_PROMPT, f"DADOS V16.0: {json.dumps(data_converted)}"] + generated_images
                ).text
                status.update(label="✅ ANÁLISE V16.0 COMPLETA", state="complete")
            except Exception as e:
                st.error(f"Erro IA: {e}")
                ai_response = "Análise IA indisponível. Usando apenas dados matemáticos."
            
            # DISPLAY RESULTS
            grade = data['SETUP_GRADE']
            score = data['SETUP_SCORE']
            base_score = data['BASE_SCORE']
            bonus_score = data['BONUS_SCORE']
            trade_style = data.get('TRADE_STYLE', 'N/A')
            setup_type = data.get('SETUP_TYPE', 'N/A')
            
            # Grade emoji e classe
            if grade == "S":
                grade_class = "score-s"
                grade_emoji = "👑"
            elif grade == "A++":
                grade_class = "score-a-plus-plus"
                grade_emoji = "🏆"
            elif grade == "A+":
                grade_class = "score-a-plus"
                grade_emoji = "💎"
            elif grade == "A":
                grade_class = "score-a"
                grade_emoji = "⭐"
            elif grade == "B":
                grade_class = "score-b"
                grade_emoji = "📊"
            else:
                grade_class = "score-c"
                grade_emoji = "⚠️"
            
            # Style emoji
            if setup_type == "PERFECT_STORM":
                style_emoji = "🌟"
                style_color = "#a855f7"
            elif setup_type == "BREAKOUT":
                style_emoji = "💥"
                style_color = "#f59e0b"
            elif trade_style == "SWING":
                style_emoji = "📈"
                style_color = "#10b981"
            elif trade_style == "DAY":
                style_emoji = "⚡"
                style_color = "#3b82f6"
            else:
                style_emoji = "⏸️"
                style_color = "#6b7280"
            
            st.markdown(f"""
            <div style='text-align: center; padding: 25px; background: rgba(251, 191, 36, 0.1); border: 3px solid #fbbf24; border-radius: 15px; margin-bottom: 25px;'>
                <h1 style='margin: 0;'>{grade_emoji} GRADE: <span class='{grade_class}'>{grade}</span></h1>
                <p style='font-size: 28px; margin: 15px 0;'><strong>SCORE: {score}/150</strong></p>
                <p style='font-size: 20px; margin: 10px 0;'>Base: {base_score}/100 | Bonus: +{bonus_score}/50</p>
                <p style='font-size: 24px; margin: 15px 0 0 0; color: {style_color};'>{style_emoji} <strong>{setup_type}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Perfect Storm Alert
            if setup_type == "PERFECT_STORM":
                st.success("🌟🌟🌟 **PERFECT STORM DETECTADO!** 🌟🌟🌟")
                st.info(f"**Critérios Atingidos:** {', '.join(data['STORM_CRITERIA'])}")
                st.balloons()
            
            # Métricas
            st.subheader("📊 MÉTRICAS DE PERFORMANCE")
            
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Win Rate", f"{data['WIN_RATE']}%")
            m2.metric("Profit Factor", f"{data['PROFIT_FACTOR']}")
            m3.metric("Sharpe Ratio", f"{data['SHARPE_RATIO']}")
            m4.metric("Sortino Ratio", f"{data['SORTINO_RATIO']}")
            m5.metric("Max DD", f"{data['MAX_DRAWDOWN']}R")
            
            # Breakdown V16.0
            st.subheader("🔬 BREAKDOWN COMPLETO V16.0")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Score Base (100 pts):**")
                base_data = pd.DataFrame([{
                    "Componente": "Força Tendência (ADX)",
                    "Score": f"{data['ADX_SCORE']}/25"
                }, {
                    "Componente": "Momentum Alignment",
                    "Score": f"{data['MOMENTUM_SCORE']}/20"
                }, {
                    "Componente": "Padrões Candlestick",
                    "Score": f"{data['PATTERN_SCORE']}/15"
                }, {
                    "Componente": "Zona de Valor",
                    "Score": f"{data['VALUE_SCORE']}/15"
                }, {
                    "Componente": "Edge Histórico",
                    "Score": f"{data['HIST_SCORE']}/25"
                }])
                st.dataframe(base_data, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**✨ Bonus Confluências (50 pts):**")
                bonus_data = pd.DataFrame([{
                    "Confluência": "Divergência",
                    "Bonus": f"+{data['DIVERGENCE_BONUS']}"
                }, {
                    "Confluência": "Fibonacci",
                    "Bonus": f"+{data['FIB_BONUS']}"
                }, {
                    "Confluência": "S/R",
                    "Bonus": f"+{data['SR_BONUS']}"
                }, {
                    "Confluência": "Perfect Alignment",
                    "Bonus": f"+{data['ALIGNMENT_BONUS']}"
                }, {
                    "Confluência": "Perfect Storm",
                    "Bonus": f"+{data['STORM_BONUS']}"
                }])
                st.dataframe(bonus_data, use_container_width=True, hide_index=True)
            
            # Confluências Detectadas
            if data['CONFLUENCES']:
                st.subheader("🔥 CONFLUÊNCIAS DETECTADAS")
                for conf in data['CONFLUENCES']:
                    st.markdown(f"- {conf}")
            
            # Sinal
            st.divider()
            
            decision = data['FINAL_DECISION']
            if "SWING" in decision or "DAY" in decision or "BREAKOUT" in decision or "STORM" in decision:
                st.success(f"✅ **SINAL CONFIRMADO:** {decision}")
                if setup_type == "PERFECT_STORM":
                    st.balloons()
            elif "BLOCKED" in decision:
                st.error(f"🛑 **BLOQUEADO:** {decision}")
            else:
                st.warning(f"⏸️ **STATUS:** {decision}")
            
            # Plano de Execução
            if "SWING" in decision or "DAY" in decision or "BREAKOUT" in decision or "STORM" in decision:
                st.subheader("📋 PLANO DE EXECUÇÃO V16.0")
                
                plan_data = pd.DataFrame([{
                    "Parâmetro": "Entrada",
                    "Valor": data['MATH_ENTRY'],
                    "Observações": data['ENTRY_TYPE']
                }, {
                    "Parâmetro": "Stop Loss",
                    "Valor": data['MATH_SL'],
                    "Observações": data['SL_REASON']
                }, {
                    "Parâmetro": data['TARGET_LABEL_1'],
                    "Valor": data['MATH_TP1'],
                    "Observações": f"Realizar {data['REALIZE_PCT_1']}%"
                }, {
                    "Parâmetro": data['TARGET_LABEL_2'],
                    "Valor": data['MATH_TP2'],
                    "Observações": f"Realizar {data['REALIZE_PCT_2']}% + trailing"
                }, {
                    "Parâmetro": "Tamanho Posição",
                    "Valor": f"{data['POSITION_SIZE']} unidades",
                    "Observações": f"${data['POSITION_VALUE']} - {data['POSITION_NOTE']}"
                }])
                
                st.dataframe(plan_data, use_container_width=True, hide_index=True)
                
                if data['KELLY_MSG']:
                    st.info(f"💡 {data['KELLY_MSG']}")
            
            # Contexto
            st.subheader("🌍 CONTEXTO DE MERCADO")
            
            ctx1, ctx2, ctx3, ctx4 = st.columns(4)
            with ctx1:
                st.metric("Estrutura", data['MARKET_STRUCTURE'])
            with ctx2:
                st.metric("Volatilidade", data['VOL_REGIME'])
            with ctx3:
                st.metric("Divergência", data['DIVERGENCE'])
            with ctx4:
                st.metric("Fib Nível", data['FIB_LEVEL'])
            
            ctx5, ctx6, ctx7, ctx8 = st.columns(4)
            with ctx5:
                st.metric("Padrões", data['PATTERNS_DETECTED'] or "Nenhum")
            with ctx6:
                st.metric("Níveis S/R", f"{data['SR_LEVELS']} detectados")
            with ctx7:
                st.metric("Alignment", data['ALIGNMENT_TYPE'])
            with ctx8:
                st.metric("Momentum", data['MOMENTUM_ALIGNMENT'])
            
            # Gráficos
            st.divider()
            st.subheader("📊 ANÁLISE GRÁFICA")
            
            tabs = st.tabs(["H4 - Tendência", "H1 - Estrutura", "M15 - Gatilho"])
            
            with tabs[0]:
                st.image(generated_images[0], use_column_width=True)
            
            with tabs[1]:
                st.image(generated_images[1], use_column_width=True)
            
            with tabs[2]:
                st.image(generated_images[2], use_column_width=True)
            
            # IA
            st.divider()
            st.subheader("🤖 ANÁLISE VISUAL IA")
            st.markdown(ai_response)

# ==============================================================================
# MODO 2: MONITORAMENTO DE TRADE EM TEMPO REAL
# ==============================================================================

elif operation_mode == "📊 Monitoramento de Trade":
    st.markdown("### 📊 TRADE MANAGEMENT EM TEMPO REAL")
    st.caption("Monitora trade ativo e alerta sobre reversões, break-even e realização parcial")
    
    col1, col2 = st.columns(2)
    
    with col1:
        monitor_symbol = st.selectbox("🎯 Ativo do Trade", list(assets.keys()))
        monitor_direction = st.selectbox("📈 Direção", ["LONG", "SHORT"])
        
    with col2:
        monitor_entry = st.number_input("💰 Preço de Entrada", min_value=0.0, value=1000.0, step=0.1)
        monitor_sl = st.number_input("🛑 Stop Loss", min_value=0.0, value=990.0, step=0.1)
        
    col3, col4 = st.columns(2)
    
    with col3:
        monitor_tp1 = st.number_input("🎯 TP1", min_value=0.0, value=1030.0, step=0.1)
        
    with col4:
        monitor_tp2 = st.number_input("🎯 TP2", min_value=0.0, value=1050.0, step=0.1)
    
    start_monitoring = st.button("🚀 INICIAR MONITORAMENTO", use_container_width=True)
    
    if start_monitoring:
        st.info("🔄 **Monitoramento Ativo** - Atualizando a cada 5 segundos...")
        
        # Criar trade ativo
        active_trade = ActiveTrade(
            symbol=monitor_symbol,
            direction=monitor_direction,
            entry_price=monitor_entry,
            current_price=monitor_entry,
            sl=monitor_sl,
            tp1=monitor_tp1,
            tp2=monitor_tp2,
            entry_time=datetime.now(),
            atr=abs(monitor_entry - monitor_sl) / 2.5,  # Estimativa
            initial_risk=abs(monitor_entry - monitor_sl)
        )
        
        if monitor_direction == "LONG":
            active_trade.highest_price = monitor_entry
        else:
            active_trade.lowest_price = monitor_entry
        
        # Placeholders
        status_placeholder = st.empty()
        metrics_placeholder = st.empty()
        alerts_placeholder = st.empty()
        recommendations_placeholder = st.empty()
        chart_placeholder = st.empty()
        
        # Loop de monitoramento
        for iteration in range(120):  # 10 minutos (120 x 5s)
            try:
                # Buscar preço atual
                h1, h4, m15, err = asyncio.run(fetch_tri_force(assets[monitor_symbol]))
                
                if not err and m15:
                    m15_df = indicators(prep_df(m15))
                    current_price = m15_df['close'].iloc[-1]
                    
                    # Atualizar trade
                    active_trade.update_price(current_price)
                    
                    # Análise de saúde
                    health_analysis = analyze_trade_health(active_trade, m15_df)
                    
                    # Status Card
                    health_class = health_analysis['health_color']
                    health_status = health_analysis['health_status']
                    health_score = health_analysis['health_score']
                    current_r = health_analysis['current_r']
                    
                    status_placeholder.markdown(f"""
                    <div class='{health_class}'>
                        <h3>🏥 SAÚDE DO TRADE: {health_status} ({health_score}/100)</h3>
                        <p>R Atual: <strong>{current_r:+.2f}R</strong> | P&L: <strong>${active_trade.get_unrealized_pl():+.2f}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Métricas
                    with metrics_placeholder.container():
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("Preço Atual", f"{current_price:.2f}")
                        m2.metric("Entrada", f"{active_trade.entry_price:.2f}")
                        m3.metric("Stop", f"{active_trade.sl:.2f}")
                        m4.metric("R Atual", f"{current_r:+.2f}R")
                        
                        if active_trade.direction == "LONG":
                            m5.metric("Máxima", f"{active_trade.highest_price:.2f}")
                        else:
                            m5.metric("Mínima", f"{active_trade.lowest_price:.2f}")
                    
                    # Alertas
                    if health_analysis['alerts']:
                        with alerts_placeholder.container():
                            st.subheader("⚠️ ALERTAS")
                            for alert in health_analysis['alerts']:
                                st.warning(alert)
                    
                    # Recomendações
                    if health_analysis['recommendations']:
                        with recommendations_placeholder.container():
                            st.subheader("💡 RECOMENDAÇÕES")
                            for rec in health_analysis['recommendations']:
                                priority_color = {
                                    'CRITICAL': '🔴',
                                    'HIGH': '🟡',
                                    'MEDIUM': '🟢'
                                }.get(rec['priority'], '⚪')
                                
                                st.info(f"{priority_color} **{rec['type']}**: {rec['action']}")
                    
                    # Chart (simplificado - só últimas 50 velas)
                    with chart_placeholder.container():
                        recent_m15 = m15_df.tail(50)
                        chart_img = plot_candles(
                            recent_m15,
                            f"{monitor_symbol} - M15 (Monitoramento)",
                            entry=active_trade.entry_price,
                            sl=active_trade.sl,
                            tp1=active_trade.tp1,
                            tp2=active_trade.tp2,
                            patterns=True
                        )
                        st.image(chart_img, use_column_width=True)
                
                time.sleep(5)  # Atualiza a cada 5 segundos
                
            except Exception as e:
                st.error(f"Erro no monitoramento: {e}")
                break
        
        st.success("✅ Monitoramento concluído (10 minutos)")
