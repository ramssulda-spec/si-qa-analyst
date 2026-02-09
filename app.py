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
from typing import Dict, List, Tuple
from dataclasses import dataclass

# ==============================================================================
# 1. VISUAL SETUP (SNIPER TRI-VISION V15.0)
# ==============================================================================
st.set_page_config(
    page_title="SI-APATECO SNIPER V15.0",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    .score-a-plus {
        color: #10b981;
        font-weight: 900;
        font-size: 28px;
    }
    .score-a {
        color: #3b82f6;
        font-weight: 900;
        font-size: 26px;
    }
    .score-b {
        color: #fbbf24;
        font-weight: 900;
        font-size: 24px;
    }
    .score-c {
        color: #ef4444;
        font-weight: 900;
        font-size: 22px;
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
# 2. ENHANCED PROMPT - V15.0
# ==============================================================================
SYSTEM_PROMPT = """
ROLE: ELITE SWING TRADE ANALYST V15.0 [Gemini 3 Pro]
Mission: Identify Grade A+ Multi-Timeframe Confluence with 1:5 Payoff Potential

**ENHANCED INPUT DATA:**
1. **Math Core:** Trend Direction, ADX Strength, Setup Score (0-100), Pattern Signals
2. **Visual Triad (M15, H1, H4):** Confirma timing, estrutura e momentum alignment
3. **Market Structure:** Swing points, BOS (Break of Structure), trend classification
4. **Candlestick Patterns:** Pin bars, engulfing, inside bars detectados
5. **Volatility Regime:** LOW/MEDIUM/HIGH/EXTREME classification
6. **Momentum Alignment:** MACD score across 3 timeframes

**ANALYSIS PROTOCOL (FRACTAL ALIGNMENT V2.0):**
1. **H4 Chart:** Major Supply/Demand? Trend strength (ADX)? Market structure (HH/HL or LH/LL)?
2. **H1 Chart:** Internal structure aligned? Support/Resistance levels? Value zone (EMA 50)?
3. **M15 Chart:** Entry trigger (Candlestick pattern)? MACD confirmation? Volume?
4. **Momentum Check:** All 3 timeframes MACD aligned? Any divergences?
5. **Pattern Confluence:** Multiple candlestick patterns stacking at same level?
6. **Volatility Filter:** Regime suitable for 1:5 targets? Not too extreme/too low?

**OUTPUT FORMAT:**

## 🎯 SNIPER VERDICT: [ {FINAL_DECISION} ]
**Setup Grade:** {SETUP_GRADE} ({SETUP_SCORE}/100)
**Ativo:** {ASSET_NAME} | **Target Payoff:** 1:5 ({MATH_TP5})

### 📊 SETUP QUALITY METRICS
*   **Score Breakdown:**
    - Trend Strength (ADX): {ADX_SCORE}/25
    - Momentum Alignment: {MOMENTUM_SCORE}/20
    - Candlestick Patterns: {PATTERN_SCORE}/15
    - Value Zone: {VALUE_SCORE}/15
    - Historical Edge: {HIST_SCORE}/25
    - **TOTAL: {SETUP_SCORE}/100**

*   **Volatility Regime:** {VOL_REGIME}
*   **Market Structure:** {STRUCTURE_TYPE}
*   **Detected Patterns:** {PATTERNS_DETECTED}

### 👁️ TRI-FORCE VISUAL ANALYSIS
*   **H4 (Macro):** {H4 analysis - trend, ADX, major S/D zones, structure}
*   **H1 (Structure):** {H1 analysis - pivots, S/R levels, value zone, BOS}
*   **M15 (Trigger):** {M15 analysis - price action, patterns, volume, MACD}

### 🎯 EXECUTION PLAN
| Order | Level | Notes |
| :--- | :--- | :--- |
| **ENTRY** | **{MATH_ENTRY}** | *{ENTRY_TYPE}* |
| **STOP** | **{MATH_SL}** | *{SL_REASON}* |
| **TP 1** | **{MATH_TP3}** | *Bank 50% here (1:3)* |
| **TP 2** | **{MATH_TP5}** | *Let it run (1:5 with Trailing)* |
| **Position Size** | **{POSITION_SIZE}** | *{POSITION_PCT}% capital risk* |

*Sniper Insight:* {Why does fractal alignment + pattern confluence + momentum score justify this Grade {SETUP_GRADE} setup? What's your confidence level (High/Medium/Low)?}
"""

# ==============================================================================
# 3. DERIV NETWORK - OPTIMIZED
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

# ==============================================================================
# 4. ENHANCED INDICATORS & PATTERN DETECTION - V15.0
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']: 
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    return df

def calculate_adx(df, window=14):
    """Calculate ADX (Average Directional Index)"""
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

def detect_pin_bar(row, prev_row):
    """Detect pin bar pattern"""
    body = abs(row['close'] - row['open'])
    total_range = row['high'] - row['low']
    
    if total_range == 0:
        return None
    
    body_pct = body / total_range
    upper_wick = row['high'] - max(row['open'], row['close'])
    lower_wick = min(row['open'], row['close']) - row['low']
    
    # Bullish pin bar: long lower wick, small body
    if lower_wick > body * 2 and body_pct < 0.4 and upper_wick < body:
        return "PIN_BULLISH"
    # Bearish pin bar: long upper wick, small body
    elif upper_wick > body * 2 and body_pct < 0.4 and lower_wick < body:
        return "PIN_BEARISH"
    
    return None

def detect_engulfing(row, prev_row):
    """Detect engulfing pattern"""
    curr_body_top = max(row['open'], row['close'])
    curr_body_bottom = min(row['open'], row['close'])
    prev_body_top = max(prev_row['open'], prev_row['close'])
    prev_body_bottom = min(prev_row['open'], prev_row['close'])
    
    # Bullish engulfing
    if (row['close'] > row['open'] and prev_row['close'] < prev_row['open'] and
        curr_body_bottom < prev_body_bottom and curr_body_top > prev_body_top):
        return "ENGULF_BULLISH"
    # Bearish engulfing
    elif (row['close'] < row['open'] and prev_row['close'] > prev_row['open'] and
          curr_body_bottom < prev_body_bottom and curr_body_top > prev_body_top):
        return "ENGULF_BEARISH"
    
    return None

def detect_inside_bar(row, prev_row):
    """Detect inside bar (consolidation)"""
    if row['high'] <= prev_row['high'] and row['low'] >= prev_row['low']:
        return "INSIDE_BAR"
    return None

def detect_doji(row):
    """Detect doji pattern (indecision)"""
    body = abs(row['close'] - row['open'])
    total_range = row['high'] - row['low']
    
    if total_range > 0 and body / total_range < 0.1:
        return "DOJI"
    return None

def detect_patterns(df):
    """Detect all candlestick patterns"""
    patterns = []
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        pattern_list = []
        
        pin = detect_pin_bar(curr, prev)
        if pin: pattern_list.append(pin)
        
        eng = detect_engulfing(curr, prev)
        if eng: pattern_list.append(eng)
        
        inside = detect_inside_bar(curr, prev)
        if inside: pattern_list.append(inside)
        
        doji = detect_doji(curr)
        if doji: pattern_list.append(doji)
        
        patterns.append(pattern_list if pattern_list else [])
    
    df['patterns'] = [[] ] + patterns  # First candle has no patterns
    return df

def detect_swing_points(df, window=5):
    """Detect swing highs and lows"""
    df['swing_high'] = df['high'] == df['high'].rolling(window=window, center=True).max()
    df['swing_low'] = df['low'] == df['low'].rolling(window=window, center=True).min()
    return df

def classify_market_structure(df):
    """Classify market structure: UPTREND, DOWNTREND, RANGE"""
    # Get swing points
    swing_highs = df[df['swing_high']]['high'].tail(3)
    swing_lows = df[df['swing_low']]['low'].tail(3)
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "INSUFFICIENT_DATA"
    
    # Check for higher highs and higher lows (uptrend)
    hh = swing_highs.iloc[-1] > swing_highs.iloc[-2]
    hl = swing_lows.iloc[-1] > swing_lows.iloc[-2]
    
    # Check for lower lows and lower highs (downtrend)
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
    """Calculate volatility regime using ATR%"""
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
    """Calculate all technical indicators"""
    # EMAs
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(span=14, adjust=False).mean()
    avg_loss = loss.ewm(span=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    df['tr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = df['tr'].ewm(span=14, adjust=False).mean()
    
    # ADX
    df = calculate_adx(df)
    
    # MACD
    df = calculate_macd(df)
    
    # Bollinger Bands
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
    df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
    df['BB_width'] = ((df['BB_upper'] - df['BB_lower']) / df['BB_middle']) * 100
    
    # Pattern detection
    df = detect_patterns(df)
    
    # Swing points and structure
    df = detect_swing_points(df)
    
    df.dropna(inplace=True)
    return df

# ==============================================================================
# 5. MOMENTUM ALIGNMENT SYSTEM
# ==============================================================================

def check_momentum_alignment(h4_df, h1_df, m15_df, direction):
    """Check if MACD is aligned across all timeframes"""
    score = 0
    
    h4_macd = h4_df['MACD'].iloc[-1]
    h1_macd = h1_df['MACD'].iloc[-1]
    m15_macd = m15_df['MACD'].iloc[-1]
    
    if direction == "BULLISH":
        if h4_macd > 0: score += 1
        if h1_macd > 0: score += 1
        if m15_macd > 0: score += 1
    else:  # BEARISH
        if h4_macd < 0: score += 1
        if h1_macd < 0: score += 1
        if m15_macd < 0: score += 1
    
    return score  # 0-3

# ==============================================================================
# 6. SETUP SCORING SYSTEM (0-100)
# ==============================================================================

@dataclass
class SetupScore:
    trend_strength: float  # 0-25
    momentum_align: float  # 0-20
    patterns: float        # 0-15
    value_zone: float      # 0-15
    historical: float      # 0-25
    total: float           # 0-100
    grade: str             # A+, A, B, C

def calculate_setup_score(adx, momentum_score, patterns_detected, distance_from_ema50, 
                          atr, win_rate, profit_factor):
    """Calculate comprehensive setup score (0-100)"""
    
    # 1. Trend Strength (ADX) - 25 points
    if adx > 25:
        trend_score = 25
    elif adx > 15:
        trend_score = 15
    else:
        trend_score = 0
    
    # 2. Momentum Alignment - 20 points (0-3 timeframes aligned)
    momentum_score_pts = (momentum_score / 3) * 20
    
    # 3. Candlestick Patterns - 15 points (each pattern = 5pts, max 3)
    pattern_score = min(len(patterns_detected) * 5, 15)
    
    # 4. Value Zone - 15 points (proximity to EMA50)
    dist_ratio = distance_from_ema50 / atr
    if dist_ratio < 0.5:
        value_score = 15
    elif dist_ratio < 1.0:
        value_score = 10
    elif dist_ratio < 1.5:
        value_score = 5
    else:
        value_score = 0
    
    # 5. Historical Performance - 25 points
    hist_score = min((win_rate * 0.15) + (profit_factor * 5), 25)
    
    total = trend_score + momentum_score_pts + pattern_score + value_score + hist_score
    
    # Assign grade
    if total >= 90:
        grade = "A+"
    elif total >= 70:
        grade = "A"
    elif total >= 50:
        grade = "B"
    else:
        grade = "C"
    
    return SetupScore(
        trend_strength=trend_score,
        momentum_align=momentum_score_pts,
        patterns=pattern_score,
        value_zone=value_score,
        historical=hist_score,
        total=total,
        grade=grade
    )

# ==============================================================================
# 7. ENHANCED BACKTEST WITH WALK-FORWARD & ADVANCED METRICS
# ==============================================================================

def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """Calculate Sharpe Ratio"""
    if len(returns) < 2:
        return 0
    excess_returns = returns - risk_free_rate
    if excess_returns.std() == 0:
        return 0
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

def calculate_sortino_ratio(returns, risk_free_rate=0.0):
    """Calculate Sortino Ratio (only downside volatility)"""
    if len(returns) < 2:
        return 0
    excess_returns = returns - risk_free_rate
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0
    return (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)

def run_enhanced_backtest(df, trend_dir):
    """
    Enhanced backtest with walk-forward validation and advanced metrics
    """
    # Split data: 70% training, 30% validation
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
    
    start_idx = max(200, split_idx)  # Use validation period only
    
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
    
    # Calculate metrics
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
    """Find swing low/high for stop loss placement"""
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
# 8. POSITION SIZING CALCULATOR
# ==============================================================================

def calculate_position_size(capital, risk_pct, entry, sl):
    """Calculate position size based on fixed risk percentage"""
    risk_amount = capital * (risk_pct / 100)
    risk_per_unit = abs(entry - sl)
    
    if risk_per_unit == 0:
        return 0, 0
    
    position_size = risk_amount / risk_per_unit
    position_value = position_size * entry
    
    return round(position_size, 2), round(position_value, 2)

def calculate_kelly_criterion(win_rate, avg_win, avg_loss):
    """Calculate Kelly Criterion for optimal position sizing"""
    if avg_loss == 0:
        return 0
    
    win_rate_decimal = win_rate / 100
    loss_rate = 1 - win_rate_decimal
    
    kelly = (win_rate_decimal * avg_win - loss_rate * avg_loss) / avg_loss
    
    # Use half-Kelly for safety
    return max(0, min(kelly * 0.5, 0.1))  # Cap at 10%

# ==============================================================================
# 9. CHART PLOTTING WITH ENHANCED VISUALS
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp3=None, tp5=None, patterns=None):
    """Enhanced candlestick chart with pattern markers"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
    
    # Candlesticks on main chart
    for i in range(len(df)):
        color = 'green' if df['open'].iloc[i] < df['close'].iloc[i] else 'red'
        ax1.plot([df.index[i], df.index[i]], [df['low'].iloc[i], df['high'].iloc[i]], 
                color=color, linewidth=1)
        ax1.plot([df.index[i], df.index[i]], [df['open'].iloc[i], df['close'].iloc[i]], 
                color=color, linewidth=4)
    
    # EMAs
    ax1.plot(df.index, df['EMA_20'], label='EMA 20', color='cyan', linestyle='--', alpha=0.7)
    ax1.plot(df.index, df['EMA_50'], label='EMA 50', color='orange', linestyle='--', alpha=0.7)
    ax1.plot(df.index, df['EMA_200'], label='EMA 200', color='purple', linestyle='-', alpha=0.5)
    
    # Bollinger Bands
    ax1.plot(df.index, df['BB_upper'], color='gray', linestyle=':', alpha=0.5)
    ax1.plot(df.index, df['BB_lower'], color='gray', linestyle=':', alpha=0.5)
    
    # Entry, SL, TPs
    if entry: ax1.axhline(y=entry, color='cyan', linestyle='-', label='Entry', linewidth=2)
    if sl: ax1.axhline(y=sl, color='red', linestyle='-', label='Stop Loss', linewidth=2)
    if tp3: ax1.axhline(y=tp3, color='lime', linestyle='--', label='TP1 (1:3)', linewidth=2)
    if tp5: ax1.axhline(y=tp5, color='green', linestyle='-', label='TP2 (1:5)', linewidth=2)
    
    # Pattern markers
    if patterns and 'patterns' in df.columns:
        last_patterns = df['patterns'].iloc[-1]
        if last_patterns:
            pattern_str = ", ".join(last_patterns)
            ax1.text(df.index[-1], df['high'].iloc[-1], f" {pattern_str}", 
                    fontsize=8, color='yellow', fontweight='bold')
    
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # MACD histogram on bottom chart
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

# ==============================================================================
# 10. ENHANCED SNIPER CORE - V15.0
# ==============================================================================

def sniper_core_v15(name, h1_raw, h4_raw, m15_raw, capital=10000, risk_pct=1.0):
    """Enhanced sniper core with all V15.0 features"""
    
    # Prepare dataframes
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = indicators(prep_df(m15_raw))
    
    curr_h1 = h1.iloc[-1]
    curr_h4 = h4.iloc[-1]
    curr_m15 = m15.iloc[-1]
    
    # 1. Determine bias from H4
    bias_h4 = "BULLISH" if curr_h4['close'] > curr_h4['EMA_200'] else "BEARISH"
    adx_h4 = curr_h4['ADX']
    adx_strong = adx_h4 > 20
    
    # 2. Market structure classification
    structure = classify_market_structure(h1)
    
    # 3. Volatility regime
    vol_regime, vol_pct = calculate_volatility_regime(h1)
    
    # 4. Momentum alignment check
    momentum_score = check_momentum_alignment(h4, h1, m15, bias_h4)
    
    # 5. Pattern detection on M15
    recent_patterns = curr_m15['patterns'] if 'patterns' in curr_m15.index else []
    
    # 6. Setup detection
    sig = "MONITORING"
    entry = curr_h1['close']
    sl = curr_h1['close']
    entry_type = "Wait"
    sl_reason = "Structural Pivot"
    
    # Filter: Volatility must be in acceptable range
    if vol_regime in ["EXTREME_HIGH", "VERY_LOW"]:
        sig = f"BLOCKED (VOL_{vol_regime})"
    elif bias_h4 == "BULLISH" and adx_strong:
        dist = abs(curr_h1['close'] - curr_h1['EMA_50'])
        is_value = dist < (curr_h1['ATR'] * 1.2)
        
        if is_value or curr_h1['RSI'] < 45:
            sig = "LONG (SWING)"
            sl = detect_swing_level(h1, "BUY", atr_multiplier=1.5)
            entry_type = "Trend Retest (Discount)"
            
            if (entry - sl) > (3 * curr_h1['ATR']):
                sl = entry - (2.5 * curr_h1['ATR'])
                sl_reason = "Max ATR Limit"
                
    elif bias_h4 == "BEARISH" and adx_strong:
        dist = abs(curr_h1['close'] - curr_h1['EMA_50'])
        is_value = dist < (curr_h1['ATR'] * 1.2)
        
        if is_value or curr_h1['RSI'] > 55:
            sig = "SHORT (SWING)"
            sl = detect_swing_level(h1, "SELL", atr_multiplier=1.5)
            entry_type = "Trend Retest (Premium)"
            
            if (sl - entry) > (3 * curr_h1['ATR']):
                sl = entry + (2.5 * curr_h1['ATR'])
                sl_reason = "Max ATR Limit"
    
    # 7. Run backtest
    sim = run_enhanced_backtest(h1, bias_h4)
    
    # 8. Calculate setup score
    distance_from_ema50 = abs(curr_h1['close'] - curr_h1['EMA_50'])
    score = calculate_setup_score(
        adx=adx_h4,
        momentum_score=momentum_score,
        patterns_detected=recent_patterns,
        distance_from_ema50=distance_from_ema50,
        atr=curr_h1['ATR'],
        win_rate=sim['WR'],
        profit_factor=sim['PF']
    )
    
    # Block if score too low or negative backtest
    if score.total < 50 or sim['NET'] <= 0 or sim['PF'] < 1.5:
        sig = f"BLOCKED (SCORE={score.total:.0f}, PF={sim['PF']})"
    
    # 9. Calculate targets
    risk = abs(entry - sl)
    if risk == 0: 
        risk = curr_h1['ATR']
    
    if "LONG" in sig or "BUY" in sig:
        tp3 = entry + (3 * risk)
        tp5 = entry + (5 * risk)
    else:
        tp3 = entry - (3 * risk)
        tp5 = entry - (5 * risk)
    
    # 10. Position sizing
    position_size, position_value = calculate_position_size(capital, risk_pct, entry, sl)
    
    # Optional: Kelly Criterion for Grade A+
    if score.grade == "A+":
        kelly_pct = calculate_kelly_criterion(sim['WR'], 5.0, 1.0) * 100
        kelly_msg = f"Kelly suggests {kelly_pct:.1f}% risk"
    else:
        kelly_msg = ""
    
    # 11. Generate charts
    img_h4 = plot_candles(h4, f"{name} - H4 (Trend)", entry if "SWING" in sig else None,
                          sl if "SWING" in sig else None, tp3 if "SWING" in sig else None,
                          tp5 if "SWING" in sig else None, patterns=False)
    
    img_h1 = plot_candles(h1, f"{name} - H1 (Structure)", entry if "SWING" in sig else None,
                          sl if "SWING" in sig else None, tp3 if "SWING" in sig else None,
                          tp5 if "SWING" in sig else None, patterns=False)
    
    img_m15 = plot_candles(m15, f"{name} - M15 (Trigger)", entry if "SWING" in sig else None,
                           sl if "SWING" in sig else None, tp3 if "SWING" in sig else None,
                           tp5 if "SWING" in sig else None, patterns=True)
    
    return {
        "FINAL_DECISION": sig,
        "SETUP_SCORE": round(score.total, 1),
        "SETUP_GRADE": score.grade,
        "ADX_SCORE": round(score.trend_strength, 1),
        "MOMENTUM_SCORE": round(score.momentum_align, 1),
        "PATTERN_SCORE": round(score.patterns, 1),
        "VALUE_SCORE": round(score.value_zone, 1),
        "HIST_SCORE": round(score.historical, 1),
        "MARKET_STRUCTURE": structure,
        "VOL_REGIME": f"{vol_regime} ({vol_pct:.2f}%)",
        "PATTERNS_DETECTED": ", ".join(recent_patterns) if recent_patterns else "None",
        "MOMENTUM_ALIGNMENT": f"{momentum_score}/3 timeframes",
        "ENTRY_TYPE": entry_type,
        "SL_REASON": sl_reason,
        "WIN_RATE": sim['WR'],
        "NET_PROFIT": sim['NET'],
        "MAX_DRAWDOWN": sim['DD'],
        "PROFIT_FACTOR": sim['PF'],
        "SHARPE_RATIO": sim['SHARPE'],
        "SORTINO_RATIO": sim['SORTINO'],
        "RECOVERY_FACTOR": sim['RECOVERY'],
        "MAX_CONS_WIN": sim['MAX_CONS_WIN'],
        "MAX_CONS_LOSS": sim['MAX_CONS_LOSS'],
        "MATH_ENTRY": round(entry, 2),
        "MATH_SL": round(sl, 2),
        "MATH_TP3": round(tp3, 2),
        "MATH_TP5": round(tp5, 2),
        "POSITION_SIZE": position_size,
        "POSITION_VALUE": position_value,
        "KELLY_MSG": kelly_msg,
        "IMAGES": [img_h4, img_h1, img_m15]
    }

# ==============================================================================
# 11. STREAMLIT INTERFACE - V15.0
# ==============================================================================

st.sidebar.title("🔐 SI-APATECO V15.0")
if "GEMINI_API_KEY" in st.secrets: 
    api = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ ACCESS GRANTED")
else: 
    api = st.sidebar.text_input("ENTER API KEY", type="password")

st.sidebar.divider()

# Position sizing inputs
capital = st.sidebar.number_input("💰 Trading Capital ($)", min_value=100, value=10000, step=100)
risk_pct = st.sidebar.slider("📊 Risk Per Trade (%)", min_value=0.5, max_value=3.0, value=1.0, step=0.1)

st.sidebar.divider()
st.sidebar.info("""
**V15.0 ENHANCEMENTS:**
- 🎯 Setup Scoring (0-100)
- 📊 Pattern Detection (Pin Bar, Engulfing, etc.)
- 🔄 Momentum Alignment (3 timeframes)
- 📈 Market Structure Analysis
- 💹 Volatility Regime Filter
- 📉 Advanced Backtest (Sharpe, Sortino)
- 💰 Position Sizing (Fixed % + Kelly)
- 🎨 Enhanced Charts with MACD
""")

st.title("🎯 SI-APATECO SNIPER (V15.0)")
st.caption("Elite Multi-Timeframe Analysis | Grade A+ Setup Detection | 1:5 Payoff System")

with st.spinner("Loading Assets..."):
    assets = get_assets()

if not assets:
    st.error("❌ SIGNAL LOST")
    st.stop()

c1, c2 = st.columns([1, 2])

with c1:
    target = st.selectbox("🎯 SELECT TARGET", list(assets.keys()))
    st.markdown("### 🔬 AUTOMATED TRI-FORCE SCAN")
    st.caption("Sistema gerará e analisará M15/H1/H4 automaticamente")
    st.write("")
    run = st.button("🚀 EXECUTE ANALYSIS", use_container_width=True)

with c2:
    if run:
        if not api:
            st.error("⚠️ API KEY REQUIRED")
            st.stop()
        
        status = st.status("🛸 INITIALIZING QUANTUM CORES...", expanded=True)
        
        status.write("1️⃣ Fetching Multi-Timeframe Data (M15/H1/H4)...")
        h1, h4, m15, err = asyncio.run(fetch_tri_force(assets[target]))
        
        if err:
            status.update(state='error', label="❌ CONNECTION FAILED")
            st.error(err)
            st.stop()
        
        status.write("2️⃣ Running Enhanced Backtest (Walk-Forward + Sharpe/Sortino)...")
        status.write("3️⃣ Detecting Patterns, Structure & Momentum Alignment...")
        status.write("4️⃣ Calculating Setup Score (0-100)...")
        
        data = sniper_core_v15(target, h1, h4, m15, capital, risk_pct)
        
        generated_images = data.pop("IMAGES")
        
        status.write("5️⃣ Gemini Pro Visual Analysis...")
        genai.configure(api_key=api)
        
        try:
            model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
            ai_response = model.generate_content(
                [SYSTEM_PROMPT, f"MATH DATA: {json.dumps(data)}"] + generated_images
            ).text
            status.update(label="✅ ANALYSIS COMPLETE", state="complete")
        except:
            try:
                fb = genai.GenerativeModel("gemini-1.5-pro")
                ai_response = fb.generate_content(
                    [SYSTEM_PROMPT, f"MATH DATA: {json.dumps(data)}"] + generated_images
                ).text
                status.update(label="✅ COMPLETE (FALLBACK)", state="complete")
            except Exception as e:
                st.error(f"AI Error: {e}")
                st.stop()
        
        # ====== DISPLAY RESULTS ======
        
        # Setup Grade Header
        grade = data['SETUP_GRADE']
        score = data['SETUP_SCORE']
        
        if grade == "A+":
            grade_class = "score-a-plus"
            grade_emoji = "🏆"
        elif grade == "A":
            grade_class = "score-a"
            grade_emoji = "⭐"
        elif grade == "B":
            grade_class = "score-b"
            grade_emoji = "📊"
        else:
            grade_class = "score-c"
            grade_emoji = "⚠️"
        
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; background: rgba(251, 191, 36, 0.1); border: 2px solid #fbbf24; border-radius: 10px; margin-bottom: 20px;'>
            <h2 style='margin: 0;'>{grade_emoji} SETUP GRADE: <span class='{grade_class}'>{grade}</span></h2>
            <p style='font-size: 24px; margin: 10px 0 0 0;'>Score: <strong>{score}/100</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics Dashboard
        st.subheader("📊 PERFORMANCE METRICS")
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Win Rate", f"{data['WIN_RATE']}%")
        m2.metric("Net Profit", f"{data['NET_PROFIT']}R")
        m3.metric("Profit Factor", f"{data['PROFIT_FACTOR']}")
        m4.metric("Sharpe Ratio", f"{data['SHARPE_RATIO']}")
        m5.metric("Max DD", f"{data['MAX_DRAWDOWN']}R")
        
        m6, m7, m8, m9, m10 = st.columns(5)
        m6.metric("Sortino Ratio", f"{data['SORTINO_RATIO']}")
        m7.metric("Recovery Factor", f"{data['RECOVERY_FACTOR']}")
        m8.metric("Max Cons. Wins", f"{data['MAX_CONS_WIN']}")
        m9.metric("Max Cons. Loss", f"{data['MAX_CONS_LOSS']}")
        m10.metric("Momentum", f"{data['MOMENTUM_ALIGNMENT']}")
        
        # Setup Quality Breakdown
        st.subheader("🔬 SETUP QUALITY BREAKDOWN")
        
        score_data = pd.DataFrame([{
            "Component": "Trend Strength",
            "Score": f"{data['ADX_SCORE']}/25",
            "Value": data['ADX_SCORE']
        }, {
            "Component": "Momentum Alignment",
            "Score": f"{data['MOMENTUM_SCORE']}/20",
            "Value": data['MOMENTUM_SCORE']
        }, {
            "Component": "Candlestick Patterns",
            "Score": f"{data['PATTERN_SCORE']}/15",
            "Value": data['PATTERN_SCORE']
        }, {
            "Component": "Value Zone",
            "Score": f"{data['VALUE_SCORE']}/15",
            "Value": data['VALUE_SCORE']
        }, {
            "Component": "Historical Edge",
            "Score": f"{data['HIST_SCORE']}/25",
            "Value": data['HIST_SCORE']
        }])
        
        st.dataframe(score_data[['Component', 'Score']], use_container_width=True, hide_index=True)
        
        # Signal Display
        st.divider()
        
        decision = data['FINAL_DECISION']
        if "SWING" in decision:
            st.success(f"✅ **SIGNAL CONFIRMED:** {decision}")
            st.balloons()
        elif "BLOCKED" in decision:
            st.error(f"🛑 **TRADE BLOCKED:** {decision}")
        else:
            st.warning(f"⏸️ **STATUS:** {decision}")
        
        # Trade Plan
        if "SWING" in decision:
            st.subheader("📋 TRADE EXECUTION PLAN")
            
            plan_data = pd.DataFrame([{
                "Parameter": "Entry",
                "Value": data['MATH_ENTRY'],
                "Notes": data['ENTRY_TYPE']
            }, {
                "Parameter": "Stop Loss",
                "Value": data['MATH_SL'],
                "Notes": data['SL_REASON']
            }, {
                "Parameter": "TP 1 (1:3)",
                "Value": data['MATH_TP3'],
                "Notes": "Bank 50% here"
            }, {
                "Parameter": "TP 2 (1:5)",
                "Value": data['MATH_TP5'],
                "Notes": "Let it run with trailing"
            }, {
                "Parameter": "Position Size",
                "Value": f"{data['POSITION_SIZE']} units",
                "Notes": f"${data['POSITION_VALUE']} ({risk_pct}% risk)"
            }])
            
            st.dataframe(plan_data, use_container_width=True, hide_index=True)
            
            if data['KELLY_MSG']:
                st.info(f"💡 {data['KELLY_MSG']}")
        
        # Market Context
        st.subheader("🌍 MARKET CONTEXT")
        
        context_cols = st.columns(3)
        with context_cols[0]:
            st.metric("Market Structure", data['MARKET_STRUCTURE'])
        with context_cols[1]:
            st.metric("Volatility Regime", data['VOL_REGIME'])
        with context_cols[2]:
            st.metric("Patterns Detected", data['PATTERNS_DETECTED'] or "None")
        
        # Charts
        st.divider()
        st.subheader("📊 CHART ANALYSIS")
        
        chart_tabs = st.tabs(["H4 - Trend", "H1 - Structure", "M15 - Trigger"])
        
        with chart_tabs[0]:
            st.image(generated_images[0], use_column_width=True)
        
        with chart_tabs[1]:
            st.image(generated_images[1], use_column_width=True)
        
        with chart_tabs[2]:
            st.image(generated_images[2], use_column_width=True)
        
        # AI Analysis
        st.divider()
        st.subheader("🤖 AI VISUAL ANALYSIS")
        st.markdown(ai_response)
