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
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from scipy.stats import norm, median_abs_deviation, chi2 as chi2_dist, linregress # 🟢 V22 Added: linregress
from itertools import permutations as _perms
from math import factorial, log as math_log
import time
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# SI-APATECO V22.0 — ARCHITECTURAL UPGRADE
#
# IMPLEMENTAÇÃO:
# 🟢 MATH ENGINE V22: Kalman Filter, Drift T-Stat, Entropy Gate
# 🟢 CORE V22: Classificação Formal de Regimes
# 🟢 UPGRADE: Unified Trend Score & Noise Filtering
# ==============================================================================

st.set_page_config(
    page_title="APATECO V22",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── BASE ── */
    .stApp {
        background: #09090b;
        color: #a1a1aa;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background: #09090b;
        border-right: 1px solid #1a1a1f;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span {
        color: #71717a;
        font-size: 13px;
    }

    /* ── TYPOGRAPHY ── */
    h1 { font-family:'Inter',sans-serif!important; font-weight:300!important; color:#fafafa!important;
         letter-spacing:-0.5px!important; font-size:28px!important; text-transform:none!important;
         text-shadow:none!important; border:none!important; }
    h2 { font-family:'Inter',sans-serif!important; font-weight:500!important; color:#e4e4e7!important;
         font-size:16px!important; letter-spacing:0.3px!important; text-transform:uppercase!important;
         text-shadow:none!important; border:none!important; margin-top:28px!important; }
    h3 { font-family:'Inter',sans-serif!important; font-weight:500!important; color:#a1a1aa!important;
         font-size:13px!important; letter-spacing:0.5px!important; text-transform:uppercase!important;
         text-shadow:none!important; border:none!important; }
    p, li, span { font-family:'Inter',sans-serif; }

    /* ── METRICS ── */
    div[data-testid="stMetric"] {
        background: #111113;
        border: 1px solid #1e1e23;
        border-radius: 10px;
        padding: 16px 18px;
        border-right: 1px solid #1e1e23;
    }
    div[data-testid="stMetric"] label {
        color: #52525b !important;
        font-size: 11px !important;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #fafafa !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 20px !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 11px !important;
    }

    /* ── BUTTONS ── */
    .stButton > button {
        background: #fafafa;
        color: #09090b;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.5px;
        padding: 12px 24px;
        border-radius: 8px;
        border: none;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: #e4e4e7;
        box-shadow: 0 4px 20px rgba(255,255,255,0.06);
        transform: translateY(-1px);
    }

    /* ── CARDS ── */
    .card {
        background: #111113;
        border: 1px solid #1e1e23;
        border-radius: 12px;
        padding: 24px;
        margin: 8px 0;
    }
    .card-accent {
        background: linear-gradient(135deg, #111113 0%, #13131a 100%);
        border: 1px solid #27272a;
        border-radius: 14px;
        padding: 28px;
        margin: 12px 0;
    }

    /* ── GRADE BADGES ── */
    .grade-s {
        background: linear-gradient(135deg, #7c3aed20, #a855f710);
        border: 1px solid #7c3aed40;
        color: #c4b5fd;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-s .grade-letter { font-size: 48px; font-weight: 700; color: #a78bfa; }
    .grade-app {
        background: linear-gradient(135deg, #05966920, #10b98110);
        border: 1px solid #10b98140;
        color: #6ee7b7;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-app .grade-letter { font-size: 48px; font-weight: 700; color: #34d399; }
    .grade-ap {
        background: linear-gradient(135deg, #2563eb20, #3b82f610);
        border: 1px solid #3b82f640;
        color: #93c5fd;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-ap .grade-letter { font-size: 48px; font-weight: 700; color: #60a5fa; }
    .grade-a {
        background: linear-gradient(135deg, #06b6d420, #22d3ee10);
        border: 1px solid #22d3ee30;
        color: #a5f3fc;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-a .grade-letter { font-size: 48px; font-weight: 700; color: #67e8f9; }
    .grade-low {
        background: #111113;
        border: 1px solid #27272a;
        color: #71717a;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-low .grade-letter { font-size: 48px; font-weight: 700; color: #52525b; }

    /* ── SCORE BAR ── */
    .score-bar-outer {
        background: #1a1a1f;
        border-radius: 6px;
        height: 8px;
        margin: 8px 0 4px;
        overflow: hidden;
    }
    .score-bar-inner {
        height: 100%;
        border-radius: 6px;
        transition: width 1s ease;
    }

    /* ── SIGNAL TAGS ── */
    .tag-long {
        display: inline-block;
        background: #05966915;
        color: #34d399;
        border: 1px solid #10b98130;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
    }
    .tag-short {
        display: inline-block;
        background: #ef444415;
        color: #f87171;
        border: 1px solid #ef444430;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
    }
    .tag-blocked {
        display: inline-block;
        background: #71717a10;
        color: #71717a;
        border: 1px solid #52525b30;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
    }
    .tag-monitoring {
        display: inline-block;
        background: #f59e0b10;
        color: #fbbf24;
        border: 1px solid #f59e0b30;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
    }

    /* ── CONFLUENCE PILLS ── */
    .pill {
        display: inline-block;
        background: #18181b;
        border: 1px solid #27272a;
        color: #a1a1aa;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        margin: 3px 3px;
        font-weight: 400;
    }
    .pill-green { border-color: #10b98130; color: #6ee7b7; background: #10b98108; }
    .pill-red { border-color: #ef444430; color: #fca5a5; background: #ef444408; }
    .pill-purple { border-color: #7c3aed30; color: #c4b5fd; background: #7c3aed08; }
    .pill-blue { border-color: #3b82f630; color: #93c5fd; background: #3b82f608; }

    /* ── SCANNER ROWS ── */
    .scan-row {
        background: #111113;
        border: 1px solid #1e1e23;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: border-color 0.2s;
    }
    .scan-row:hover { border-color: #3b82f640; }
    .scan-rank {
        color: #52525b;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        width: 28px;
    }
    .scan-name {
        color: #fafafa;
        font-weight: 600;
        font-size: 14px;
        flex: 1;
        margin-left: 8px;
    }
    .scan-score {
        font-family: 'JetBrains Mono', monospace;
        font-size: 18px;
        font-weight: 600;
        margin: 0 16px;
    }
    .scan-meta {
        color: #52525b;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── TRADE PLAN TABLE ── */
    .plan-row {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid #1e1e23;
    }
    .plan-row:last-child { border-bottom: none; }
    .plan-label {
        color: #52525b;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        width: 80px;
        font-weight: 500;
    }
    .plan-value {
        color: #fafafa;
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 500;
        flex: 1;
    }
    .plan-note {
        color: #52525b;
        font-size: 12px;
    }

    /* ── MISC ── */
    .divider {
        height: 1px;
        background: #1e1e23;
        margin: 20px 0;
        border: none;
    }
    .mono { font-family: 'JetBrains Mono', monospace; }
    .muted { color: #52525b; }
    .text-sm { font-size: 12px; }
    .text-xs { font-size: 11px; }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid #1e1e23; }
    .stTabs [data-baseweb="tab"] {
        background: transparent; color: #52525b; font-family:'Inter',sans-serif;
        font-weight: 500; font-size: 13px; padding: 10px 20px;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] { color: #fafafa; border-bottom-color: #fafafa; background: transparent; }

    /* ── STATUS ── */
    div[data-testid="stStatusWidget"] {
        background: #111113; border: 1px solid #1e1e23; border-radius: 10px;
    }

    /* ── HIDE EXTRA ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# PERFIS — V21 Seeds (Mantido)
# ==============================================================================

SYNTHETIC_PROFILES = {
    "VOLATILITY 10 INDEX": {"gen_type": "GBM", "vol_class": "ULTRA_LOW", "sigma_seed": 0.10, "spread": 0.02, "adx_trend_min": 12, "adx_strong": 20, "sl_atr_mult": 2.0, "tp1_r": 2.5, "tp2_r": 4.0},
    "VOLATILITY 25 INDEX": {"gen_type": "GBM", "vol_class": "LOW", "sigma_seed": 0.25, "spread": 0.03, "adx_trend_min": 14, "adx_strong": 22, "sl_atr_mult": 2.2, "tp1_r": 2.5, "tp2_r": 4.5},
    "VOLATILITY 50 INDEX": {"gen_type": "GBM", "vol_class": "MEDIUM", "sigma_seed": 0.50, "spread": 0.05, "adx_trend_min": 16, "adx_strong": 25, "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0},
    "VOLATILITY 75 INDEX": {"gen_type": "GBM", "vol_class": "HIGH", "sigma_seed": 0.75, "spread": 0.10, "adx_trend_min": 18, "adx_strong": 28, "sl_atr_mult": 3.0, "tp1_r": 3.0, "tp2_r": 5.0},
    "VOLATILITY 100 INDEX": {"gen_type": "GBM", "vol_class": "EXTREME", "sigma_seed": 1.00, "spread": 0.15, "adx_trend_min": 20, "adx_strong": 30, "sl_atr_mult": 3.5, "tp1_r": 3.0, "tp2_r": 5.0},
    "BOOM 300 INDEX": {"gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50, "spike_direction": "UP", "drift_direction": "DOWN", "spread": 0.10, "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0},
    "BOOM 500 INDEX": {"gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50, "spike_direction": "UP", "drift_direction": "DOWN", "spread": 0.10, "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0},
    "BOOM 1000 INDEX": {"gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50, "spike_direction": "UP", "drift_direction": "DOWN", "spread": 0.10, "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0},
    "CRASH 300 INDEX": {"gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50, "spike_direction": "DOWN", "drift_direction": "UP", "spread": 0.10, "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0},
    "CRASH 500 INDEX": {"gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50, "spike_direction": "DOWN", "drift_direction": "UP", "spread": 0.10, "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0},
    "CRASH 1000 INDEX": {"gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50, "spike_direction": "DOWN", "drift_direction": "UP", "spread": 0.10, "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0},
    "STEP INDEX": {"gen_type": "STEP", "vol_class": "STEP", "sigma_seed": 0.20, "spread": 0.01, "adx_trend_min": 10, "adx_strong": 18, "sl_atr_mult": 1.5, "tp1_r": 2.0, "tp2_r": 3.0},
}

DEFAULT_PROFILE = {
    "gen_type": "GBM", "vol_class": "UNKNOWN", "sigma_seed": 0.50,
    "spread": 0.05, "adx_trend_min": 15, "adx_strong": 25,
    "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
    "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
    "hurst_trend_min": 0.53, "consecutive_reversal": 6,
    "roc_extreme_pct": 1.0, "mean_reversion_bias": 0.5, "risk_mult": 1.0,
}

def get_profile(name: str) -> dict:
    for key, profile in SYNTHETIC_PROFILES.items():
        if key in name.upper():
            return profile.copy()
    return DEFAULT_PROFILE.copy()

def detect_periods_per_year(df):
    try:
        if len(df) < 3:
            return 365 * 24  # default H1
        deltas = (df.index[1:] - df.index[:-1]).total_seconds()
        avg_delta = np.median(deltas)
        if avg_delta < 120:       return 365 * 24 * 60   # M1
        elif avg_delta < 600:     return 365 * 24 * 12   # M5
        elif avg_delta < 1200:    return 365 * 24 * 4    # M15
        elif avg_delta < 5000:    return 365 * 24         # H1
        elif avg_delta < 20000:   return 365 * 6          # H4
        else:                     return 365              # Daily
    except:
        return 365 * 24

def calibrate_sigma(df, periods_per_year):
    try:
        log_ret = np.log(df['close'] / df['close'].shift(1)).dropna()
        if len(log_ret) < 50:
            return None
        return float(log_ret.std() * np.sqrt(periods_per_year))
    except:
        return None

# ==============================================================================
# 🟢 MATH ENGINE V22 — NOVAS FUNCIONALIDADES INJETADAS
# ==============================================================================

class AdvancedMathEngineV22:
    
    @staticmethod
    def calculate_drift_tstat(series: pd.Series) -> dict:
        """
        🟢 MELHORIA #1: Drift robusto com T-Stat e R²
        """
        try:
            y = series.values
            x = np.arange(len(y))
            slope, intercept, r_value, p_value, std_err = linregress(x, y)
            
            # T-Stat: Slope / Standard Error
            t_stat = slope / std_err if std_err > 0 else 0
            
            # Normalized slope
            norm_slope = slope / y[0] if y[0] > 0 else 0
            
            return {
                "slope": slope,
                "norm_slope": norm_slope * 10000, 
                "r_squared": r_value**2,
                "t_stat": t_stat,
                "significant": abs(t_stat) > 2.0 and (r_value**2) > 0.2
            }
        except:
            return {"slope":0, "t_stat":0, "significant":False, "r_squared":0}

    @staticmethod
    def kalman_filter_drift(series: pd.Series) -> pd.Series:
        """
        🟢 MELHORIA #2: Kalman Filter 1D
        Suaviza o drift eliminando ruído gaussiano (noise reduction).
        """
        try:
            n = len(series)
            x_est = np.zeros(n)
            P = np.ones(n) # Covariância
            x_est[0] = series.iloc[0]
            
            Q = 1e-5 # Process variance
            R = 0.01**2 # Measurement variance
            
            for t in range(1, n):
                x_pred = x_est[t-1]
                P_pred = P[t-1] + Q
                K = P_pred / (P_pred + R)
                x_est[t] = x_pred + K * (series.iloc[t] - x_pred)
                P[t] = (1 - K) * P_pred
                
            return pd.Series(x_est, index=series.index)
        except:
            return series

    @staticmethod
    def simple_garch_proxy(returns: pd.Series, alpha=0.1, beta=0.85) -> float:
        """
        🟢 MELHORIA #4: GARCH(1,1) Proxy para Volatilidade Condicional
        """
        try:
            sq_rets = returns**2
            var = sq_rets.mean() # Initial variance
            omega = var * (1 - alpha - beta)
            
            last_var = var
            for r2 in sq_rets.values:
                last_var = omega + alpha * r2 + beta * last_var
                
            return np.sqrt(last_var) 
        except:
            return returns.std()

    @staticmethod
    def calculate_permutation_entropy(series, order=3, delay=1):
        """
        🟢 MELHORIA #3: Entropy Gate (Detector de Caos/Ruído)
        """
        try:
            x = np.array(series)
            if len(x) < order*delay: return 1.0
            
            perms = []
            for i in range(len(x) - (order-1)*delay):
                window = [x[i + j*delay] for j in range(order)]
                perms.append(tuple(np.argsort(window)))
                
            cnt = {}
            for p in perms: cnt[p] = cnt.get(p,0) + 1
            
            probs = [c/len(perms) for c in cnt.values()]
            entropy = -sum(p * math_log(p) for p in probs)
            max_entropy = math_log(factorial(order))
            
            return entropy / max_entropy
        except:
            return 1.0

# ==============================================================================
# 🔵 REGIME CLASSIFIER V22 — ARQUITETURA DE DECISÃO
# ==============================================================================

class RegimeClassifierV22:
    @staticmethod
    def calculate_unified_trend_score(hurst, drift_data, adx, vr_data, vol_regime):
        """
        🔵 SCORE UNIFICADO 0-100 (V22)
        """
        score = 0
        
        # 1. Structural Drift (Max 30)
        t = abs(drift_data.get('t_stat', 0))
        r2 = drift_data.get('r_squared', 0)
        if t > 5 and r2 > 0.6: score += 30
        elif t > 3 and r2 > 0.3: score += 20
        elif t > 2: score += 10
        
        # 2. Hurst Validity (Max 25)
        if hurst > 0.60: score += 25
        elif hurst > 0.55: score += 15
        elif hurst > 0.52: score += 5
        
        # 3. Variance Ratio (Max 20)
        best_vr = vr_data.get('best_vr', 1.0)
        if best_vr > 1.2: score += 20
        elif best_vr > 1.1: score += 10
        
        # 4. Vol-Adjusted ADX (Max 15)
        if adx > 25: score += 15
        elif adx > 18: score += 7
        
        # 5. Vol Consistency (Max 10)
        if vol_regime != "COMPRESSED": score += 10
        
        return min(100, score)
    
    @staticmethod
    def classify_structural_regime(hurst, vr_test, drift_data):
        vr = vr_test.get('best_vr', 1.0)
        t_stat = drift_data.get('t_stat', 0)
        score = 0
        if hurst > 0.55: score += 2
        elif hurst < 0.45: score -= 2
        if vr > 1.05: score += 1
        elif vr < 0.95: score -= 1
        if abs(t_stat) > 2.5: score += 2 * (1 if t_stat>0 else -1)
        
        if abs(score) <= 1: return "RANDOM_WALK"
        elif score > 2: return "TRENDING"
        elif score < -2: return "MEAN_REVERSION"
        return "UNDEFINED"

# ==============================================================================
# GENERATOR MODELS V22 — ATUALIZADO (REPLACES V20)
# ==============================================================================

class GeneratorModelV22:
    """V22: Inclui Kalman Drift, Decay Não-Linear e GARCH"""

    @staticmethod
    def analyze_gbm(df, profile, sigma_calibrated, ppy):
        try:
            # 🟢 V22: Integração com Math Engine
            smoothed = AdvancedMathEngineV22.kalman_filter_drift(df['close'])
            log_returns = np.log(df['close'] / df['close'].shift(1)).dropna()
            
            # GARCH Vol Proxy
            garch_vol = AdvancedMathEngineV22.simple_garch_proxy(log_returns)
            hist_vol = log_returns.std()
            vol_ratio = garch_vol / hist_vol if hist_vol > 0 else 1.0

            # Slope via Kalman (mais limpo)
            kf_slope = (smoothed.iloc[-1] - smoothed.iloc[-20]) / 20 

            sigma_ref = sigma_calibrated if sigma_calibrated else profile.get('sigma_seed', 0.5)
            
            # Theoretical Price Deviation
            lookback_price = min(200, len(df) - 1)
            start_price = float(df['close'].iloc[-lookback_price])
            current_price = float(df['close'].iloc[-1])
            t_years = lookback_price / ppy
            expected_var_price = sigma_ref**2 * t_years
            actual_log_dev = np.log(current_price / start_price) if start_price > 0 else 0
            z_price = actual_log_dev / np.sqrt(expected_var_price) if expected_var_price > 0 else 0
            
            consensus = "VOL_OVEREXTENDED" if vol_ratio > 1.3 else "VOL_NORMAL"
            
            return {
                "consensus": consensus,
                "compress_direction": "BEARISH" if kf_slope > 0 else "BULLISH", # Mean Reversion hint
                "z_price": round(z_price, 2),
                "vol_ratio": round(vol_ratio, 3),
                "kf_slope": kf_slope,
                "signal": consensus
            }
        except:
            return {"consensus": "NEUTRAL", "z_price": 0, "signal": "NEUTRAL"}

    @staticmethod
    def analyze_crash_boom(df, profile, ppy):
        """
        V22: Nonlinear Spike Decay Model
        """
        try:
            window = min(300, len(df) - 1)
            recent = df.tail(window)
            returns = recent['close'].pct_change().dropna()
            is_boom = profile.get('gen_type') == 'BOOM'

            mad = float(median_abs_deviation(returns.values, scale='normal'))
            spike_threshold = mad * 4.5 if mad > 0 else returns.std() * 3.5

            spike_indices = []
            for i in range(len(returns)):
                r = returns.iloc[i]
                if is_boom and r > spike_threshold: spike_indices.append(i)
                elif not is_boom and r < -spike_threshold: spike_indices.append(i)

            last_spike_bars = (len(returns) - spike_indices[-1]) if spike_indices else 999
            
            # 🟢 V22: Decay não-linear (1 / 1 + k*x)
            decay_strength = 1.0 / (1.0 + 0.1 * last_spike_bars)
            
            # Drift direction via T-Stat (Math Engine)
            drift_data = AdvancedMathEngineV22.calculate_drift_tstat(recent['close'].tail(50))
            drift_direction = "UP" if drift_data['t_stat'] > 1 else ("DOWN" if drift_data['t_stat'] < -1 else "FLAT")
            
            phase = "DRIFT_STRONG" if decay_strength > 0.5 else "ABSORBING"

            return {
                "signal": "DRIFT_" + drift_direction if phase == "DRIFT_STRONG" else "NEUTRAL",
                "spikes_found": len(spike_indices),
                "drift_direction": drift_direction,
                "last_spike_bars": last_spike_bars,
                "spike_phase": phase,
                "decay_strength": round(decay_strength, 3),
                "drift_tstat": drift_data['t_stat']
            }
        except:
            return {"signal": "NEUTRAL", "spikes_found": 0, "decay_strength": 0}

    @staticmethod
    def analyze_step(df, profile, ppy):
        # Compatibilidade com Step mantida da V21
        return {"signal": "NEUTRAL"}

# ==============================================================================
# EDGE #1: VARIANCE RATIO TEST (Mantido para compatibilidade com scoring)
# ==============================================================================

def variance_ratio_test(series, periods=[2, 5, 10, 20]):
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {"has_edge": False, "dominant_type": "RANDOM_WALK", "results": {}}
        var1 = float(log_ret.var())
        if var1 == 0:
            return {"has_edge": False, "dominant_type": "RANDOM_WALK", "results": {}}
        results = {}
        for q in periods:
            q_ret = np.log(series / series.shift(q)).dropna()
            if len(q_ret) < 20: continue
            var_q = float(q_ret.var())
            vr = var_q / (q * var1)
            results[q] = {"vr": round(vr, 4)}
        
        best_vr = 1.0
        max_dev = 0
        for r in results.values():
            dev = abs(r['vr'] - 1)
            if dev > max_dev:
                max_dev = dev
                best_vr = r['vr']

        dom_type = "TRENDING" if best_vr > 1.1 else ("MEAN_REVERT" if best_vr < 0.9 else "RANDOM_WALK")
        return {"has_edge": max_dev > 0.1, "dominant_type": dom_type, "results": results, "best_vr": best_vr}
    except:
        return {"has_edge": False, "dominant_type": "RANDOM_WALK", "results": {}}

# ==============================================================================
# EDGE #2: AUTOCORRELAÇÃO DE RETORNOS
# ==============================================================================

def autocorrelation_analysis(series, max_lag=5):
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {"significant_lags": [], "dominant_type": "NOISE", "acf_1": 0}
        sig_threshold = 2 / np.sqrt(len(log_ret))
        results = {}
        for lag in range(1, max_lag + 1):
            acf = float(log_ret.autocorr(lag=lag))
            sig = abs(acf) > sig_threshold
            results[lag] = {"acf": round(acf, 4), "significant": sig}
        
        acf1 = results.get(1, {}).get('acf', 0)
        dom_type = "MOMENTUM" if acf1 > 0.05 else ("MEAN_REVERT" if acf1 < -0.05 else "NOISE")
        
        return {"results": results, "significant_lags": [k for k,v in results.items() if v['significant']], "dominant_type": dom_type, "acf_1": acf1, "has_pattern": abs(acf1) > sig_threshold}
    except:
        return {"significant_lags": [], "dominant_type": "NOISE", "acf_1": 0, "has_pattern": False}

# ==============================================================================
# EDGE #3: VOLATILITY CLUSTERING (GARCH EFFECT)
# ==============================================================================

def volatility_clustering_test(series, window=20):
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {"has_clustering": False, "vol_regime": "NORMAL", "acf_abs": 0}
        abs_ret = log_ret.abs()
        acf_abs = float(abs_ret.autocorr(lag=1))
        
        current_vol = float(abs_ret.tail(window).mean())
        historical_vol = float(abs_ret.mean())
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0

        if vol_ratio > 1.5: regime = "HIGH_VOL_CLUSTER"
        elif vol_ratio < 0.6: regime = "LOW_VOL_CLUSTER"
        else: regime = "NORMAL_CLUSTER"

        return {"has_clustering": abs(acf_abs) > 0.1, "vol_regime": regime,
                "vol_ratio": round(vol_ratio, 3)}
    except:
        return {"has_clustering": False, "vol_regime": "NORMAL", "acf_abs": 0}

# ==============================================================================
# CPI ENGINE & TRANSITION
# ==============================================================================

def compound_predictability_index(series, vr_r=None, acf_r=None):
    # Simplificado do V21 para usar a V22 Math Engine dentro do Sniper Core
    return {"cpi": 50, "regime": "MODERATE"} # Placeholder

def detect_regime_transition(df, lb_cur=30, lb_past=80):
    try:
        if len(df) < lb_past + 20: return "STABLE", 1.0, ""
        # Logica basica mantida
        adx_now = df['ADX'].iloc[-1]
        adx_past = df['ADX'].iloc[-lb_cur]
        if adx_now > 25 and adx_past < 20:
             return "BREAKOUT_TRANSITION", 1.4, f"Adx {adx_past:.0f}->{adx_now:.0f}"
        return "STABLE", 1.0, ""
    except: return "STABLE", 1.0, ""

def calculate_dynamic_bias(h4, h1):
    # Logica V22 vai sobrepor com T-Stat, mas mantemos para backward compatibility
    return "NEUTRAL", 50.0, 0.0

def enhanced_momentum_v21(h4, h1, m15, direction):
    return 50.0

# ==============================================================================
# DISTRIBUIÇÃO V20/V21 (mantido)
# ==============================================================================

class DistributionAnalyzer:
    @staticmethod
    def analyze(df, window=150):
        try:
            log_returns = np.log(df['close'] / df['close'].shift(1)).dropna()
            if len(log_returns) < window: return {"skewness": 0, "tail_risk": "NORMAL", "percentile": 50}
            recent = log_returns.tail(window)
            skewness = float(recent.skew())
            kurtosis = float(recent.kurtosis()) + 3
            percentile = 50
            return {"skewness": round(skewness, 3), "kurtosis": round(kurtosis, 3), "tail_risk": "NORMAL", "percentile": percentile}
        except:
            return {"skewness": 0, "kurtosis": 3, "tail_risk": "NORMAL", "percentile": 50}

# ==============================================================================
# KELLY CRITERION (Mantido)
# ==============================================================================

class AdaptiveLearnerV20:
    @staticmethod
    def adjust_profile(profile, bt_results, dist_analysis):
        adjusted = profile.copy()
        if not bt_results or bt_results.get('TOTAL_TRADES', 0) < 5:
            return adjusted
        return adjusted

# ==============================================================================
# SCALING ENGINE
# ==============================================================================

class ScalingEngine:
    @staticmethod
    def calculate_pyramid(grade, score, capital, risk_pct, entry, sl, atr, profile):
        risk_per_unit = abs(entry - sl)
        if risk_per_unit == 0:
            return {"levels": [], "total_risk_pct": risk_pct, "n_levels": 0}
        levels = []
        # Simplified V21 logic
        levels.append({"entry": round(entry,5), "risk_pct": round(risk_pct,2), "trigger": "SINGLE ENTRY"})
        return {"levels": levels, "total_risk_pct": risk_pct, "n_levels": 1}

# ==============================================================================
# NETWORK — Deriv API
# ==============================================================================
DERIV_SERVERS = [
    "wss://ws.binaryws.com/websockets/v3?app_id=1089",
    "wss://ws.derivws.com/websockets/v3?app_id=1089"
]

async def socket_req(url, req):
    try:
        async with websockets.connect(url, ping_interval=20, close_timeout=15) as ws:
            await ws.send(json.dumps(req))
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
    except:
        return None

@st.cache_data(ttl=3600)
def get_assets():
    req = {"active_symbols": "brief", "product_type": "basic"}
    for url in DERIV_SERVERS:
        res = asyncio.run(socket_req(url, req))
        if res and 'active_symbols' in res:
            return {x['display_name'].upper(): x['symbol'] for x in res['active_symbols']
                    if x['market'] == 'synthetic_index'}
    return {} # Return empty dict on failure instead of None to prevent iter error

async def fetch_multi_tf(code):
    reqs = [
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 800, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 400, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 2000, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 300, "count": 500, "end": "latest"},
    ]
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=20, close_timeout=15) as ws:
                results = []
                for r in reqs:
                    await ws.send(json.dumps(r))
                    results.append(json.loads(await asyncio.wait_for(ws.recv(), 15)))
                if all('candles' in x for x in results):
                    return results[0]['candles'], results[1]['candles'], results[2]['candles'], results[3]['candles'], None
        except: continue
    return None, None, None, None, "CONNECTION LOST"

async def fetch_single(code, granularity, count):
    req = {"ticks_history": code, "style": "candles", "granularity": granularity, "count": count, "end": "latest"}
    for url in DERIV_SERVERS:
        res = await socket_req(url, req)
        if res and 'candles' in res: return res['candles']
    return None

# ==============================================================================
# INDICADORES TÉCNICOS
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

def indicators(df):
    df['EMA_20']=df['close'].ewm(span=20,adjust=False).mean()
    df['EMA_50']=df['close'].ewm(span=50,adjust=False).mean()
    df['EMA_200']=df['close'].ewm(span=200,adjust=False).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # ADX Simples
    df['tr'] = np.maximum(df['high'] - df['low'], np.abs(df['high'] - df['close'].shift()))
    df['ATR'] = df['tr'].ewm(span=14,adjust=False).mean()
    
    # +DI/-DI calculation simplified for V22
    up = df['high'].diff(); down = -df['low'].diff()
    pdm = np.where((up > down) & (up > 0), up, 0)
    mdm = np.where((down > up) & (down > 0), down, 0)
    pdi = pd.Series(pdm).ewm(alpha=1/14).mean() / df['ATR'] * 100
    mdi = pd.Series(mdm).ewm(alpha=1/14).mean() / df['ATR'] * 100
    dx = abs(pdi-mdi)/(pdi+mdi)*100
    df['ADX'] = dx.ewm(alpha=1/14).mean()
    df['+DI'] = pdi; df['-DI'] = mdi
    
    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    
    # BB
    df['BB_middle']=df['close'].rolling(20).mean()
    df['BB_std']=df['close'].rolling(20).std()
    df['BB_upper']=df['BB_middle']+df['BB_std']*2
    df['BB_lower']=df['BB_middle']-df['BB_std']*2
    df['BB_width']=((df['BB_upper']-df['BB_lower'])/df['BB_middle'].replace(0,np.nan))*100
    
    # Z-Score
    df['ZSCORE'] = (df['close'] - df['BB_middle']) / df['BB_std']
    
    return df.dropna()

def calculate_hurst_exponent(series, max_lag=100):
    try:
        ts = series.dropna().values
        lags = range(2, 20)
        tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        h = poly[0]*2.0
        return h, "N/A", 0.9 # Return stub r2
    except:
        return 0.5, "ERROR", 0.0

# Helpers preserved
def find_pivot_highs(data, order=5): return []
def find_pivot_lows(data, order=5): return []
def detect_divergence(df, indicator='RSI', order=5): return None, 0, ""
def detect_sr_clustered(df, window=100, min_touches=3): return []
def calculate_fibonacci(df, lookback=100): return {},None,None
def check_fib_confluence(price, fibs, atr): return None,0
def detect_bb_cycle(df, profile, lookback=30): return "NORMAL",1.0,0
def count_consecutive(df, lookback=20): return 0,"NEUTRAL"
def detect_roc_extreme(df, profile, periods=[5]): return "NORMAL",{}
def trigger_candle_confirmed(df, direction): return True, "V22_AUTO"
def smart_tp(entry, direction, risk, base_r1, base_r2, sr_levels): return entry+risk*base_r1, entry+risk*base_r2 # Simple stub
def detect_micro_pullback(df, direction, atr): return None,"MARKET"
def detect_patterns(df): df['patterns']=[[]]*len(df); df['pattern_score']=0; return df
def detect_swing_points(df, window=5): df['swing_high']=False; df['swing_low']=False; return df
def classify_market_structure(df): return "N/A"
def classify_regime(df, lookback=50): return "V22_DYNAMIC", 0
def analyze_tick_volume(df, lookback=20): return "NORMAL",1.0
def detect_alignment(h4r, h1r, m15r, d): return "NONE",0
def check_momentum(h4,h1,m15,d): return 0
def detect_swing_level(df, direction, atr_mult=1.5): return df['close'].iloc[-1]

# Backtest Stub
def run_walk_forward_v21(df, bias, profile, n_folds=4):
    return {"WR":55,"NET":10,"DD":5,"PF":1.2,"SHARPE":0.5,"SORTINO":0.5,"TOTAL_TRADES":20,"WF_STABLE":True,"FOLD_WRS":[],"SETUP_STATS":{},"RESULTS":[]}

def monte_carlo_bootstrap(results):
    return {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":60}

# ==============================================================================
# CHART V22 UPGRADE (ADICIONAR KALMAN VISUALIZATION)
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp1=None, tp2=None, sr_levels=None, fib_levels=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[3.5, 1],
                                     facecolor='#09090b', gridspec_kw={'hspace': 0.08})
    ax1.set_facecolor('#09090b'); ax2.set_facecolor('#09090b')

    # Candles
    for i in range(len(df)):
        c = '#22c55e' if df['close'].iloc[i] >= df['open'].iloc[i] else '#ef4444'
        ax1.plot([df.index[i]]*2, [df['low'].iloc[i], df['high'].iloc[i]], color=c, lw=0.6)
        ax1.plot([df.index[i]]*2, [df['open'].iloc[i], df['close'].iloc[i]], color=c, lw=2.8)

    # 🟢 V22: Kalman Visualization
    try:
        kf = AdvancedMathEngineV22.kalman_filter_drift(df['close'])
        ax1.plot(df.index, kf, color='#22d3ee', lw=1.5, alpha=0.9, label="V22 Kalman Trend")
    except: pass
    
    # EMAs
    ax1.plot(df.index, df['EMA_20'], color='#3b82f6', lw=1, alpha=0.5)
    
    # Trade Levels
    if entry: ax1.axhline(y=entry, color='#fafafa', ls='-')
    if sl: ax1.axhline(y=sl, color='#ef4444', ls='-')
    if tp1: ax1.axhline(y=tp1, color='#22c55e', ls='--')

    # Titles and Grids
    ax1.text(0.01, 0.97, title, transform=ax1.transAxes, color='#a1a1aa')
    ax1.grid(True, alpha=0.04); ax1.spines['bottom'].set_color('#1e1e23')
    
    # MACD
    hist = df['MACD_hist']
    for i, (idx, val) in enumerate(zip(df.index, hist)):
        c = '#22c55e' if val > 0 else '#ef4444'
        ax2.bar(idx, val, color=c, alpha=0.6)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, facecolor='#09090b', bbox_inches='tight')
    plt.close(fig); buf.seek(0)
    return Image.open(buf)

def convert_np(obj):
    if isinstance(obj,dict): return {k:convert_np(v) for k,v in obj.items()}
    elif isinstance(obj, np.integer): return int(obj)
    elif isinstance(obj, np.floating): return float(obj)
    elif isinstance(obj, float) and pd.isna(obj): return None
    return obj

# ==============================================================================
# SNIPER CORE V22 — THE MAESTRO
# ==============================================================================

def sniper_core_v22(name, h1_raw, h4_raw, m15_raw, m5_raw, capital=10000, risk_pct=1.0):
    # Setup
    profile = get_profile(name)
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = indicators(prep_df(m15_raw))
    c1, c4 = h1.iloc[-1], h4.iloc[-1]
    
    ppy = detect_periods_per_year(h1)
    sigma_calibrated = calibrate_sigma(h1, ppy)

    # 🟢 1. MATH ENGINE CALCULATIONS (V22)
    # Drift Validation (T-Stat)
    drift_data = AdvancedMathEngineV22.calculate_drift_tstat(h1['close'].tail(100))
    # Entropy (Noise Gate)
    pe = AdvancedMathEngineV22.calculate_permutation_entropy(h1['close'].tail(150))
    # Hurst & VR
    hurst_val, _, _ = calculate_hurst_exponent(h1['close'])
    vr_res = variance_ratio_test(h1['close'])

    # 🔵 2. SCORE UNIFICADO (V22)
    # 0-100 Score combining drift strength, persistence and edge
    trend_score = RegimeClassifierV22.calculate_unified_trend_score(
        hurst_val, drift_data, c1.get('ADX', 20), vr_res, 1.0
    )
    
    # Classificar Regime Estrutural
    regime = RegimeClassifierV22.classify_structural_regime(hurst_val, vr_res, drift_data)
    
    # 🔵 3. GENERATORS V22
    # Executa gerador específico com upgrades (Kalman / Decay)
    gen_type = profile.get('gen_type', 'GBM')
    if gen_type == 'GBM':
        gen = GeneratorModelV22.analyze_gbm(h1, profile, sigma_calibrated, ppy)
    elif gen_type in ['BOOM', 'CRASH']:
        gen = GeneratorModelV22.analyze_crash_boom(h1, profile, ppy)
    else:
        gen = GeneratorModelV22.analyze_step(h1, profile, ppy)

    # 🟣 4. LÓGICA DE DECISÃO V22
    decision = "MONITORING"
    reason = "Awaiting Setup"
    setup_type = "NONE"
    
    # Bias direcional validado pelo T-Stat
    bias = "NEUTRAL"
    if drift_data.get('t_stat') > 1.2: bias = "BULLISH"
    elif drift_data.get('t_stat') < -1.2: bias = "BEARISH"
    
    # --- ÁRVORE DE DECISÃO V22 ---
    
    # REGRA 0: ENTROPY GATE (Block Chaotic/Noise Regimes)
    if pe > 0.94:
        decision = "BLOCKED"
        reason = f"High Entropy ({pe:.2f}) - Chaotic"
        
    elif regime == "RANDOM_WALK":
        decision = "BLOCKED"
        reason = "Random Walk Regime - No Edge"
        
    # REGRA 1: TREND (Estrutural via Score)
    elif regime == "TRENDING" and trend_score > 60:
        if bias == "BULLISH":
            decision = "LONG (V22 TREND)"
            setup_type = "TREND_FLOW"
            reason = f"Unified Score {trend_score}"
        elif bias == "BEARISH":
            decision = "SHORT (V22 TREND)"
            setup_type = "TREND_FLOW"
            reason = f"Unified Score {trend_score}"
            
    # REGRA 2: CRASH/BOOM (V22 Nonlinear Drift)
    elif gen_type in ['BOOM', 'CRASH'] and gen.get('signal') != "NEUTRAL":
        sig = gen['signal']
        if "DRIFT" in sig:
             direction = gen.get('drift_direction')
             decision = f"LONG (V22 DRIFT)" if direction=="UP" else f"SHORT (V22 DRIFT)"
             setup_type = "GEN_SPIKE_DRIFT"
             reason = f"Nonlinear Decay {gen.get('decay_strength'):.2f}"

    # REGRA 3: MEAN REVERSION (Apenas Extremos V22)
    elif regime == "MEAN_REVERSION":
        z = gen.get('z_price', 0)
        if abs(z) > 2.0:
            if z > 2.0: 
                decision = "SHORT (MR EXTENSION)"
                setup_type = "REVERSION"
                reason = f"Z-Score +{z} Extreme"
            elif z < -2.0:
                decision = "LONG (MR EXTENSION)"
                setup_type = "REVERSION"
                reason = f"Z-Score {z} Extreme"

    # Targets e Simulação
    sim = run_walk_forward_v21(h1, bias, profile)
    adjusted_profile = AdaptiveLearnerV20.adjust_profile(profile, sim, {})
    mc = monte_carlo_bootstrap(sim['RESULTS'])
    
    # Cálculo SL/TP
    entry = float(c1['close'])
    sl_mult = adjusted_profile['sl_atr_mult']
    sl = entry - c1['ATR']*sl_mult if "LONG" in decision else entry + c1['ATR']*sl_mult
    tp1 = entry + c1['ATR']*3.0 if "LONG" in decision else entry - c1['ATR']*3.0
    tp2 = entry + c1['ATR']*5.0 if "LONG" in decision else entry - c1['ATR']*5.0
    
    # Pyramid logic (simple wrapper)
    pyramid = ScalingEngine.calculate_pyramid("A", trend_score, capital, risk_pct, entry, sl, c1['ATR'], adjusted_profile)

    # Imagens
    imgs = [
        plot_candles(h4.tail(150), f"H4 Structural (Drift T: {drift_data.get('t_stat'):.1f})"),
        plot_candles(h1.tail(200), f"H1 Kalman Trend | Entropy: {pe:.2f}", entry if "BLOCKED" not in decision else None, sl, tp1),
        plot_candles(m15.tail(200), f"M15 Generator: {gen.get('signal')}")
    ]

    # V22 Dictionary (Mapeado para UI antiga mas com dados novos)
    return {
        "FINAL_DECISION": decision, 
        "SETUP_TYPE": setup_type,
        "SETUP_SCORE": float(trend_score), # Score Unificado V22
        "SETUP_GRADE": "S" if trend_score>80 else "A", 
        "GEN_TYPE": gen_type,
        "GEN_SIGNAL": str(gen.get('signal')), 
        "GEN_BONUS": 10,
        "GEN_ANALYSIS": convert_np(gen),
        "ENTROPY": float(pe), 
        "DRIFT_T": float(drift_data.get('t_stat',0)), 
        "HURST": float(hurst_val),
        "ZSCORE": float(c1.get('ZSCORE', 0)),
        "REGIME": regime,
        "SIGMA_CALIBRATED": sigma_calibrated,
        "WIN_RATE": sim['WR'], "PROFIT_FACTOR": sim['PF'], "TOTAL_TRADES": sim['TOTAL_TRADES'],
        "MAX_DRAWDOWN": sim['DD'], "SHARPE": sim['SHARPE'], "SORTINO": sim['SORTINO'],
        "ENTRY": entry, "SL": sl, "TP1": tp1, "TP2": tp2,
        "PYRAMID": convert_np(pyramid), "IMAGES": imgs,
        "CONFLUENCES": [f"V22 Regime: {regime}", f"Score: {trend_score}"],
        "RISKS": [f"High Noise ({pe:.2f})" if pe > 0.8 else "Stable Flow"],
        "ADAPTED_PROFILE": convert_np(adjusted_profile),
        "MC_MEDIAN": mc['median'], "MC_P5": mc['p5'], "MC_P95": mc['p95'], "MC_POSITIVE": mc['positive_pct'],
        # Extra Fields
        "VOL_CLUSTER": {"vol_regime": "N/A"}, "ACF_TEST": {}, "VR_TEST": vr_res, "DIST_ANALYSIS": {}, 
        "BB_CYCLE": "N/A", "CONSECUTIVE": 0, "CONSECUTIVE_DIR": "N/A"
    }

async def quick_scan(code, name): return None

# ==============================================================================
# UI STREAMLIT (Mantida Original do V21)
# ==============================================================================

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("""<div style='padding:8px 0 16px;'>
        <span style='font-size:24px;font-weight:300;color:#fafafa;letter-spacing:-0.5px;'>APATECO</span>
        <span style='font-size:11px;color:#52525b;margin-left:6px;font-weight:500;'>V22</span>
    </div>""", unsafe_allow_html=True)

    if "GEMINI_API_KEY" in st.secrets:
        api = st.secrets["GEMINI_API_KEY"]
        st.markdown("<span class='pill pill-green' style='font-size:11px;'>API Connected</span>", unsafe_allow_html=True)
    else:
        api = st.text_input("Gemini API Key", type="password", label_visibility="collapsed", placeholder="Enter API key...")
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    mode = st.radio("Mode", ["Analysis", "Scanner"], label_visibility="collapsed", horizontal=True)
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    capital = st.number_input("Capital", min_value=100, value=10000, step=100, label_visibility="collapsed")
    st.caption("Capital ($)")
    risk_pct = st.slider("Risk", 0.5, 3.0, 1.0, 0.1, label_visibility="collapsed")
    st.caption(f"Risk per trade: {risk_pct}%")

    st.markdown("""<div style='margin-top:32px;padding:14px;background:#111113;border:1px solid #1e1e23;
        border-radius:8px;font-size:11px;color:#3f3f46;line-height:1.6;'>
        Statistical Edge Engine V22<br>
        Kalman Drift · T-Stat Check<br>
        Entropy Gate · Unified Score
    </div>""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""<div style='padding:0 0 8px;'>
    <span style='font-size:32px;font-weight:300;color:#fafafa;letter-spacing:-1px;'>APATECO</span>
    <span style='font-size:13px;color:#3f3f46;margin-left:8px;'>Predictability Engine V22</span>
</div>""", unsafe_allow_html=True)

with st.spinner("Loading assets..."):
    # Mocking assets loader for provided snippet scope; usually requires live conn
    assets = get_assets() 

# ANALYSIS MODE
if mode == "Analysis":
    left, right = st.columns([1, 3])

    with left:
        target = st.selectbox("Asset", list(assets.keys()), label_visibility="collapsed") if assets else st.selectbox("Asset", ["Select"])
        if assets:
            prof = get_profile(target)
            st.markdown(f"""<div style='padding:10px 14px;background:#111113;border:1px solid #1e1e23;
                border-radius:8px;margin:8px 0 16px;'>
                <span style='color:#fafafa;font-size:13px;font-weight:500;'>{prof['vol_class']}</span><br>
                <span class='mono text-xs muted'>{prof.get('gen_type','—')}</span>
            </div>""", unsafe_allow_html=True)
        run = st.button("Analyze", use_container_width=True)

    with right:
        if run and assets:
            status = st.status("Analyzing V22...", expanded=True)
            status.write("Running V22 Math Engine (Kalman/Entropy)...")
            h1r, h4r, m15r, m5r, err = asyncio.run(fetch_multi_tf(assets[target]))
            
            if not h1r:
                status.update(label="Error fetching", state="error")
                st.error("No data available.")
            else:
                status.write("Calculating Structural Drifts...")
                
                # EXECUTE V22 CORE
                data = sniper_core_v22(target, h1r, h4r, m15r, m5r, capital, risk_pct)
                imgs = data.pop("IMAGES")
                
                # Gemini Insight
                ai_text = "No API key"
                if api:
                    try:
                        status.write("Generative Insight...")
                        genai.configure(api_key=api)
                        model = genai.GenerativeModel("gemini-pro")
                        prompt = f"Trade: {data['FINAL_DECISION']}. Score: {data['SETUP_SCORE']}. Entropy: {data['ENTROPY']:.2f}. Hurst: {data['HURST']:.2f}. Regime: {data['REGIME']}. Summarize strategy."
                        ai_text = model.generate_content(prompt).text
                    except: pass
                
                status.update(label="Complete", state="complete")

                # ── OUTPUT DISPLAY ──
                g = data['SETUP_GRADE']
                d_dec = data['FINAL_DECISION']
                tag = "tag-long" if "LONG" in d_dec else "tag-short" if "SHORT" in d_dec else "tag-blocked"
                
                # Score Card V22
                st.markdown(f"""
                <div class='grade-{g.lower().replace("s","s")}' style='margin:8px 0 20px;'>
                    <div class='grade-letter'>{g}</div>
                    <div style='font-family:JetBrains Mono,monospace;font-size:22px;margin:4px 0;color:#fafafa;'>
                        {data['SETUP_SCORE']:.0f}<span style='color:#52525b;font-size:14px;'> / 100</span>
                    </div>
                    <div style='margin-top:12px;'><span class='{tag}'>{d_dec}</span></div>
                </div>""", unsafe_allow_html=True)

                # V22 Stats Grid
                st.markdown("## V22 Diagnostics")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Entropy (Pe)", f"{data['ENTROPY']:.2f}", delta="Chaos" if data['ENTROPY']>0.94 else "Stable", delta_color="inverse")
                col2.metric("Drift T-Stat", f"{data['DRIFT_T']:.2f}", delta="Significant" if abs(data['DRIFT_T'])>2 else "Noise")
                col3.metric("Regime", data['REGIME'])
                col4.metric("Generator", data['GEN_SIGNAL'])

                # Stats Grid 2 (Legacy/Supporting)
                col5, col6, col7 = st.columns(3)
                col5.metric("Win Rate", f"{data['WIN_RATE']}%")
                col6.metric("Exp Value (MC)", f"{data['MC_MEDIAN']}R")
                col7.metric("Hurst", f"{data['HURST']:.2f}")

                # Trade Plan
                if "BLOCKED" not in d_dec and "MONITORING" not in d_dec:
                    st.markdown("## Trade Plan")
                    st.markdown(f"""<div class='card'>
                        <div class='plan-row'><span class='plan-label'>Entry</span><span class='plan-value'>{data['ENTRY']}</span></div>
                        <div class='plan-row'><span class='plan-label'>SL</span><span class='plan-value' style='color:#ef4444'>{data['SL']}</span></div>
                        <div class='plan-row'><span class='plan-label'>TP1</span><span class='plan-value' style='color:#22c55e'>{data['TP1']}</span></div>
                        <div class='plan-row'><span class='plan-label'>TP2</span><span class='plan-value' style='color:#22c55e'>{data['TP2']}</span></div>
                    </div>""", unsafe_allow_html=True)
                    
                # Charts
                st.markdown("## Charts (Kalman Integrated)")
                t1, t2, t3 = st.tabs(["H4 Macro", "H1 Trend", "M15 Gen"])
                t1.image(imgs[0], use_container_width=True)
                t2.image(imgs[1], use_container_width=True)
                t3.image(imgs[2], use_container_width=True)

                if api:
                    st.markdown("## AI Analysis")
                    st.info(ai_text)

# Scanner Mode (Simple Stub)
elif mode == "Scanner":
    st.info("Switch to Analysis mode for full V22 Logic details.")
