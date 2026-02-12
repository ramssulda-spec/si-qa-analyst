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
from scipy.stats import norm, median_abs_deviation
import time
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# SI-APATECO V20.0 — STATISTICAL EDGE ENGINE
#
# ANÁLISE CIRÚRGICA V19 → 20 CORREÇÕES IMPLEMENTADAS:
#
# 🔴 BUG FIX #1: periods_per_year auto-detectado (não hardcoded)
# 🔴 BUG FIX #2: VOL_COMPRESS direção CONTRA o movimento recente
# 🔴 BUG FIX #3: Crash/Boom drift segue cálculo real (não bias)
# 🔴 BUG FIX #4: Backtest por TIPO DE SETUP (não só Swing)
# 🔴 BUG FIX #5: Backtest roda 1× (não 2×)
# 🔴 BUG FIX #6: Monte Carlo bootstrap REAL (não distribuição inventada)
#
# 🟠 MATH FIX #1: Sigma calibrado do histórico (não inventado)
# 🟠 MATH FIX #2: Hurst com validação R²
# 🟠 MATH FIX #3: Step Index escala correta (log-returns, não step_size)
# 🟠 MATH FIX #4: Spike detection MAD-based (não std circular)
# 🟠 MATH FIX #5: Crash/Boom drift por REGRESSÃO LINEAR (não média)
#
# 🟡 EDGE #1: Variance Ratio Test (detecta se há edge real)
# 🟡 EDGE #2: Autocorrelação de Retornos (lag 1-5)
# 🟡 EDGE #3: Volatility Clustering (GARCH effect)
# 🟡 EDGE #4: Multi-TF Vol Ratio
# 🟡 EDGE #5: Spike Decay Model (Crash/Boom timing)
# 🟡 EDGE #6: Preço Teórico vs Real (GBM z-score)
# 🟡 EDGE #7: Regime-Specific Strategy Selection
# 🟡 EDGE #8: Entry Trigger Candle Confirmation
#
# 🟢 PRECISION #1: Multi-Window Vol Analysis (3 janelas)
# 🟢 PRECISION #2: Trailing Stop por regime/tipo
# 🟢 PRECISION #3: Dynamic TP com S/R awareness
# 🟢 PRECISION #4: Scanner para TODOS gen types
# 🟢 PRECISION #5: Adaptive Kelly Criterion (não if/elif)
# 🟢 PRECISION #6: M5 entry timing
# ==============================================================================

st.set_page_config(
    page_title="SI-APATECO V20.0 STATISTICAL EDGE",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Teko:wght@300;600&family=Share+Tech+Mono&display=swap');
    .stApp { background-color:#050505; background-image:linear-gradient(0deg,#000 0%,#0a0a0a 100%); color:#d4d4d4; font-family:'Share Tech Mono',monospace; }
    h1,h2,h3 { font-family:'Teko',sans-serif!important; text-transform:uppercase; color:#fbbf24; letter-spacing:3px; text-shadow:0 0 10px rgba(251,191,36,0.3); }
    div[data-testid="stMetric"] { background-color:#111; border-right:4px solid #fbbf24; padding:15px; }
    .stButton>button { background:linear-gradient(45deg,#d97706,#fbbf24); color:black; font-weight:900; text-transform:uppercase; padding:20px; font-size:20px; border-radius:0px; width:100%; border:1px solid #fbbf24; }
    .stButton>button:hover { box-shadow:0 0 30px rgba(251,191,36,0.6); transform:scale(1.02); }
    .score-s { color:#a855f7; font-weight:900; font-size:32px; animation:pulse 2s infinite; }
    .score-a-pp { color:#10b981; font-weight:900; font-size:30px; }
    .score-a-p { color:#3b82f6; font-weight:900; font-size:28px; }
    .score-a { color:#22d3ee; font-weight:900; font-size:26px; }
    .score-b { color:#fbbf24; font-weight:900; font-size:24px; }
    .score-c { color:#6b7280; font-weight:900; font-size:22px; }
    @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.7;} }
    .health-exc { background:linear-gradient(90deg,#10b981,#059669); color:white; padding:15px; border-radius:8px; font-weight:bold; }
    .health-good { background:linear-gradient(90deg,#3b82f6,#2563eb); color:white; padding:15px; border-radius:8px; font-weight:bold; }
    .health-warn { background:linear-gradient(90deg,#f59e0b,#d97706); color:white; padding:15px; border-radius:8px; font-weight:bold; }
    .health-danger { background:linear-gradient(90deg,#ef4444,#dc2626); color:white; padding:15px; border-radius:8px; font-weight:bold; animation:blink 1s infinite; }
    @keyframes blink { 0%,50%,100%{opacity:1;} 25%,75%{opacity:0.5;} }
    .gen-model { background:rgba(168,85,247,0.1); border-left:4px solid #a855f7; padding:15px; margin:10px 0; border-radius:0 8px 8px 0; }
    .edge-card { background:rgba(16,185,129,0.08); border:1px solid #10b981; padding:12px; border-radius:8px; margin:5px 0; }
    .bug-fixed { background:rgba(239,68,68,0.05); border-left:3px solid #10b981; padding:8px; margin:3px 0; font-size:12px; }
</style>
""", unsafe_allow_html=True)

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# PERFIS — sigma_annual será CALIBRADO dos dados reais (MATH FIX #1)
# Os valores aqui são SEEDS iniciais, substituídos pela calibração
# ==============================================================================

SYNTHETIC_PROFILES = {
    "VOLATILITY 10 INDEX": {
        "gen_type": "GBM", "vol_class": "ULTRA_LOW", "sigma_seed": 0.10,
        "spread": 0.02, "adx_trend_min": 12, "adx_strong": 20,
        "sl_atr_mult": 2.0, "tp1_r": 2.5, "tp2_r": 4.0,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 2.5,
        "hurst_trend_min": 0.55, "consecutive_reversal": 8,
        "roc_extreme_pct": 0.3, "mean_reversion_bias": 0.7, "risk_mult": 1.3,
    },
    "VOLATILITY 10 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "ULTRA_LOW", "sigma_seed": 0.10,
        "spread": 0.02, "adx_trend_min": 12, "adx_strong": 20,
        "sl_atr_mult": 2.0, "tp1_r": 2.5, "tp2_r": 4.0,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 2.5,
        "hurst_trend_min": 0.55, "consecutive_reversal": 8,
        "roc_extreme_pct": 0.3, "mean_reversion_bias": 0.7, "risk_mult": 1.3,
    },
    "VOLATILITY 25 INDEX": {
        "gen_type": "GBM", "vol_class": "LOW", "sigma_seed": 0.25,
        "spread": 0.03, "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 2.2, "tp1_r": 2.5, "tp2_r": 4.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 2.3,
        "hurst_trend_min": 0.54, "consecutive_reversal": 7,
        "roc_extreme_pct": 0.5, "mean_reversion_bias": 0.6, "risk_mult": 1.2,
    },
    "VOLATILITY 25 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "LOW", "sigma_seed": 0.25,
        "spread": 0.03, "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 2.2, "tp1_r": 2.5, "tp2_r": 4.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 2.3,
        "hurst_trend_min": 0.54, "consecutive_reversal": 7,
        "roc_extreme_pct": 0.5, "mean_reversion_bias": 0.6, "risk_mult": 1.2,
    },
    "VOLATILITY 50 INDEX": {
        "gen_type": "GBM", "vol_class": "MEDIUM", "sigma_seed": 0.50,
        "spread": 0.05, "adx_trend_min": 16, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.53, "consecutive_reversal": 6,
        "roc_extreme_pct": 0.8, "mean_reversion_bias": 0.5, "risk_mult": 1.0,
    },
    "VOLATILITY 50 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "MEDIUM", "sigma_seed": 0.50,
        "spread": 0.05, "adx_trend_min": 16, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.53, "consecutive_reversal": 6,
        "roc_extreme_pct": 0.8, "mean_reversion_bias": 0.5, "risk_mult": 1.0,
    },
    "VOLATILITY 75 INDEX": {
        "gen_type": "GBM", "vol_class": "HIGH", "sigma_seed": 0.75,
        "spread": 0.10, "adx_trend_min": 18, "adx_strong": 28,
        "sl_atr_mult": 3.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.65, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 1.2, "mean_reversion_bias": 0.4, "risk_mult": 0.7,
    },
    "VOLATILITY 75 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "HIGH", "sigma_seed": 0.75,
        "spread": 0.10, "adx_trend_min": 18, "adx_strong": 28,
        "sl_atr_mult": 3.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.65, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 1.2, "mean_reversion_bias": 0.4, "risk_mult": 0.7,
    },
    "VOLATILITY 100 INDEX": {
        "gen_type": "GBM", "vol_class": "EXTREME", "sigma_seed": 1.00,
        "spread": 0.15, "adx_trend_min": 20, "adx_strong": 30,
        "sl_atr_mult": 3.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.7, "zscore_extreme": 1.5,
        "hurst_trend_min": 0.51, "consecutive_reversal": 4,
        "roc_extreme_pct": 1.5, "mean_reversion_bias": 0.35, "risk_mult": 0.5,
    },
    "VOLATILITY 100 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "EXTREME", "sigma_seed": 1.00,
        "spread": 0.15, "adx_trend_min": 20, "adx_strong": 30,
        "sl_atr_mult": 3.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.7, "zscore_extreme": 1.5,
        "hurst_trend_min": 0.51, "consecutive_reversal": 4,
        "roc_extreme_pct": 1.5, "mean_reversion_bias": 0.35, "risk_mult": 0.5,
    },
    "BOOM 300 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/300, "spike_direction": "UP", "drift_direction": "DOWN",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.8,
    },
    "BOOM 500 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/500, "spike_direction": "UP", "drift_direction": "DOWN",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.8,
    },
    "BOOM 1000 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/1000, "spike_direction": "UP", "drift_direction": "DOWN",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.9,
    },
    "CRASH 300 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/300, "spike_direction": "DOWN", "drift_direction": "UP",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.8,
    },
    "CRASH 500 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/500, "spike_direction": "DOWN", "drift_direction": "UP",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.8,
    },
    "CRASH 1000 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/1000, "spike_direction": "DOWN", "drift_direction": "UP",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.9,
    },
    "STEP INDEX": {
        "gen_type": "STEP", "vol_class": "STEP", "sigma_seed": 0.20,
        "spread": 0.01, "adx_trend_min": 10, "adx_strong": 18,
        "sl_atr_mult": 1.5, "tp1_r": 2.0, "tp2_r": 3.0,
        "bb_squeeze_threshold": 0.4, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.55, "consecutive_reversal": 10,
        "roc_extreme_pct": 0.2, "mean_reversion_bias": 0.8, "risk_mult": 1.5,
    },
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

# ==============================================================================
# 🔴 BUG FIX #1: AUTO-DETECT TIMEFRAME
# ==============================================================================

def detect_periods_per_year(df):
    """Detecta timeframe automaticamente e retorna períodos/ano corretos.
    Sintéticos operam 24/7/365, não 252 dias."""
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

# ==============================================================================
# 🟠 MATH FIX #1: CALIBRAR SIGMA REAL DO HISTÓRICO
# ==============================================================================

def calibrate_sigma(df, periods_per_year):
    """Calcula sigma REAL do ativo a partir de todo o histórico disponível.
    Usa toda a série como referência — NÃO assume que Vol10 = 0.10."""
    try:
        log_ret = np.log(df['close'] / df['close'].shift(1)).dropna()
        if len(log_ret) < 50:
            return None
        return float(log_ret.std() * np.sqrt(periods_per_year))
    except:
        return None

# ==============================================================================
# GENERATOR MODELS V20 — TODOS OS BUGS CORRIGIDOS
# ==============================================================================

class GeneratorModelV20:
    """V20: Modela o gerador com sigma calibrado, direction-aware, multi-window"""

    @staticmethod
    def analyze_gbm(df, profile, sigma_calibrated, ppy):
        """
        🔴 FIX #2: VOL_COMPRESS agora sabe a DIREÇÃO (contra movimento recente)
        🟠 FIX #1: Usa sigma calibrado, não inventado
        🔴 FIX #1: periods_per_year auto-detectado
        🟢 PRECISION #1: Multi-window (30, 100, 300)
        🟡 EDGE #6: Preço teórico vs real
        """
        try:
            log_returns = np.log(df['close'] / df['close'].shift(1)).dropna()
            sigma_ref = sigma_calibrated if sigma_calibrated else profile.get('sigma_seed', 0.5)
            results = {}

            # 🟢 MULTI-WINDOW ANALYSIS
            for label, window in [("SHORT", 30), ("MEDIUM", 100), ("LONG", min(300, len(log_returns)-1))]:
                if len(log_returns) < window:
                    results[label] = {"vol_ratio": 1.0, "signal": "NEUTRAL", "confidence": 0}
                    continue
                recent = log_returns.tail(window)
                vol_realized = float(recent.std() * np.sqrt(ppy))
                ratio = vol_realized / sigma_ref if sigma_ref > 0 else 1.0

                # Chi² test correto
                expected_var = (sigma_ref / np.sqrt(ppy)) ** 2
                observed_var = float(recent.var())
                chi2 = (window - 1) * observed_var / expected_var if expected_var > 0 else window
                z_chi = (chi2 - (window - 1)) / np.sqrt(2 * (window - 1))
                p_value = 2 * (1 - norm.cdf(abs(z_chi)))

                if ratio > 1.3:
                    signal = "VOL_COMPRESS"
                    confidence = min((ratio - 1.0) / 0.5, 1.0) * 100
                elif ratio < 1.0 / 1.3:
                    signal = "VOL_EXPAND"
                    confidence = min((1.0 / ratio - 1.0) / 0.5, 1.0) * 100
                else:
                    signal = "VOL_NORMAL"
                    confidence = 0

                results[label] = {
                    "vol_ratio": round(ratio, 3), "vol_realized": round(vol_realized, 4),
                    "signal": signal, "confidence": round(confidence, 1),
                    "p_value": round(p_value, 4), "z_chi": round(z_chi, 2),
                }

            # CONSENSUS: multi-window agreement
            signals = [r['signal'] for r in results.values()]
            if all(s == "VOL_COMPRESS" for s in signals):
                consensus = "VOL_COMPRESS"
                consensus_confidence = min(sum(r['confidence'] for r in results.values()) / 3 * 1.5, 100)
            elif all(s == "VOL_EXPAND" for s in signals):
                consensus = "VOL_EXPAND"
                consensus_confidence = min(sum(r['confidence'] for r in results.values()) / 3 * 1.5, 100)
            elif signals.count("VOL_COMPRESS") >= 2:
                consensus = "VOL_COMPRESS"
                consensus_confidence = min(sum(r['confidence'] for r in results.values() if r['signal']=="VOL_COMPRESS") / 2, 100)
            elif signals.count("VOL_EXPAND") >= 2:
                consensus = "VOL_EXPAND"
                consensus_confidence = min(sum(r['confidence'] for r in results.values() if r['signal']=="VOL_EXPAND") / 2, 100)
            else:
                consensus = "VOL_NORMAL"
                consensus_confidence = 0

            # 🔴 BUG FIX #2: DIREÇÃO CONTRA O MOVIMENTO RECENTE
            lookback = min(100, len(df) - 1)
            recent_move = float(df['close'].iloc[-1] - df['close'].iloc[-lookback])
            if consensus == "VOL_COMPRESS":
                compress_direction = "BEARISH" if recent_move > 0 else "BULLISH"
            else:
                compress_direction = "NEUTRAL"

            # 🟡 EDGE #6: PREÇO TEÓRICO VS REAL
            lookback_price = min(200, len(df) - 1)
            start_price = float(df['close'].iloc[-lookback_price])
            current_price = float(df['close'].iloc[-1])
            t_years = lookback_price / ppy
            expected_var_price = sigma_ref**2 * t_years
            actual_log_dev = np.log(current_price / start_price) if start_price > 0 else 0
            z_price = actual_log_dev / np.sqrt(expected_var_price) if expected_var_price > 0 else 0

            return {
                "windows": results,
                "consensus": consensus,
                "consensus_confidence": round(consensus_confidence, 1),
                "compress_direction": compress_direction,
                "recent_move": round(recent_move, 4),
                "sigma_calibrated": round(sigma_ref, 4),
                "z_price": round(z_price, 2),
                "price_deviation_signal": "OVERBOUGHT" if z_price > 2 else "OVERSOLD" if z_price < -2 else "NORMAL",
                "vol_ratio": results.get("MEDIUM", {}).get("vol_ratio", 1.0),
                "signal": consensus,
                "confidence": consensus_confidence,
            }
        except:
            return {"windows": {}, "consensus": "NEUTRAL", "consensus_confidence": 0,
                    "compress_direction": "NEUTRAL", "sigma_calibrated": 0,
                    "z_price": 0, "signal": "NEUTRAL", "confidence": 0, "vol_ratio": 1.0}

    @staticmethod
    def analyze_crash_boom(df, profile, ppy):
        """
        🟠 FIX #4: MAD-based spike detection (não std circular)
        🟠 FIX #5: Drift por REGRESSÃO LINEAR (não média)
        🟡 EDGE #5: Spike Decay Model
        🔴 FIX #3: Drift direction calculada, não hardcoded
        """
        try:
            window = min(300, len(df) - 1)
            if window < 50:
                return {"signal": "NEUTRAL", "spikes_found": 0, "drift_direction": "UNKNOWN",
                        "drift_slope": 0, "last_spike_bars": 999, "spike_phase": "UNKNOWN", "decay_strength": 0}

            recent = df.tail(window)
            returns = recent['close'].pct_change().dropna()
            is_boom = profile.get('gen_type') == 'BOOM'

            # 🟠 FIX #4: MAD-BASED SPIKE DETECTION
            mad = float(median_abs_deviation(returns.values, scale='normal'))
            spike_threshold = mad * 4.5 if mad > 0 else returns.std() * 3.5

            spike_indices = []
            for i in range(len(returns)):
                r = returns.iloc[i]
                if is_boom and r > spike_threshold:
                    spike_indices.append(i)
                elif not is_boom and r < -spike_threshold:
                    spike_indices.append(i)

            last_spike_bars = (len(returns) - spike_indices[-1]) if spike_indices else 999

            # 🟠 FIX #5: DRIFT POR REGRESSÃO LINEAR
            slopes = []
            if len(spike_indices) >= 2:
                for si in range(len(spike_indices) - 1):
                    start_idx = spike_indices[si] + 3  # após absorção
                    end_idx = spike_indices[si + 1]
                    if end_idx - start_idx > 5:
                        segment = recent['close'].iloc[start_idx:end_idx].values
                        x = np.arange(len(segment))
                        try:
                            slope = np.polyfit(x, segment, 1)[0]
                            norm_slope = slope / recent['close'].iloc[start_idx] if recent['close'].iloc[start_idx] > 0 else 0
                            slopes.append(norm_slope)
                        except:
                            pass

            # Também calcular drift do segmento ATUAL (após último spike)
            if spike_indices:
                current_start = spike_indices[-1] + 3
                if current_start < len(recent) - 5:
                    current_segment = recent['close'].iloc[current_start:].values
                    x = np.arange(len(current_segment))
                    try:
                        current_slope = np.polyfit(x, current_segment, 1)[0]
                        current_norm_slope = current_slope / recent['close'].iloc[current_start]
                        slopes.append(current_norm_slope)
                    except:
                        pass

            drift_slope = float(np.median(slopes)) if slopes else 0
            drift_direction = "UP" if drift_slope > 0 else "DOWN" if drift_slope < 0 else "FLAT"
            drift_strength = abs(drift_slope) * 10000  # Normalizar para legibilidade

            avg_between = window / max(len(spike_indices), 1)

            # 🟡 EDGE #5: SPIKE DECAY MODEL
            progress = last_spike_bars / avg_between if avg_between > 0 else 0
            if progress < 0.05:
                spike_phase = "ABSORBING"
                decay_strength = 0
            elif progress < 0.15:
                spike_phase = "DRIFT_STRONG"
                decay_strength = drift_strength * 1.5
            elif progress < 0.5:
                spike_phase = "DRIFT_NORMAL"
                decay_strength = drift_strength * 1.0
            elif progress < 0.8:
                spike_phase = "DRIFT_WEAKENING"
                decay_strength = drift_strength * 0.5
            else:
                spike_phase = "SPIKE_IMMINENT"
                decay_strength = 0

            # Signal
            if spike_phase in ["DRIFT_STRONG", "DRIFT_NORMAL"] and drift_strength > 0.5:
                signal = f"DRIFT_{drift_direction}"
            elif spike_phase == "ABSORBING":
                signal = "SPIKE_RECOVERY"
            elif spike_phase == "SPIKE_IMMINENT":
                signal = "SPIKE_WARNING"
            else:
                signal = "NEUTRAL"

            return {
                "signal": signal,
                "spikes_found": len(spike_indices),
                "drift_direction": drift_direction,
                "drift_slope": round(drift_slope * 10000, 4),
                "drift_strength": round(drift_strength, 3),
                "last_spike_bars": last_spike_bars,
                "avg_bars_between": round(avg_between, 0),
                "spike_phase": spike_phase,
                "progress": round(progress, 2),
                "decay_strength": round(decay_strength, 3),
                "confidence": min(drift_strength * 30, 100) if signal != "NEUTRAL" else 0,
            }
        except:
            return {"signal": "NEUTRAL", "spikes_found": 0, "drift_direction": "UNKNOWN",
                    "drift_slope": 0, "last_spike_bars": 999, "spike_phase": "UNKNOWN",
                    "decay_strength": 0, "confidence": 0}

    @staticmethod
    def analyze_step(df, profile, ppy):
        """
        🟠 FIX #3: Escala correta (log-returns, não step_size em candles)
        """
        try:
            window = min(300, len(df) - 1)
            if window < 50:
                return {"signal": "NEUTRAL", "deviation_sigma": 0, "runs_test": "NORMAL", "runs_z": 0}

            recent = df.tail(window)
            log_ret = np.log(recent['close'] / recent['close'].shift(1)).dropna()

            # Deviation: vol realizada recente vs toda a série
            full_log_ret = np.log(df['close'] / df['close'].shift(1)).dropna()
            full_std = float(full_log_ret.std())
            recent_std = float(log_ret.std()) if len(log_ret) > 10 else full_std

            # Preço: quanto desviou em termos de std acumulado
            price_change = float(recent['close'].iloc[-1] - recent['close'].iloc[0])
            expected_std_price = full_std * np.sqrt(window) * float(recent['close'].iloc[0])
            deviation_sigma = price_change / expected_std_price if expected_std_price > 0 else 0

            # Runs test
            directions = (recent['close'].diff().dropna() > 0).astype(int)
            runs = 1
            for i in range(1, len(directions)):
                if directions.iloc[i] != directions.iloc[i-1]:
                    runs += 1
            n1 = int(directions.sum())
            n0 = len(directions) - n1
            if n0 > 0 and n1 > 0:
                expected_runs = (2 * n0 * n1) / (n0 + n1) + 1
                denom = (n0 + n1)**2 * (n0 + n1 - 1)
                std_runs = np.sqrt(2*n0*n1*(2*n0*n1-n0-n1) / denom) if denom > 0 else 1
                z_runs = (runs - expected_runs) / std_runs if std_runs > 0 else 0
            else:
                z_runs = 0

            runs_test = "CLUSTERING" if z_runs < -2 else "ALTERNATING" if z_runs > 2 else "NORMAL"

            # Vol ratio
            vol_ratio = recent_std / full_std if full_std > 0 else 1.0

            # Signal
            if abs(deviation_sigma) > 2.5:
                signal = "EXTREME_DEVIATION"
            elif abs(deviation_sigma) > 1.5:
                signal = "HIGH_DEVIATION"
            elif runs_test == "CLUSTERING":
                signal = "TREND_CLUSTER"
            elif runs_test == "ALTERNATING":
                signal = "MEAN_REVERT_PATTERN"
            elif vol_ratio > 1.4:
                signal = "VOL_EXPANDING"
            elif vol_ratio < 0.6:
                signal = "VOL_COMPRESSING"
            else:
                signal = "NEUTRAL"

            return {
                "signal": signal,
                "deviation_sigma": round(deviation_sigma, 2),
                "runs_test": runs_test,
                "runs_z": round(z_runs, 2),
                "vol_ratio": round(vol_ratio, 3),
                "price_change": round(price_change, 4),
                "confidence": min(abs(deviation_sigma) * 25, 100) if signal != "NEUTRAL" else 0,
            }
        except:
            return {"signal": "NEUTRAL", "deviation_sigma": 0, "runs_test": "NORMAL",
                    "runs_z": 0, "confidence": 0}

# ==============================================================================
# 🟡 EDGE #1: VARIANCE RATIO TEST — Detecta se há edge real
# ==============================================================================

def variance_ratio_test(series, periods=[2, 5, 10, 20]):
    """Se VR ≠ 1 → NÃO é random walk → há edge explorável.
    VR < 1 = mean-reverting. VR > 1 = trending."""
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
            if len(q_ret) < 20:
                continue
            var_q = float(q_ret.var())
            vr = var_q / (q * var1)
            n = len(log_ret)
            z = (vr - 1) / np.sqrt(2*(2*q-1)*(q-1) / (3*q*n)) if n > 0 else 0
            results[q] = {"vr": round(vr, 4), "z": round(z, 2), "significant": abs(z) > 1.96,
                          "type": "MEAN_REVERT" if vr < 1 and abs(z)>1.96 else "TRENDING" if vr > 1 and abs(z)>1.96 else "RANDOM"}
        sig_results = [r for r in results.values() if r['significant']]
        if not sig_results:
            return {"has_edge": False, "dominant_type": "RANDOM_WALK", "results": results,
                    "best_vr": min((r['vr'] for r in results.values()), default=1.0)}
        types = [r['type'] for r in sig_results]
        dominant = max(set(types), key=types.count)
        return {"has_edge": True, "dominant_type": dominant, "results": results,
                "n_significant": len(sig_results),
                "best_vr": min((r['vr'] for r in results.values()), default=1.0)}
    except:
        return {"has_edge": False, "dominant_type": "RANDOM_WALK", "results": {}}

# ==============================================================================
# 🟡 EDGE #2: AUTOCORRELAÇÃO DE RETORNOS
# ==============================================================================

def autocorrelation_analysis(series, max_lag=5):
    """Autocorrelação significativa → padrão explorável"""
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {"significant_lags": [], "dominant_type": "NOISE", "acf_1": 0}
        sig_threshold = 2 / np.sqrt(len(log_ret))
        results = {}
        for lag in range(1, max_lag + 1):
            acf = float(log_ret.autocorr(lag=lag))
            sig = abs(acf) > sig_threshold
            rtype = "MEAN_REVERT" if acf < -sig_threshold else "MOMENTUM" if acf > sig_threshold else "NOISE"
            results[lag] = {"acf": round(acf, 4), "significant": sig, "type": rtype}
        sig_lags = [lag for lag, r in results.items() if r['significant']]
        types = [results[l]['type'] for l in sig_lags]
        dominant = max(set(types), key=types.count) if types else "NOISE"
        return {"results": results, "significant_lags": sig_lags, "dominant_type": dominant,
                "acf_1": results.get(1, {}).get('acf', 0), "has_pattern": len(sig_lags) > 0}
    except:
        return {"significant_lags": [], "dominant_type": "NOISE", "acf_1": 0, "has_pattern": False}

# ==============================================================================
# 🟡 EDGE #3: VOLATILITY CLUSTERING (GARCH EFFECT)
# ==============================================================================

def volatility_clustering_test(series, window=20):
    """Autocorrelação de retornos absolutos → vol clusters → edge"""
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {"has_clustering": False, "vol_regime": "NORMAL", "acf_abs": 0}
        abs_ret = log_ret.abs()
        acf_abs = float(abs_ret.autocorr(lag=1))
        sig = 2 / np.sqrt(len(abs_ret))
        has_clustering = acf_abs > sig

        current_vol = float(abs_ret.tail(window).mean())
        historical_vol = float(abs_ret.mean())
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0

        if has_clustering:
            if vol_ratio > 1.5:
                regime = "HIGH_VOL_CLUSTER"
            elif vol_ratio < 0.6:
                regime = "LOW_VOL_CLUSTER"
            else:
                regime = "NORMAL_CLUSTER"
        else:
            regime = "NO_CLUSTER"

        return {"has_clustering": has_clustering, "vol_regime": regime,
                "acf_abs": round(acf_abs, 4), "vol_ratio": round(vol_ratio, 3),
                "current_vol": round(current_vol, 6), "historical_vol": round(historical_vol, 6)}
    except:
        return {"has_clustering": False, "vol_regime": "NORMAL", "acf_abs": 0}

# ==============================================================================
# DISTRIBUIÇÃO V20 (mantido do V19, corrigido)
# ==============================================================================

class DistributionAnalyzer:
    @staticmethod
    def analyze(df, window=150):
        try:
            log_returns = np.log(df['close'] / df['close'].shift(1)).dropna()
            if len(log_returns) < window:
                return {"skewness": 0, "kurtosis": 3, "tail_risk": "NORMAL",
                        "percentile": 50, "is_normal": True, "signal": "NEUTRAL"}
            recent = log_returns.tail(window)
            skewness = float(recent.skew())
            kurtosis = float(recent.kurtosis()) + 3
            jb = (window / 6) * (skewness**2 + (1/4)*(kurtosis - 3)**2)
            is_normal = jb < 5.99
            if kurtosis > 5: tail_risk = "FAT_TAILS"
            elif kurtosis > 4: tail_risk = "HEAVY_TAILS"
            elif kurtosis < 2.5: tail_risk = "THIN_TAILS"
            else: tail_risk = "NORMAL"
            z_return = float((recent.iloc[-1] - recent.mean()) / recent.std()) if recent.std() > 0 else 0
            recent_cum = float(recent.tail(10).sum())
            all_windows = [float(log_returns.iloc[i:i+10].sum()) for i in range(0, len(log_returns)-10, 5)]
            percentile = sum(1 for w in all_windows if w < recent_cum) / len(all_windows) * 100 if all_windows else 50
            signal = "NEUTRAL"
            if abs(skewness) > 0.5:
                signal = "POSITIVE_SKEW" if skewness > 0 else "NEGATIVE_SKEW"
            if tail_risk == "FAT_TAILS" and abs(z_return) > 2:
                signal = "EXTREME_TAIL_EVENT"
            return {"skewness": round(skewness, 3), "kurtosis": round(kurtosis, 3),
                    "jarque_bera": round(jb, 2), "is_normal": is_normal, "tail_risk": tail_risk,
                    "z_return": round(z_return, 2), "percentile": round(percentile, 1), "signal": signal}
        except:
            return {"skewness": 0, "kurtosis": 3, "tail_risk": "NORMAL", "percentile": 50,
                    "is_normal": True, "signal": "NEUTRAL"}

# ==============================================================================
# 🟢 PRECISION #5: ADAPTIVE KELLY CRITERION (não if/elif primitivo)
# ==============================================================================

class AdaptiveLearnerV20:
    @staticmethod
    def adjust_profile(profile, bt_results, dist_analysis):
        adjusted = profile.copy()
        if not bt_results or bt_results.get('TOTAL_TRADES', 0) < 5:
            return adjusted
        wr = bt_results.get('WR', 50)
        pf = bt_results.get('PF', 1.0)
        dd = bt_results.get('DD', 0)
        # Kelly Criterion contínuo: f* = (p×b - q) / b
        p = wr / 100
        b = pf if pf > 0 else 1.0
        q = 1 - p
        kelly = (p * b - q) / b if b > 0 else 0
        kelly = max(0.0, min(kelly, 0.25))
        # DD penalty contínuo
        dd_penalty = max(0.3, 1.0 - dd / 20)
        # Risk multiplier
        adjusted['risk_mult'] = round(profile['risk_mult'] * (0.5 + kelly * 2) * dd_penalty, 3)
        adjusted['risk_mult'] = max(0.2, min(adjusted['risk_mult'], 2.5))
        # SL contínuo
        sl_adj = 1.0 + max(0, dd - 5) * 0.03 - max(0, wr - 60) * 0.005
        adjusted['sl_atr_mult'] = round(profile['sl_atr_mult'] * max(0.8, min(sl_adj, 1.3)), 2)
        # TP baseado em kurtosis
        kurt = dist_analysis.get('kurtosis', 3)
        tp_mult = 1.0 + max(0, kurt - 3) * 0.1
        adjusted['tp2_r'] = round(min(profile['tp2_r'] * tp_mult, 10.0), 1)
        return adjusted

# ==============================================================================
# SCALING ENGINE V20 (mantido, funcional)
# ==============================================================================

class ScalingEngine:
    @staticmethod
    def calculate_pyramid(grade, score, capital, risk_pct, entry, sl, atr, profile):
        risk_per_unit = abs(entry - sl)
        if risk_per_unit == 0:
            return {"levels": [{"entry": entry, "risk_pct": risk_pct, "size": 0, "trigger": "BASE"}],
                    "total_risk_pct": risk_pct, "total_size": 0, "n_levels": 1}
        levels = []
        rm = profile.get('risk_mult', 1.0)
        if grade == "S" and score >= 140:
            for mult, rp, off, trig in [(1.5, risk_pct*1.5, 0, "STORM ENTRY"),
                                         (1.0, risk_pct, 0.5, "+0.5 ATR → add (SL→BE)"),
                                         (0.5, risk_pct*0.5, 1.5, "+1.5 ATR → add")]:
                e = entry + atr*off*(1 if entry>sl else -1) if off else entry
                levels.append({"entry": round(e,5), "risk_pct": round(rp,2),
                    "size": round(capital*rp/100*rm/risk_per_unit,2), "trigger": trig})
        elif grade in ["A++","A+"] and score >= 90:
            for mult, rp, off, trig in [(1.0, risk_pct, 0, "BASE ENTRY"),
                                         (0.5, risk_pct*0.5, 0.8, "+0.8 ATR → add (SL→BE)")]:
                e = entry + atr*off*(1 if entry>sl else -1) if off else entry
                levels.append({"entry": round(e,5), "risk_pct": round(rp,2),
                    "size": round(capital*rp/100*rm/risk_per_unit,2), "trigger": trig})
        else:
            levels.append({"entry": round(entry,5), "risk_pct": round(risk_pct,2),
                "size": round(capital*risk_pct/100*rm/risk_per_unit,2), "trigger": "SINGLE ENTRY"})
        return {"levels": levels, "total_risk_pct": round(sum(l['risk_pct'] for l in levels),2),
                "total_size": round(sum(l['size'] for l in levels),2), "n_levels": len(levels)}

# ==============================================================================
# NETWORK — Deriv API
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
    return None

async def fetch_multi_tf(code):
    """H1=800, H4=400, M15=2000, M5=500"""
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
        except:
            continue
    return None, None, None, None, "CONNECTION LOST"

async def fetch_single(code, granularity, count):
    req = {"ticks_history": code, "style": "candles", "granularity": granularity, "count": count, "end": "latest"}
    for url in DERIV_SERVERS:
        res = await socket_req(url, req)
        if res and 'candles' in res: return res['candles']
    return None

# ==============================================================================
# INDICADORES TÉCNICOS (limpo, sem mudanças — funcional)
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

def calculate_rsi_wilder(series, period=14):
    delta = series.diff(); gain = delta.where(delta>0,0.0); loss = -delta.where(delta<0,0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    for i in range(period, len(series)):
        if pd.notna(avg_gain.iloc[i-1]):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1]*(period-1)+gain.iloc[i])/period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1]*(period-1)+loss.iloc[i])/period
    rs = avg_gain / avg_loss.replace(0,np.nan)
    return 100 - (100/(1+rs))

def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_f = df['close'].ewm(span=fast,adjust=False).mean()
    ema_s = df['close'].ewm(span=slow,adjust=False).mean()
    df['MACD'] = ema_f-ema_s; df['MACD_signal'] = df['MACD'].ewm(span=signal,adjust=False).mean()
    df['MACD_hist'] = df['MACD']-df['MACD_signal']; return df

def calculate_adx(df, window=14):
    df['trh']=df['high']-df['low']; df['trc']=abs(df['high']-df['close'].shift()); df['trl']=abs(df['low']-df['close'].shift())
    df['TR']=df[['trh','trc','trl']].max(axis=1)
    df['+DM']=np.where((df['high']>df['high'].shift())&(df['low']<=df['low'].shift()),df['high']-df['high'].shift(),0)
    df['-DM']=np.where((df['low']<df['low'].shift())&(df['high']>=df['high'].shift()),df['low'].shift()-df['low'],0)
    df['+DM']=np.where(df['+DM']>df['-DM'],df['+DM'],0); df['-DM']=np.where(df['-DM']>df['+DM'],df['-DM'],0)
    df['TR_E']=df['TR'].ewm(span=window,adjust=False).mean()
    df['+DM_E']=df['+DM'].ewm(span=window,adjust=False).mean(); df['-DM_E']=df['-DM'].ewm(span=window,adjust=False).mean()
    df['+DI']=(df['+DM_E']/df['TR_E'])*100; df['-DI']=(df['-DM_E']/df['TR_E'])*100
    di_sum=(df['+DI']+df['-DI']).replace(0,np.nan); df['DX']=(abs(df['+DI']-df['-DI'])/di_sum)*100
    df['ADX']=df['DX'].ewm(span=window,adjust=False).mean()
    df.drop(columns=['trh','trc','trl','TR','+DM','-DM','TR_E','+DM_E','-DM_E','DX'],inplace=True); return df

def calculate_zscore(series, window=50):
    mean = series.rolling(window=window).mean(); std = series.rolling(window=window).std()
    return (series-mean)/std.replace(0,np.nan)

# 🟠 MATH FIX #2: HURST COM VALIDAÇÃO R²
def calculate_hurst_exponent(series, max_lag=100):
    try:
        ts = series.dropna().values
        if len(ts) < 50: return 0.5, "RANDOM_WALK", 0.0
        lags = range(10, min(max_lag, len(ts)//3))
        rs_values = []
        for lag in lags:
            n_chunks = len(ts)//lag
            if n_chunks < 1: continue
            rs_lag = []
            for i in range(n_chunks):
                chunk = ts[i*lag:(i+1)*lag]; mean_val = np.mean(chunk); dev = chunk-mean_val
                cum = np.cumsum(dev); R = np.max(cum)-np.min(cum); S = np.std(chunk, ddof=1)
                if S > 0: rs_lag.append(R/S)
            if rs_lag: rs_values.append((np.log(lag), np.log(np.mean(rs_lag))))
        if len(rs_values) < 3: return 0.5, "INSUFFICIENT_DATA", 0.0
        x = np.array([v[0] for v in rs_values]); y = np.array([v[1] for v in rs_values])
        coeffs = np.polyfit(x, y, 1); H = max(0.0, min(1.0, coeffs[0]))
        # R² VALIDATION
        y_pred = coeffs[0]*x + coeffs[1]
        ss_res = np.sum((y-y_pred)**2); ss_tot = np.sum((y-np.mean(y))**2)
        r_squared = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        if r_squared < 0.7:
            return round(H,3), "UNRELIABLE", round(r_squared,3)
        if H > 0.6: regime = "STRONG_TREND"
        elif H > 0.53: regime = "WEAK_TREND"
        elif H > 0.47: regime = "RANDOM_WALK"
        elif H > 0.4: regime = "WEAK_MEAN_REVERT"
        else: regime = "STRONG_MEAN_REVERT"
        return round(H,3), regime, round(r_squared,3)
    except:
        return 0.5, "ERROR", 0.0

def find_pivot_highs(data, order=5):
    pivots = []; values = data.values if hasattr(data,'values') else np.array(data)
    for i in range(order, len(values)-order):
        if np.isnan(values[i]): continue
        if all(values[i]>values[i-j] and values[i]>values[i+j] for j in range(1,order+1)): pivots.append(i)
    return np.array(pivots)

def find_pivot_lows(data, order=5):
    pivots = []; values = data.values if hasattr(data,'values') else np.array(data)
    for i in range(order, len(values)-order):
        if np.isnan(values[i]): continue
        if all(values[i]<values[i-j] and values[i]<values[i+j] for j in range(1,order+1)): pivots.append(i)
    return np.array(pivots)

def detect_divergence(df, indicator='RSI', order=5):
    try:
        if len(df) < (order*2+5) or indicator not in df.columns: return None, 0, ""
        ph=find_pivot_highs(df['high'],order); pl=find_pivot_lows(df['low'],order)
        ih=find_pivot_highs(df[indicator],order); il=find_pivot_lows(df[indicator],order)
        if len(ph)>=2 and len(ih)>=2:
            ph1,ph2=ph[-2],ph[-1]; ih1=ih[np.argmin(np.abs(ih-ph1))]; ih2=ih[np.argmin(np.abs(ih-ph2))]
            if abs(ih1-ph1)<=3 and abs(ih2-ph2)<=3:
                if df['high'].iloc[ph2]>df['high'].iloc[ph1] and df[indicator].iloc[ih2]<df[indicator].iloc[ih1]:
                    s=min((df['high'].iloc[ph2]-df['high'].iloc[ph1])/df['high'].iloc[ph1]*100+(df[indicator].iloc[ih1]-df[indicator].iloc[ih2])/max(df[indicator].iloc[ih1],1)*100,10)
                    if s>1: return "BEARISH_DIVERGENCE",-int(min(s*3,20)),f"Preço HH vs {indicator} LH"
        if len(pl)>=2 and len(il)>=2:
            pl1,pl2=pl[-2],pl[-1]; il1=il[np.argmin(np.abs(il-pl1))]; il2=il[np.argmin(np.abs(il-pl2))]
            if abs(il1-pl1)<=3 and abs(il2-pl2)<=3:
                if df['low'].iloc[pl2]<df['low'].iloc[pl1] and df[indicator].iloc[il2]>df[indicator].iloc[il1]:
                    s=min((df['low'].iloc[pl1]-df['low'].iloc[pl2])/df['low'].iloc[pl1]*100+(df[indicator].iloc[il2]-df[indicator].iloc[il1])/max(abs(df[indicator].iloc[il1]),1)*100,10)
                    if s>1: return "BULLISH_DIVERGENCE",int(min(s*3,20)),f"Preço LL vs {indicator} HL"
        if len(pl)>=2 and len(il)>=2:
            pl1,pl2=pl[-2],pl[-1]; il1=il[np.argmin(np.abs(il-pl1))]; il2=il[np.argmin(np.abs(il-pl2))]
            if abs(il1-pl1)<=3 and abs(il2-pl2)<=3:
                if df['low'].iloc[pl2]>df['low'].iloc[pl1] and df[indicator].iloc[il2]<df[indicator].iloc[il1]:
                    return "HIDDEN_BULLISH",15,"Hidden: HL vs LL"
        if len(ph)>=2 and len(ih)>=2:
            ph1,ph2=ph[-2],ph[-1]; ih1=ih[np.argmin(np.abs(ih-ph1))]; ih2=ih[np.argmin(np.abs(ih-ph2))]
            if abs(ih1-ph1)<=3 and abs(ih2-ph2)<=3:
                if df['high'].iloc[ph2]<df['high'].iloc[ph1] and df[indicator].iloc[ih2]>df[indicator].iloc[ih1]:
                    return "HIDDEN_BEARISH",-15,"Hidden: LH vs HH"
        return None, 0, ""
    except: return None, 0, ""

def detect_sr_clustered(df, window=100, min_touches=3):
    try:
        if len(df)<window or 'ATR' not in df.columns: return []
        recent=df.tail(window); atr=recent['ATR'].iloc[-1]
        if pd.isna(atr) or atr==0: return []
        tolerance=atr*0.3
        hp=find_pivot_highs(recent['high'],3); lp=find_pivot_lows(recent['low'],3)
        prices=sorted([recent['high'].iloc[i] for i in hp]+[recent['low'].iloc[i] for i in lp])
        if not prices: return []
        clusters,current=[],[prices[0]]
        for i in range(1,len(prices)):
            if prices[i]-current[-1]<=tolerance: current.append(prices[i])
            else:
                if len(current)>=min_touches: clusters.append(current)
                current=[prices[i]]
        if len(current)>=min_touches: clusters.append(current)
        cp=df['close'].iloc[-1]
        levels=[{'price':round(np.mean(c),4),'touches':len(c),'type':'RESISTANCE' if np.mean(c)>cp else 'SUPPORT',
                'strength':len(c)+(1 if max(c)-min(c)<tolerance*0.5 else 0),
                'zone_high':round(max(c),4),'zone_low':round(min(c),4)} for c in clusters]
        levels.sort(key=lambda x:x['strength'],reverse=True); return levels[:6]
    except: return []

def calculate_fibonacci(df, lookback=100):
    try:
        if len(df)<lookback: return {},None,None
        recent=df.tail(lookback); hp=find_pivot_highs(recent['high'],7); lp=find_pivot_lows(recent['low'],7)
        if len(hp)==0 or len(lp)==0: return {},None,None
        sh=recent['high'].iloc[hp[-1]]; sl_v=recent['low'].iloc[lp[-1]]
        if pd.isna(sh) or pd.isna(sl_v) or sh==sl_v: return {},None,None
        diff=sh-sl_v
        if hp[-1]>lp[-1]:
            d="UPTREND"; fibs={'23.6%':sh-diff*0.236,'38.2%':sh-diff*0.382,'50.0%':sh-diff*0.50,'61.8%':sh-diff*0.618,'78.6%':sh-diff*0.786}
        else:
            d="DOWNTREND"; fibs={'23.6%':sl_v+diff*0.236,'38.2%':sl_v+diff*0.382,'50.0%':sl_v+diff*0.50,'61.8%':sl_v+diff*0.618,'78.6%':sl_v+diff*0.786}
        return fibs,d,{'high':sh,'low':sl_v}
    except: return {},None,None

def check_fib_confluence(price, fibs, atr):
    try:
        if not fibs or pd.isna(price) or pd.isna(atr) or atr==0: return None,0
        for name,lvl in fibs.items():
            if pd.notna(lvl) and abs(price-lvl)<atr*0.4:
                return name,(15 if '61.8' in name else 10 if '50.0' in name or '38.2' in name else 5)
        return None,0
    except: return None,0

def detect_bb_cycle(df, profile, lookback=30):
    try:
        if len(df)<lookback: return "UNKNOWN",0,0
        recent=df.tail(lookback); bw=recent['BB_width']; avg=bw.mean(); cur=bw.iloc[-1]
        if avg==0: return "UNKNOWN",0,0
        ratio=cur/avg; threshold=profile.get('bb_squeeze_threshold',0.6)
        sc=sum(bw<avg*threshold)
        if ratio<threshold: return "SQUEEZE",ratio,sc
        elif ratio>1.5: return "EXPANSION",ratio,0
        return "NORMAL",ratio,0
    except: return "UNKNOWN",0,0

def count_consecutive(df, lookback=20):
    try:
        recent=df.tail(lookback); dirs=(recent['close']>recent['open']).astype(int)
        cd=dirs.iloc[-1]; streak=0
        for i in range(len(dirs)-1,-1,-1):
            if dirs.iloc[i]==cd: streak+=1
            else: break
        return streak, "BULLISH" if cd==1 else "BEARISH"
    except: return 0, "UNKNOWN"

def detect_roc_extreme(df, profile, periods=[5,10,20]):
    try:
        results={}; threshold=profile.get('roc_extreme_pct',1.0)
        for p in periods:
            if len(df)<p+1: continue
            roc=((df['close'].iloc[-1]-df['close'].iloc[-p-1])/df['close'].iloc[-p-1])*100
            if abs(roc)>threshold*2: status="EXTREME"
            elif abs(roc)>threshold: status="ELEVATED"
            else: status="NORMAL"
            results[f"ROC_{p}"]={'value':round(roc,3),'status':status,'direction':"UP" if roc>0 else "DOWN"}
        overall="NORMAL"
        for r in results.values():
            if r['status']=="EXTREME": overall="EXTREME"; break
            elif r['status']=="ELEVATED": overall="ELEVATED"
        return overall,results
    except: return "NORMAL",{}

# 🟡 EDGE #8: TRIGGER CANDLE CONFIRMATION
def trigger_candle_confirmed(df, direction):
    """Verifica se último candle confirma a entrada"""
    try:
        if len(df) < 3: return False, "NO_DATA"
        last = df.iloc[-1]; prev = df.iloc[-2]
        body = abs(last['close']-last['open']); rng = last['high']-last['low']
        body_pct = body/rng if rng > 0 else 0
        if direction == "BULLISH":
            bullish = last['close'] > last['open']
            above_prev = last['close'] > prev['close']
            strong = body_pct > 0.5
            if bullish and above_prev and strong: return True, "STRONG_TRIGGER"
            elif bullish and above_prev: return True, "WEAK_TRIGGER"
            return False, "NO_TRIGGER"
        else:
            bearish = last['close'] < last['open']
            below_prev = last['close'] < prev['close']
            strong = body_pct > 0.5
            if bearish and below_prev and strong: return True, "STRONG_TRIGGER"
            elif bearish and below_prev: return True, "WEAK_TRIGGER"
            return False, "NO_TRIGGER"
    except: return False, "ERROR"

# 🟢 PRECISION #3: SMART TP COM S/R AWARENESS
def smart_tp(entry, direction, risk, base_r1, base_r2, sr_levels):
    """Ajusta TP se S/R forte no caminho"""
    raw_tp1 = entry + base_r1 * risk if direction=="LONG" else entry - base_r1 * risk
    raw_tp2 = entry + base_r2 * risk if direction=="LONG" else entry - base_r2 * risk
    for sr in (sr_levels or []):
        if sr.get('strength',0) < 4: continue
        sp = sr['price']
        if direction == "LONG":
            if entry < sp < raw_tp1: raw_tp1 = sp - risk * 0.1; break
        else:
            if raw_tp1 < sp < entry: raw_tp1 = sp + risk * 0.1; break
    return round(raw_tp1, 5), round(raw_tp2, 5)

def detect_micro_pullback(df, direction, atr):
    try:
        if len(df)<5: return None,"MARKET"
        last=df.tail(3); curr=last.iloc[-1]; prev=last.iloc[-2]
        if direction=="BULLISH":
            if curr['close']<prev['close'] and curr['close']>curr['EMA_20'] and curr['low']>curr['EMA_50']:
                return (curr['low']+curr['EMA_20'])/2, "MICRO_PULLBACK"
            if abs(curr['low']-curr['EMA_20'])<atr*0.3 and curr['close']>curr['EMA_20']:
                return curr['EMA_20']+atr*0.1, "EMA_RETEST"
        elif direction=="BEARISH":
            if curr['close']>prev['close'] and curr['close']<curr['EMA_20'] and curr['high']<curr['EMA_50']:
                return (curr['high']+curr['EMA_20'])/2, "MICRO_PULLBACK"
            if abs(curr['high']-curr['EMA_20'])<atr*0.3 and curr['close']<curr['EMA_20']:
                return curr['EMA_20']-atr*0.1, "EMA_RETEST"
        return None,"MARKET"
    except: return None,"MARKET"

def detect_patterns(df):
    patterns,scores=[],[]
    for i in range(1,len(df)):
        c,p=df.iloc[i],df.iloc[i-1]; pl,sc=[],0
        body=abs(c['close']-c['open']); rng=c['high']-c['low']
        if rng>0:
            uw=c['high']-max(c['open'],c['close']); lw=min(c['open'],c['close'])-c['low']
            if lw>0 and body/rng<0.35 and uw<body:
                r=lw/max(body,0.0001)
                if r>3: pl.append("PIN_BULL_STRONG"); sc+=10
                elif r>2: pl.append("PIN_BULL_MOD"); sc+=5
            elif uw>0 and body/rng<0.35 and lw<body:
                r=uw/max(body,0.0001)
                if r>3: pl.append("PIN_BEAR_STRONG"); sc+=10
                elif r>2: pl.append("PIN_BEAR_MOD"); sc+=5
        cb=abs(c['close']-c['open']); pb=abs(p['close']-p['open'])
        ct,cb2=max(c['open'],c['close']),min(c['open'],c['close'])
        pt,pb3=max(p['open'],p['close']),min(p['open'],p['close'])
        if c['close']>c['open'] and p['close']<p['open'] and cb2<pb3 and ct>pt:
            r=cb/max(pb,0.0001)
            if r>2: pl.append("ENGULF_BULL_STRONG"); sc+=10
            else: pl.append("ENGULF_BULL"); sc+=5
        elif c['close']<c['open'] and p['close']>p['open'] and cb2<pb3 and ct>pt:
            r=cb/max(pb,0.0001)
            if r>2: pl.append("ENGULF_BEAR_STRONG"); sc+=10
            else: pl.append("ENGULF_BEAR"); sc+=5
        if c['high']<=p['high'] and c['low']>=p['low']: pl.append("INSIDE_BAR"); sc+=5
        if rng>0 and body/rng<0.1: pl.append("DOJI"); sc+=3
        patterns.append(pl); scores.append(sc)
    df['patterns']=[[]]+patterns; df['pattern_score']=[0]+scores; return df

def detect_swing_points(df, window=5):
    df['swing_high']=False; df['swing_low']=False
    for i in range(window,len(df)):
        lb=df.iloc[max(0,i-window):i+1]
        if df['high'].iloc[i]==lb['high'].max(): df.iloc[i,df.columns.get_loc('swing_high')]=True
        if df['low'].iloc[i]==lb['low'].min(): df.iloc[i,df.columns.get_loc('swing_low')]=True
    return df

def classify_market_structure(df):
    sh=df[df['swing_high']]['high'].tail(4); sl=df[df['swing_low']]['low'].tail(4)
    if len(sh)<2 or len(sl)<2: return "INSUFFICIENT"
    hh=sh.iloc[-1]>sh.iloc[-2]; hl=sl.iloc[-1]>sl.iloc[-2]
    ll=sl.iloc[-1]<sl.iloc[-2]; lh=sh.iloc[-1]<sh.iloc[-2]
    if hh and hl: return "UPTREND_STRONG"
    elif ll and lh: return "DOWNTREND_STRONG"
    elif hh or hl: return "UPTREND_WEAK"
    elif ll or lh: return "DOWNTREND_WEAK"
    return "RANGE_BOUND"

def classify_regime(df, lookback=50):
    try:
        if len(df)<lookback: return "UNKNOWN",0
        recent=df.tail(lookback); c=recent.iloc[-1]; adx=c['ADX']
        slope=(recent['EMA_50'].iloc[-1]-recent['EMA_50'].iloc[-10])/(c['ATR']*10) if c['ATR']>0 else 0
        bb_ratio=c['BB_width']/recent['BB_width'].mean() if recent['BB_width'].mean()>0 else 1
        sc=0
        if adx>30: sc+=3
        elif adx>20: sc+=2
        elif adx>15: sc+=1
        if abs(slope)>0.3: sc+=2
        elif abs(slope)>0.15: sc+=1
        if bb_ratio>1.3: sc+=1
        elif bb_ratio<0.7: sc-=1
        if sc>=4: return "TRENDING_STRONG",sc
        elif sc>=2: return "TRENDING_WEAK",sc
        elif sc<=0: return "RANGING",sc
        return "TRANSITIONAL",sc
    except: return "UNKNOWN",0

def analyze_tick_volume(df, lookback=20):
    try:
        if len(df)<lookback: return "NORMAL",1.0
        recent=df.tail(lookback); ranges=recent['high']-recent['low']; bodies=abs(recent['close']-recent['open'])
        rr=ranges.iloc[-1]/ranges.mean() if ranges.mean()>0 else 1
        br=bodies.iloc[-1]/bodies.mean() if bodies.mean()>0 else 1
        proxy=(rr+br)/2
        if proxy>2.0: return "VERY_HIGH",proxy
        elif proxy>1.5: return "HIGH",proxy
        elif proxy>0.7: return "NORMAL",proxy
        return "LOW",proxy
    except: return "NORMAL",1.0

def confirm_breakout_volume(df):
    try:
        if len(df)<20: return False,0
        ranges=df['high']-df['low']; ratio=ranges.iloc[-1]/ranges.iloc[-20:-1].mean() if ranges.iloc[-20:-1].mean()>0 else 1
        return ratio>1.3, ratio
    except: return False,0

def indicators(df):
    df['EMA_20']=df['close'].ewm(span=20,adjust=False).mean()
    df['EMA_50']=df['close'].ewm(span=50,adjust=False).mean()
    df['EMA_200']=df['close'].ewm(span=200,adjust=False).mean()
    df['RSI']=calculate_rsi_wilder(df['close'],14)
    hl=df['high']-df['low']; hc=(df['high']-df['close'].shift()).abs(); lc=(df['low']-df['close'].shift()).abs()
    df['tr']=pd.concat([hl,hc,lc],axis=1).max(axis=1); df['ATR']=df['tr'].ewm(span=14,adjust=False).mean()
    df=calculate_adx(df); df=calculate_macd(df)
    df['BB_middle']=df['close'].rolling(20).mean(); df['BB_std']=df['close'].rolling(20).std()
    df['BB_upper']=df['BB_middle']+df['BB_std']*2; df['BB_lower']=df['BB_middle']-df['BB_std']*2
    df['BB_width']=((df['BB_upper']-df['BB_lower'])/df['BB_middle'].replace(0,np.nan))*100
    df['ZSCORE']=calculate_zscore(df['close'],50)
    df=detect_patterns(df); df=detect_swing_points(df); df.dropna(inplace=True); return df

def detect_alignment(h4r, h1r, m15r, d):
    sc=0
    if d=="BULLISH":
        if h4r['close']>h4r['EMA_20']>h4r['EMA_50']>h4r['EMA_200']: sc+=10
        if h1r['close']>h1r['EMA_20']>h1r['EMA_50']>h1r['EMA_200']: sc+=10
        if m15r['close']>m15r['EMA_20']>m15r['EMA_50']>m15r['EMA_200']: sc+=10
    else:
        if h4r['close']<h4r['EMA_20']<h4r['EMA_50']<h4r['EMA_200']: sc+=10
        if h1r['close']<h1r['EMA_20']<h1r['EMA_50']<h1r['EMA_200']: sc+=10
        if m15r['close']<m15r['EMA_20']<m15r['EMA_50']<m15r['EMA_200']: sc+=10
    if sc==30: return "PERFECT",25
    elif sc>=20: return "STRONG",15
    elif sc>=10: return "WEAK",5
    return "NONE",0

def check_momentum(h4,h1,m15,d):
    sc=0
    if d=="BULLISH":
        if h4['MACD'].iloc[-1]>0:sc+=1
        if h1['MACD'].iloc[-1]>0:sc+=1
        if m15['MACD'].iloc[-1]>0:sc+=1
    else:
        if h4['MACD'].iloc[-1]<0:sc+=1
        if h1['MACD'].iloc[-1]<0:sc+=1
        if m15['MACD'].iloc[-1]<0:sc+=1
    return sc

def detect_swing_level(df, direction, atr_mult=1.5):
    if direction=="BUY":
        sw=df[df['swing_low']]['low']
        return (sw.iloc[-1]-df['ATR'].iloc[-1]*atr_mult) if not sw.empty else df['low'].tail(20).min()-df['ATR'].iloc[-1]*atr_mult
    else:
        sw=df[df['swing_high']]['high']
        return (sw.iloc[-1]+df['ATR'].iloc[-1]*atr_mult) if not sw.empty else df['high'].tail(20).max()+df['ATR'].iloc[-1]*atr_mult

# ==============================================================================
# 🔴 BUG FIX #4: WALK-FORWARD QUE TESTA CADA TIPO DE SETUP
# ==============================================================================

def run_walk_forward_v20(df, bias, profile, gen_analysis, vr_test, acf_test, n_folds=4):
    """V20: Backtest testa setups Generator + Clássicos + Mean Reversion"""
    spread = profile.get('spread', 0.05)
    sl_mult = profile.get('sl_atr_mult', 2.5)
    fold_size = len(df) // (n_folds + 1)
    all_trades = []

    for fold in range(n_folds):
        ts = fold_size * (fold + 1)
        te = fold_size * (fold + 2) if fold < n_folds - 1 else len(df)
        if ts >= len(df) - 80:
            break
        si = max(200, ts)

        for i in range(si, min(te, len(df) - 60)):
            row = df.iloc[i]
            if pd.isna(row['ADX']) or pd.isna(row['ATR']) or row['ATR'] == 0:
                continue
            sig = None
            atr = row['ATR']
            entry = sl = risk = 0
            setup = "NONE"

            # SETUP 1: TREND (clássico melhorado)
            if row['ADX'] > profile.get('adx_strong', 25):
                if bias == "BULLISH" and row['close'] > row['EMA_200'] and row['RSI'] < 60:
                    sig = "BUY"; setup = "SWING"
                elif bias == "BEARISH" and row['close'] < row['EMA_200'] and row['RSI'] > 40:
                    sig = "SELL"; setup = "SWING"

            # SETUP 2: MEAN REVERSION (Z-Score extreme)
            if not sig and 'ZSCORE' in df.columns:
                z = row['ZSCORE']
                if pd.notna(z) and abs(z) > profile.get('zscore_extreme', 2.0) * 0.7:
                    if z < -1.5:
                        sig = "BUY"; setup = "MEAN_REVERSION"
                    elif z > 1.5:
                        sig = "SELL"; setup = "MEAN_REVERSION"

            # SETUP 3: VOL COMPRESS (se edge detectado por VR)
            if not sig and vr_test.get('has_edge') and vr_test.get('dominant_type') == 'MEAN_REVERT':
                z = row.get('ZSCORE', 0)
                if pd.notna(z) and z < -1.0:
                    sig = "BUY"; setup = "VOL_COMPRESS"
                elif pd.notna(z) and z > 1.0:
                    sig = "SELL"; setup = "VOL_COMPRESS"

            # SETUP 4: ACF MOMENTUM (se autocorrelação significativa)
            if not sig and acf_test.get('has_pattern') and acf_test.get('dominant_type') == 'MOMENTUM':
                if i >= 2:
                    prev_ret = df['close'].iloc[i] - df['close'].iloc[i-1]
                    if prev_ret > atr * 0.3:
                        sig = "BUY"; setup = "ACF_MOMENTUM"
                    elif prev_ret < -atr * 0.3:
                        sig = "SELL"; setup = "ACF_MOMENTUM"

            if not sig:
                continue

            # Executar trade
            entry = row['close'] + (spread if sig == "BUY" else -spread)
            sl_base = detect_swing_level(df.iloc[:i+1], sig, sl_mult)
            if sig == "BUY":
                sl = max(entry - sl_mult * atr, sl_base)
            else:
                sl = min(entry + sl_mult * atr, sl_base)
            risk = abs(entry - sl)
            if risk == 0: risk = atr

            tp1_r = profile.get('tp1_r', 3.0) if setup != "MEAN_REVERSION" else 2.0
            tp2_r = profile.get('tp2_r', 5.0) if setup != "MEAN_REVERSION" else 3.0
            tp1 = entry + tp1_r * risk if sig == "BUY" else entry - tp1_r * risk
            tp2 = entry + tp2_r * risk if sig == "BUY" else entry - tp2_r * risk

            # 🟢 PRECISION #2: TRAILING ADAPTATIVO
            trail_mult = 2.0  # default
            if setup == "SWING": trail_mult = 2.5
            elif setup == "MEAN_REVERSION": trail_mult = 1.2
            elif setup == "VOL_COMPRESS": trail_mult = 1.5

            p1_open, p2_open = True, True
            r1, r2 = 0, 0
            csl = sl
            for f in range(i + 1, min(i + 80, len(df))):
                nx = df.iloc[f]
                if sig == "BUY":
                    if nx['low'] <= csl:
                        if p1_open: r1 = (csl - entry) / risk
                        if p2_open: r2 = (csl - entry) / risk
                        break
                    if p1_open and nx['high'] >= tp1:
                        r1 = tp1_r - spread/risk; p1_open = False; csl = entry + spread
                    if not p1_open and p2_open:
                        csl = max(csl, nx['high'] - trail_mult * atr)
                        if nx['high'] >= tp2:
                            r2 = tp2_r - spread/risk; p2_open = False; break
                else:
                    if nx['high'] >= csl:
                        if p1_open: r1 = (entry - csl) / risk
                        if p2_open: r2 = (entry - csl) / risk
                        break
                    if p1_open and nx['low'] <= tp1:
                        r1 = tp1_r - spread/risk; p1_open = False; csl = entry - spread
                    if not p1_open and p2_open:
                        csl = min(csl, nx['low'] + trail_mult * atr)
                        if nx['low'] <= tp2:
                            r2 = tp2_r - spread/risk; p2_open = False; break

            result = r1 * 0.5 + r2 * 0.5
            if not (p1_open and p2_open):
                all_trades.append({'fold': fold, 'result': result, 'setup': setup, 'win': result > 0})

    if not all_trades:
        return {"WR":0,"NET":0,"DD":0,"PF":0,"SHARPE":0,"SORTINO":0,"TOTAL_TRADES":0,
                "WF_STABLE":False,"FOLD_WRS":[],"RESULTS":[]}

    results = [t['result'] for t in all_trades]
    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]
    wr = len(wins)/len(results)*100
    net = sum(results)
    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 0
    pf = gp/gl if gl > 0 else (gp if gp > 0 else 0)
    cum = np.cumsum(results)
    peak = np.maximum.accumulate(cum)
    dd = float((peak - cum).max()) if len(cum) > 0 else 0
    rs = pd.Series(results)
    sharpe = float(rs.mean()/rs.std()*np.sqrt(252)) if len(rs) >= 2 and rs.std() > 0 else 0
    ds = rs[rs<0]
    sortino = float(rs.mean()/ds.std()*np.sqrt(252)) if len(ds) >= 2 and ds.std() > 0 else 0

    # Per-fold WRs
    fold_wrs = []
    for fold_id in range(n_folds):
        ft = [t for t in all_trades if t['fold'] == fold_id]
        if ft:
            fold_wrs.append(round(sum(1 for t in ft if t['win'])/len(ft)*100, 1))

    # Per-setup stats
    setup_stats = {}
    for setup_name in set(t['setup'] for t in all_trades):
        st = [t for t in all_trades if t['setup'] == setup_name]
        sw = [t for t in st if t['win']]
        setup_stats[setup_name] = {"trades": len(st), "wr": round(len(sw)/len(st)*100,1) if st else 0}

    return {"WR":round(wr,1),"NET":round(net,1),"DD":round(dd,1),"PF":round(pf,2),
            "SHARPE":round(sharpe,2),"SORTINO":round(sortino,2),"TOTAL_TRADES":len(results),
            "WF_STABLE":len(fold_wrs)>=2 and all(w>30 for w in fold_wrs),
            "FOLD_WRS":fold_wrs,"SETUP_STATS":setup_stats,"RESULTS":results}

# ==============================================================================
# 🔴 BUG FIX #6: MONTE CARLO BOOTSTRAP REAL
# ==============================================================================

def monte_carlo_bootstrap(results, n_sim=1000, n_trades=50):
    """Bootstrap dos resultados REAIS do backtest"""
    try:
        if len(results) < 5:
            return {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":0}
        arr = np.array(results)
        sims = np.array([np.sum(np.random.choice(arr, size=min(n_trades, len(arr)), replace=True))
                         for _ in range(n_sim)])
        return {"median":round(float(np.median(sims)),1),
                "p5":round(float(np.percentile(sims,5)),1),
                "p95":round(float(np.percentile(sims,95)),1),
                "p25":round(float(np.percentile(sims,25)),1),
                "p75":round(float(np.percentile(sims,75)),1),
                "positive_pct":round(float(np.mean(sims>0)*100),1)}
    except:
        return {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":0}

# ==============================================================================
# SCORING V20 — 16 fatores (14 + VR + ACF)
# ==============================================================================

@dataclass
class SetupScore:
    trend_strength:float; momentum_align:float; patterns:float
    value_zone:float; historical:float; base_total:float
    divergence_bonus:float; fib_bonus:float; sr_bonus:float
    alignment_bonus:float; storm_bonus:float; regime_bonus:float
    volume_bonus:float; hurst_bonus:float; zscore_bonus:float
    consecutive_bonus:float; generator_bonus:float; distribution_bonus:float
    vr_bonus:float; acf_bonus:float
    bonus_total:float; total:float; grade:str

def calculate_score(adx, momentum_score, pattern_score, dist_ema50, atr,
                    win_rate, profit_factor, profile, **bonuses):
    ts=25 if adx>profile.get('adx_strong',25) else(15 if adx>profile.get('adx_trend_min',15) else 0)
    mp=(momentum_score/3)*20
    dr=dist_ema50/atr if atr>0 else 999
    vs=15 if dr<0.5 else(10 if dr<1.0 else(5 if dr<1.5 else 0))
    hs=min((win_rate*0.15)+(profit_factor*5),25)
    base=ts+mp+pattern_score+vs+hs
    keys=['divergence_bonus','fib_bonus','sr_bonus','alignment_bonus','storm_bonus',
          'regime_bonus','volume_bonus','hurst_bonus','zscore_bonus','consecutive_bonus',
          'generator_bonus','distribution_bonus','vr_bonus','acf_bonus']
    bonus=min(sum(bonuses.get(k,0) for k in keys),70)  # V20: max 70
    total=base+bonus
    if total>=160: g="S"
    elif total>=135: g="A++"
    elif total>=105: g="A+"
    elif total>=80: g="A"
    elif total>=55: g="B"
    elif total>=35: g="C"
    else: g="D"
    return SetupScore(ts,mp,pattern_score,vs,hs,base,
        *[bonuses.get(k,0) for k in keys], bonus,total,g)

# ==============================================================================
# STORM DETECTOR V20
# ==============================================================================

def calculate_storm_bonus(sd):
    met, lst = 0, []
    checks = [
        (sd.get('adx',0)>30,"ADX>30"),(sd.get('momentum_score',0)==3,"Mom 3/3"),
        (sd.get('pattern_score',0)>=10,"Padrões"),(sd.get('divergence') is not None,"Div"),
        (sd.get('fib'),"Fib"),(sd.get('sr_touch'),"S/R"),(sd.get('alignment'),"Align"),
        (sd.get('bb_squeeze'),"BB Squeeze"),(sd.get('trending'),"Trending"),
        (sd.get('volume'),"Volume"),(sd.get('hurst_trending'),"Hurst"),
        (sd.get('zscore'),"Z-Score"),(sd.get('gen_signal'),"Generator"),
        (sd.get('dist'),"Distrib"),(sd.get('vr_edge'),"VR Edge"),(sd.get('acf_edge'),"ACF Edge"),
    ]
    for c,l in checks:
        if c: met+=1; lst.append(l)
    if met>=11: return "PERFECT_STORM",25,lst
    elif met>=8: return "STRONG_CONFLUENCE",20,lst
    elif met>=6: return "GOOD_CONFLUENCE",15,lst
    elif met>=4: return "MODERATE",10,lst
    return None,0,lst

# ==============================================================================
# CHART V20
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp1=None, tp2=None, sr_levels=None, fib_levels=None):
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(14,9),height_ratios=[3,1],facecolor='#0a0a0a')
    ax1.set_facecolor('#0a0a0a'); ax2.set_facecolor('#0a0a0a')
    for i in range(len(df)):
        c='#10b981' if df['close'].iloc[i]>=df['open'].iloc[i] else '#ef4444'
        ax1.plot([df.index[i]]*2,[df['low'].iloc[i],df['high'].iloc[i]],color=c,lw=0.8)
        ax1.plot([df.index[i]]*2,[df['open'].iloc[i],df['close'].iloc[i]],color=c,lw=3.5)
    ax1.plot(df.index,df['EMA_20'],label='EMA20',color='cyan',ls='--',alpha=0.6,lw=1)
    ax1.plot(df.index,df['EMA_50'],label='EMA50',color='orange',ls='--',alpha=0.6,lw=1)
    ax1.plot(df.index,df['EMA_200'],label='EMA200',color='purple',ls='-',alpha=0.4,lw=1.5)
    ax1.fill_between(df.index,df['BB_upper'],df['BB_lower'],alpha=0.05,color='white')
    if sr_levels:
        for sr in sr_levels[:4]:
            c='#ef4444' if sr['type']=='RESISTANCE' else '#10b981'
            ax1.axhspan(sr['zone_low'],sr['zone_high'],alpha=0.1,color=c)
    if fib_levels:
        for n,p in fib_levels.items():
            if pd.notna(p): ax1.axhline(y=p,color='#fbbf24',ls='-.',alpha=0.25,lw=0.7)
    if entry: ax1.axhline(y=entry,color='cyan',ls='-',label='Entry',lw=2)
    if sl: ax1.axhline(y=sl,color='#ef4444',ls='-',label='SL',lw=2)
    if tp1: ax1.axhline(y=tp1,color='#10b981',ls='--',label='TP1',lw=1.5)
    if tp2: ax1.axhline(y=tp2,color='#059669',ls='-',label='TP2',lw=2)
    ax1.set_title(title,fontsize=14,fontweight='bold',color='#fbbf24')
    ax1.legend(loc='upper left',fontsize=7,facecolor='#111',edgecolor='#333',labelcolor='white')
    ax1.grid(True,alpha=0.1,color='#333'); ax1.tick_params(colors='#666')
    colors=['#10b981' if x>0 else '#ef4444' for x in df['MACD_hist']]
    ax2.bar(df.index,df['MACD_hist'],color=colors,alpha=0.5,width=0.8)
    ax2.plot(df.index,df['MACD'],color='#3b82f6',lw=1); ax2.plot(df.index,df['MACD_signal'],color='#ef4444',lw=1)
    ax2.axhline(y=0,color='#333',lw=0.5); ax2.set_title('MACD',fontsize=10,color='#fbbf24')
    ax2.grid(True,alpha=0.1,color='#333'); ax2.tick_params(colors='#666')
    plt.xticks(rotation=45); plt.tight_layout()
    buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=120,facecolor='#0a0a0a',bbox_inches='tight')
    plt.close(fig); buf.seek(0); return Image.open(buf)

def convert_np(obj):
    if isinstance(obj,dict): return {k:convert_np(v) for k,v in obj.items()}
    elif isinstance(obj,list): return [convert_np(i) for i in obj]
    elif isinstance(obj,np.integer): return int(obj)
    elif isinstance(obj,np.floating): return float(obj)
    elif isinstance(obj,np.ndarray): return obj.tolist()
    elif isinstance(obj,np.bool_): return bool(obj)
    elif isinstance(obj,float) and pd.isna(obj): return None
    return obj

# ==============================================================================
# SYSTEM PROMPT V20
# ==============================================================================

SYSTEM_PROMPT = """
FUNÇÃO: ANALISTA V20.0 — STATISTICAL EDGE ENGINE [Gemini 3 Pro]
Missão: Explorar edges estatísticos reais nos sintéticos Deriv

**RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO**

**V20.0 — 20 CORREÇÕES DA ANÁLISE CIRÚRGICA:**
- Sigma calibrado do histórico real (não inventado)
- VOL_COMPRESS com direção CONTRA o movimento
- Crash/Boom drift por regressão linear + spike decay model
- Backtest testa CADA tipo de setup separadamente
- Monte Carlo bootstrap dos resultados REAIS
- Variance Ratio Test (detecta se há edge)
- Autocorrelação de retornos (padrão explorável)
- Vol Clustering (GARCH)
- Preço teórico vs real (GBM z-score)
- Multi-window vol analysis (3 janelas)
- Smart TP com S/R awareness
- Trigger candle confirmation
- Hurst com validação R²
- Kelly Criterion contínuo

**FORMATO:**

## ⚡ VEREDICTO V20.0: [ {DECISION} ]
**Grade:** {GRADE} | **Score:** {SCORE}/170
**Tipo:** {STYLE} | **Edge Real:** {VR_HAS_EDGE}

### 🧮 MODELO DO GERADOR
- Sigma calibrado: {X}% | Vol Ratio (3 janelas): S={short} M={med} L={long}
- Consensus: {SIGNAL} → Direção: {compress_direction}
- Preço teórico z: {z_price} ({deviation_signal})

### 📊 EDGE ESTATÍSTICO
- Variance Ratio: {VR edge type} ({N} períodos significativos)
- Autocorrelação: lag-1={acf_1} ({type})
- Vol Clustering: {regime}
- Distribuição: Skew={S} Kurt={K} Tails={T}

### 🎯 PLANO DE TRADE
{Entradas + Pirâmide + Smart TP}

### ⚠️ CONFLUÊNCIAS + RISCOS

*V20 Insight:* {Baseado nos EDGES REAIS detectados pelo Variance Ratio
e Autocorrelação, NÃO em indicadores clássicos. Se VR mostra random walk,
dizer claramente que não há edge estatístico operável.}
"""

# ==============================================================================
# SNIPER CORE V20.0 — STATISTICAL EDGE ENGINE
# ==============================================================================

def sniper_core_v20(name, h1_raw, h4_raw, m15_raw, m5_raw, capital=10000, risk_pct=1.0):
    profile = get_profile(name)
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = indicators(prep_df(m15_raw))
    m5 = indicators(prep_df(m5_raw)) if m5_raw else None
    c1, c4, cm = h1.iloc[-1], h4.iloc[-1], m15.iloc[-1]
    c5 = m5.iloc[-1] if m5 is not None and len(m5) > 0 else None

    bias = "BULLISH" if c4['close'] > c4['EMA_200'] else "BEARISH"
    adx = c4['ADX']
    structure = classify_market_structure(h1)
    regime, regime_sc = classify_regime(h1)
    momentum = check_momentum(h4, h1, m15, bias)

    # 🔴 FIX #1: Auto-detect periods/year
    ppy = detect_periods_per_year(h1)

    # 🟠 FIX #1: CALIBRAR SIGMA REAL
    sigma_calibrated = calibrate_sigma(h1, ppy)

    # ═══ GENERATOR MODEL V20 ═══
    gen_type = profile.get('gen_type', 'GBM')
    if gen_type == "GBM":
        gen = GeneratorModelV20.analyze_gbm(h1, profile, sigma_calibrated, ppy)
    elif gen_type in ["BOOM", "CRASH"]:
        gen = GeneratorModelV20.analyze_crash_boom(h1, profile, ppy)
    elif gen_type == "STEP":
        gen = GeneratorModelV20.analyze_step(h1, profile, ppy)
    else:
        gen = {"signal": "NEUTRAL", "confidence": 0}

    # ═══ EDGE TESTS V20 ═══
    vr = variance_ratio_test(h1['close'])
    acf = autocorrelation_analysis(h1['close'])
    vol_cluster = volatility_clustering_test(h1['close'])
    dist = DistributionAnalyzer.analyze(h1)

    # ═══ CLASSIC STATS ═══
    hurst_val, hurst_regime, hurst_r2 = calculate_hurst_exponent(h1['close'])
    z_current = float(cm['ZSCORE']) if pd.notna(cm.get('ZSCORE')) else 0
    bb_cycle, bb_ratio, bb_squeeze_count = detect_bb_cycle(h1, profile)
    consec_count, consec_dir = count_consecutive(m15)
    roc_status, roc_details = detect_roc_extreme(m15, profile)

    # Divergências
    rsi_div, rsi_db, rsi_dd = detect_divergence(m15, 'RSI', 4)
    macd_div, macd_db, macd_dd = detect_divergence(m15, 'MACD', 4)
    divergence = rsi_div or macd_div
    div_bonus = max(rsi_db, macd_db); div_detail = rsi_dd or macd_dd

    # S/R, Fib
    sr_levels = detect_sr_clustered(h1)
    sr_bonus, sr_touch, closest_sr = 0, False, None
    if sr_levels:
        closest_sr = min(sr_levels, key=lambda x: abs(x['price']-c1['close']))
        if abs(closest_sr['price']-c1['close']) < c1['ATR']*0.5:
            sr_bonus = min(closest_sr['strength']*3, 15); sr_touch = True
    fibs, fib_dir, _ = calculate_fibonacci(h1)
    fib_level, fib_bonus = check_fib_confluence(c1['close'], fibs, c1['ATR'])

    align_type, align_bonus = detect_alignment(c4, c1, cm, bias)
    vol_st, vol_proxy = analyze_tick_volume(m15)
    vol_confirmed = vol_proxy > 1.3; vol_bonus = 5 if vol_confirmed else 0
    regime_bonus = 5 if "TRENDING" in regime else 0
    pat_score = min(cm.get('pattern_score', 0), 15)
    bb_compression = bb_cycle == "SQUEEZE"

    # BONUSES V20
    gen_bonus = 0; gen_signal = gen.get('signal', 'NEUTRAL')
    if gen_type == "GBM":
        if gen.get('consensus') in ["VOL_COMPRESS","VOL_EXPAND"] and gen.get('consensus_confidence',0) > 30:
            gen_bonus = min(int(gen['consensus_confidence'] / 8), 12)
        if abs(gen.get('z_price',0)) > 2:
            gen_bonus += 5
    elif gen_type in ["BOOM","CRASH"]:
        if gen.get('spike_phase') in ["DRIFT_STRONG","DRIFT_NORMAL"]:
            gen_bonus = min(int(gen.get('decay_strength',0)*8), 12)
    elif gen_type == "STEP":
        if gen.get('signal') in ["EXTREME_DEVIATION","HIGH_DEVIATION"]:
            gen_bonus = min(int(gen.get('confidence',0)/8), 12)

    hurst_bonus = 0; hurst_trending = False
    if hurst_r2 >= 0.7:
        if hurst_val > profile.get('hurst_trend_min',0.53): hurst_bonus=10; hurst_trending=True
        elif hurst_val < 0.45: hurst_bonus=5

    zscore_bonus = 0; zscore_favorable = False
    if bias=="BULLISH" and z_current < -profile.get('zscore_extreme',2)*0.6:
        zscore_bonus=10; zscore_favorable=True
    elif bias=="BEARISH" and z_current > profile.get('zscore_extreme',2)*0.6:
        zscore_bonus=10; zscore_favorable=True

    consec_reversal = consec_count >= profile.get('consecutive_reversal',6)
    consecutive_bonus = 0
    if consec_reversal and ((bias=="BULLISH" and consec_dir=="BEARISH") or (bias=="BEARISH" and consec_dir=="BULLISH")):
        consecutive_bonus = 10

    dist_bonus = 0; dist_favorable = False
    if dist['tail_risk'] in ["FAT_TAILS","HEAVY_TAILS"]: dist_bonus += 3
    if dist['percentile'] < 10 and bias=="BULLISH": dist_bonus+=7; dist_favorable=True
    elif dist['percentile'] > 90 and bias=="BEARISH": dist_bonus+=7; dist_favorable=True

    vr_bonus = 0
    if vr.get('has_edge'): vr_bonus = min(vr.get('n_significant',0)*4, 12)
    acf_bonus = 0
    if acf.get('has_pattern'): acf_bonus = min(len(acf.get('significant_lags',[]))*3, 10)

    # ═══ 🔴 FIX #5: BACKTEST 1× (não 2×) + V20 multi-setup ═══
    sim = run_walk_forward_v20(h1, bias, profile, gen, vr, acf, n_folds=4)

    # ADAPTIVE (usa resultado do único backtest)
    adapted_profile = AdaptiveLearnerV20.adjust_profile(profile, sim, dist)

    # 🔴 FIX #6: Monte Carlo REAL
    mc = monte_carlo_bootstrap(sim.get('RESULTS', []))

    # ═══ SETUP DETECTION V20 — 🟡 EDGE #7: REGIME-SPECIFIC ═══
    sig = "MONITORING"; entry = float(c1['close']); sl_val = float(c1['close'])
    entry_type = "Wait"; sl_reason = "Pivot"; trade_style = None; setup_type = None
    vc = profile['vol_class']

    # M5 trigger check
    trigger_ok, trigger_type = (True, "N/A")
    if m5 is not None and len(m5) > 0:
        trigger_ok, trigger_type = trigger_candle_confirmed(m5, bias)

    mp_price, mp_type = detect_micro_pullback(m15, bias, c1['ATR'])

    def try_setup(direction):
        nonlocal sig, sl_val, entry_type, trade_style, setup_type, entry
        is_long = direction == "BULLISH"
        div_block = divergence and (("BEARISH" in str(divergence) and is_long and "HIDDEN" not in str(divergence)) or
                                     ("BULLISH" in str(divergence) and not is_long and "HIDDEN" not in str(divergence)))
        if div_block:
            sig = f"BLOCKED (DIV: {div_detail})"; return

        # REGIME-SPECIFIC STRATEGY
        # TRENDING → Swing/Breakout
        # RANGING → Mean Reversion
        # VOL_COMPRESS → Contra o movimento
        # TRANSITIONAL → Esperar ou size reduzido

        # 1. GENERATOR SETUPS (PRIORIDADE)
        if gen_type == "GBM" and gen.get('consensus') == "VOL_COMPRESS" and gen.get('consensus_confidence',0) > 40:
            # 🔴 FIX #2: Direção CONTRA o movimento
            cd = gen.get('compress_direction','NEUTRAL')
            if (cd == "BULLISH" and is_long) or (cd == "BEARISH" and not is_long):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (VOL COMPRESS)"
                sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                entry_type = f"GBM Compress → {cd} (ratio={gen.get('vol_ratio',1):.2f})"
                trade_style = "REVERSAL"; setup_type = "GEN_VOL_COMPRESS"
                return

        if gen_type == "GBM" and abs(gen.get('z_price',0)) > 2:
            zp = gen['z_price']
            if (zp < -2 and is_long) or (zp > 2 and not is_long):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (PRICE DEVIATION)"
                sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                entry_type = f"Preço {zp:.1f}σ do teórico"
                trade_style = "REVERSAL"; setup_type = "GEN_PRICE_DEV"
                return

        # 🔴 FIX #3: Crash/Boom — drift direction real
        if gen_type in ["BOOM","CRASH"]:
            phase = gen.get('spike_phase','')
            drift_dir = gen.get('drift_direction','')
            if phase in ["DRIFT_STRONG","DRIFT_NORMAL"]:
                if (drift_dir=="UP" and is_long) or (drift_dir=="DOWN" and not is_long):
                    d = "LONG" if is_long else "SHORT"
                    sig = f"{d} (SPIKE DRIFT {phase})"
                    sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                    entry_type = f"Drift {drift_dir} ({gen.get('last_spike_bars',0)} bars)"
                    trade_style = "DAY"; setup_type = "GEN_SPIKE_DRIFT"
                    return

        if gen_type == "STEP":
            dev = gen.get('deviation_sigma',0)
            if (dev < -1.5 and is_long) or (dev > 1.5 and not is_long):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (STEP REVERT)"
                sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                entry_type = f"Step {dev:.1f}σ deviation"
                trade_style = "REVERSAL"; setup_type = "GEN_STEP_REVERT"
                return

        # 2. REGIME-SPECIFIC CLASSIC SETUPS
        if "TRENDING" in regime and adx > adapted_profile.get('adx_strong',25):
            if (is_long and abs(c1['close']-c1['EMA_50'])<c1['ATR']*1.5) or \
               (not is_long and abs(c1['close']-c1['EMA_50'])<c1['ATR']*1.5):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (SWING)"
                sl_val = detect_swing_level(h1, "BUY" if is_long else "SELL", adapted_profile['sl_atr_mult'])
                entry_type = f"Swing — {mp_type}"
                trade_style = "SWING"; setup_type = "SWING"
                if mp_price and mp_type != "MARKET": entry = mp_price
                return

        if "RANGING" in regime or hurst_val < 0.48:
            if abs(z_current) > profile.get('zscore_extreme',2)*0.6:
                if (z_current < 0 and is_long) or (z_current > 0 and not is_long):
                    d = "LONG" if is_long else "SHORT"
                    sig = f"{d} (MEAN REVERSION)"
                    sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                    entry_type = f"MR Z={z_current:.1f}"
                    trade_style = "REVERSAL"; setup_type = "MEAN_REVERSION"
                    return

        # 3. DAY
        if adx > adapted_profile.get('adx_trend_min',15):
            d = "LONG" if is_long else "SHORT"
            sig = f"{d} (DAY)"
            sl_val = detect_swing_level(h1, "BUY" if is_long else "SELL", adapted_profile['sl_atr_mult']*0.8)
            entry_type = f"Day — {mp_type}"
            trade_style = "DAY"; setup_type = "DAY"
            if mp_price and mp_type != "MARKET": entry = mp_price
            return

        # 4. BREAKOUT
        if sr_touch and closest_sr:
            bk_ok, bk_r = confirm_breakout_volume(m15)
            if bk_ok:
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (BREAKOUT)"
                sl_val = closest_sr['price'] - c1['ATR'] if is_long else closest_sr['price'] + c1['ATR']
                entry_type = f"Breakout S/R (×{bk_r:.1f})"
                trade_style = "BREAKOUT"; setup_type = "BREAKOUT"
                return

    # For Crash/Boom: try BOTH directions (drift can be opposite to bias)
    if gen_type in ["BOOM","CRASH"]:
        drift_dir = gen.get('drift_direction','')
        if drift_dir == "UP": try_setup("BULLISH")
        elif drift_dir == "DOWN": try_setup("BEARISH")
        if sig == "MONITORING": try_setup(bias)
    else:
        try_setup(bias)

    # Spread
    if "LONG" in sig: entry += profile['spread']
    elif "SHORT" in sig: entry -= profile['spread']

    # Clamp SL
    if "LONG" in sig and (entry - sl_val) > adapted_profile['sl_atr_mult'] * c1['ATR']:
        sl_val = entry - adapted_profile['sl_atr_mult'] * c1['ATR']
    elif "SHORT" in sig and (sl_val - entry) > adapted_profile['sl_atr_mult'] * c1['ATR']:
        sl_val = entry + adapted_profile['sl_atr_mult'] * c1['ATR']

    # Storm
    storm_data = {'adx':adx,'momentum_score':momentum,'pattern_score':pat_score,
        'divergence':divergence,'fib':fib_level is not None,'sr_touch':sr_touch,
        'alignment':align_type=="PERFECT",'bb_squeeze':bb_compression,
        'trending':"TRENDING" in regime,'volume':vol_confirmed,'hurst_trending':hurst_trending,
        'zscore':zscore_favorable,'gen_signal':gen_bonus>0,'dist':dist_favorable,
        'vr_edge':vr.get('has_edge',False),'acf_edge':acf.get('has_pattern',False)}
    storm_level, storm_bonus, storm_criteria = calculate_storm_bonus(storm_data)

    if storm_level == "PERFECT_STORM" and "BLOCKED" not in sig and sig != "MONITORING":
        sig = sig.replace("LONG","LONG ⭐STORM⭐").replace("SHORT","SHORT ⭐STORM⭐")
        setup_type = "PERFECT_STORM"

    final_db = 0
    if divergence and (("LONG" in sig and "BULLISH" in str(divergence)) or ("SHORT" in sig and "BEARISH" in str(divergence))):
        final_db = abs(div_bonus)

    score = calculate_score(
        adx=adx, momentum_score=momentum, pattern_score=pat_score,
        dist_ema50=abs(c1['close']-c1['EMA_50']), atr=c1['ATR'],
        win_rate=sim['WR'], profit_factor=sim['PF'], profile=adapted_profile,
        divergence_bonus=final_db, fib_bonus=fib_bonus, sr_bonus=sr_bonus,
        alignment_bonus=align_bonus, storm_bonus=storm_bonus,
        regime_bonus=regime_bonus, volume_bonus=vol_bonus,
        hurst_bonus=hurst_bonus, zscore_bonus=zscore_bonus,
        consecutive_bonus=consecutive_bonus, generator_bonus=gen_bonus,
        distribution_bonus=dist_bonus, vr_bonus=vr_bonus, acf_bonus=acf_bonus)

    # Filters
    configs = {"PERFECT_STORM":(100,1.5),"BREAKOUT":(60,1.4),"MEAN_REVERSION":(45,1.1),
               "GEN_VOL_COMPRESS":(40,1.0),"GEN_SPIKE_DRIFT":(35,0.9),"GEN_STEP_REVERT":(35,0.9),
               "GEN_PRICE_DEV":(40,1.0),"DAY":(45,1.2),"SWING":(70,1.4)}
    ms, mpf = configs.get(setup_type, (70, 1.4))
    is_gen_setup = setup_type and "GEN" in str(setup_type)
    if "BLOCKED" not in sig and sig != "MONITORING":
        fails = []
        if score.total < ms: fails.append(f"SCORE={score.total:.0f}<{ms}")
        if sim['NET'] <= 0 and not is_gen_setup: fails.append("NET≤0")
        if sim['PF'] < mpf and not is_gen_setup: fails.append(f"PF={sim['PF']}<{mpf}")
        if fails: sig = f"BLOCKED ({', '.join(fails)})"

    # Targets — 🟢 PRECISION #3: Smart TP
    risk = abs(entry - sl_val)
    if risk == 0: risk = float(c1['ATR'])
    tc = {"PERFECT_STORM":(5,10),"BREAKOUT":(adapted_profile['tp1_r'],adapted_profile['tp2_r']+2),
          "MEAN_REVERSION":(2,3),"GEN_VOL_COMPRESS":(2.5,4),"GEN_SPIKE_DRIFT":(2,5),
          "GEN_STEP_REVERT":(1.5,2.5),"GEN_PRICE_DEV":(2,3.5),"DAY":(2,3),
          "SWING":(adapted_profile['tp1_r'],adapted_profile['tp2_r'])}
    r1, r2 = tc.get(setup_type, (adapted_profile['tp1_r'], adapted_profile['tp2_r']))
    direction = "LONG" if "LONG" in sig else "SHORT"
    tp1, tp2 = smart_tp(entry, direction, risk, r1, r2, sr_levels)

    # Pyramid
    pyramid = ScalingEngine.calculate_pyramid(score.grade, score.total, capital, risk_pct, entry, sl_val, float(c1['ATR']), adapted_profile)

    show = any(x in sig for x in ["SWING","DAY","BREAKOUT","STORM","REVERSION","COMPRESS","DRIFT","STEP","DEVIATION","PRICE"])

    imgs = [
        plot_candles(h4.tail(150), f"{name} H4 — {regime} | Gen:{gen_signal}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels if show else None),
        plot_candles(h1.tail(200), f"{name} H1 — H:{hurst_val} Z:{z_current:.1f} σ:{sigma_calibrated or 0:.3f}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels, fibs if show else None),
        plot_candles(m15.tail(200), f"{name} M15 — BB:{bb_cycle} VR:{vr.get('dominant_type','?')} ACF:{acf.get('dominant_type','?')}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None),
    ]

    confs = []
    if gen_bonus>0: confs.append(f"🧮 Gen: {gen_signal} (+{gen_bonus})")
    if vr.get('has_edge'): confs.append(f"📐 VR: {vr['dominant_type']} ({vr.get('n_significant',0)} sig)")
    if acf.get('has_pattern'): confs.append(f"📊 ACF: {acf['dominant_type']} (lag-1={acf.get('acf_1',0):.3f})")
    if vol_cluster.get('has_clustering'): confs.append(f"🔥 VolCluster: {vol_cluster['vol_regime']}")
    if dist_favorable: confs.append(f"📊 Dist P{dist['percentile']:.0f}")
    if divergence: confs.append(f"🔍 {divergence}")
    if fib_level: confs.append(f"📐 Fib {fib_level}")
    if sr_touch: confs.append(f"🎯 S/R")
    if align_type!="NONE": confs.append(f"⭐ Align {align_type}")
    if storm_level: confs.append(f"🌟 {storm_level} ({len(storm_criteria)}/16)")
    if hurst_trending: confs.append(f"🧬 Hurst {hurst_val}")
    if zscore_favorable: confs.append(f"📊 Z {z_current:.1f}")
    if bb_compression: confs.append("💥 BB Squeeze")
    if trigger_ok and trigger_type!="N/A": confs.append(f"✅ Trigger: {trigger_type}")

    risks = []
    if "RANGING" in regime: risks.append("⚠️ RANGING")
    if not sim['WF_STABLE']: risks.append("⚠️ WF instável")
    if mc.get('positive_pct',0)<55: risks.append(f"⚠️ MC {mc['positive_pct']}%")
    if roc_status=="EXTREME": risks.append("⚠️ ROC EXTREMO")
    if hurst_regime=="RANDOM_WALK": risks.append("⚠️ Random Walk")
    if hurst_regime=="UNRELIABLE": risks.append(f"⚠️ Hurst unreliable R²={hurst_r2}")
    if not vr.get('has_edge'): risks.append("⚠️ VR: sem edge estatístico")
    if gen.get('spike_phase')=="SPIKE_IMMINENT": risks.append("💥 SPIKE IMINENTE")
    if not trigger_ok and c5 is not None: risks.append(f"⚠️ M5 sem trigger ({trigger_type})")

    return {
        "FINAL_DECISION": sig, "TRADE_STYLE": trade_style or "N/A", "SETUP_TYPE": setup_type or "N/A",
        "SETUP_SCORE": float(round(score.total,1)), "BASE_SCORE": float(round(score.base_total,1)),
        "BONUS_SCORE": float(round(score.bonus_total,1)), "SETUP_GRADE": score.grade,
        "INDEX_PROFILE": vc, "GEN_TYPE": gen_type,
        "GEN_ANALYSIS": convert_np(gen), "GEN_SIGNAL": gen_signal, "GEN_BONUS": gen_bonus,
        "SIGMA_CALIBRATED": sigma_calibrated,
        "VR_TEST": convert_np(vr), "VR_BONUS": vr_bonus,
        "ACF_TEST": convert_np(acf), "ACF_BONUS": acf_bonus,
        "VOL_CLUSTER": convert_np(vol_cluster),
        "DIST_ANALYSIS": convert_np(dist), "DIST_BONUS": dist_bonus,
        "HURST": float(hurst_val), "HURST_REGIME": hurst_regime, "HURST_R2": float(hurst_r2),
        "ZSCORE": float(round(z_current,2)),
        "BB_CYCLE": bb_cycle, "CONSECUTIVE": int(consec_count), "CONSECUTIVE_DIR": consec_dir,
        "ROC_STATUS": roc_status, "MARKET_STRUCTURE": structure, "MARKET_REGIME": regime,
        "TRIGGER_OK": trigger_ok, "TRIGGER_TYPE": trigger_type,
        "CONFLUENCES": confs, "RISKS": risks, "MOMENTUM": f"{momentum}/3",
        "ENTRY_TYPE": entry_type, "SL_REASON": sl_reason,
        "WIN_RATE": float(sim['WR']), "NET_PROFIT": float(sim['NET']),
        "MAX_DRAWDOWN": float(sim['DD']), "PROFIT_FACTOR": float(sim['PF']),
        "SHARPE": float(sim['SHARPE']), "SORTINO": float(sim['SORTINO']),
        "WF_STABLE": sim['WF_STABLE'], "FOLD_WRS": sim['FOLD_WRS'],
        "TOTAL_TRADES": int(sim['TOTAL_TRADES']),
        "SETUP_STATS": convert_np(sim.get('SETUP_STATS',{})),
        "MC_MEDIAN": float(mc.get('median',0)), "MC_P5": float(mc.get('p5',0)),
        "MC_P95": float(mc.get('p95',0)), "MC_POSITIVE": float(mc.get('positive_pct',0)),
        "ENTRY": float(round(entry,5)), "SL": float(round(sl_val,5)),
        "TP1": float(round(tp1,5)), "TP2": float(round(tp2,5)),
        "PYRAMID": convert_np(pyramid), "ADAPTED_PROFILE": convert_np({k:v for k,v in adapted_profile.items() if k in ['risk_mult','sl_atr_mult','tp2_r']}),
        "IMAGES": imgs, "ATR": float(c1['ATR']),
        "SCORE_BREAKDOWN": convert_np({
            "ADX":score.trend_strength,"MOM":score.momentum_align,"PAT":score.patterns,
            "VAL":score.value_zone,"HIST":score.historical,
            "DIV":score.divergence_bonus,"FIB":score.fib_bonus,"SR":score.sr_bonus,
            "ALIGN":score.alignment_bonus,"STORM":score.storm_bonus,"REGIME":score.regime_bonus,
            "VOL":score.volume_bonus,"HURST":score.hurst_bonus,"ZSCORE":score.zscore_bonus,
            "CONSEC":score.consecutive_bonus,"GEN":score.generator_bonus,"DIST":score.distribution_bonus,
            "VR":score.vr_bonus,"ACF":score.acf_bonus
        }),
    }

# ==============================================================================
# SCANNER V20 — 🟢 FIX #4: Todos os gen types
# ==============================================================================

async def quick_scan(code, name):
    try:
        raw = await fetch_single(code, 3600, 300)
        if not raw: return None
        df = indicators(prep_df(raw)); profile = get_profile(name)
        if len(df) < 50: return None
        c = df.iloc[-1]; ppy = detect_periods_per_year(df)
        hurst_val, _, hr2 = calculate_hurst_exponent(df['close'])
        z = float(c['ZSCORE']) if pd.notna(c.get('ZSCORE')) else 0
        vr = variance_ratio_test(df['close'])
        gt = profile.get('gen_type','GBM')
        if gt == 'GBM':
            sig_cal = calibrate_sigma(df, ppy)
            gen = GeneratorModelV20.analyze_gbm(df, profile, sig_cal, ppy)
        elif gt in ['BOOM','CRASH']:
            gen = GeneratorModelV20.analyze_crash_boom(df, profile, ppy)
        elif gt == 'STEP':
            gen = GeneratorModelV20.analyze_step(df, profile, ppy)
        else: gen = {}
        regime, _ = classify_regime(df)
        qs = 0
        if c['ADX'] > profile.get('adx_strong',25): qs += 25
        elif c['ADX'] > profile.get('adx_trend_min',15): qs += 12
        if abs(z) > profile.get('zscore_extreme',2)*0.6: qs += 18
        if hurst_val > profile.get('hurst_trend_min',0.53) or hurst_val < 0.45: qs += 12
        if gen.get('signal','NEUTRAL') not in ['NEUTRAL','VOL_NORMAL']: qs += 20
        if vr.get('has_edge'): qs += 15
        if "TRENDING" in regime: qs += 8
        bias = "BULLISH" if c['close'] > c['EMA_200'] else "BEARISH"
        return {"name":name,"code":code,"score":qs,"bias":bias,"adx":round(c['ADX'],1),
                "hurst":round(hurst_val,3),"zscore":round(z,2),"regime":regime,
                "gen_signal":gen.get('signal','N/A'),"vr_edge":vr.get('has_edge',False),
                "vr_type":vr.get('dominant_type','?'),"profile":profile['vol_class']}
    except: return None

# ==============================================================================
# STREAMLIT UI V20
# ==============================================================================

st.sidebar.title("⚡ SI-APATECO V20.0")
st.sidebar.caption("STATISTICAL EDGE ENGINE")

if "GEMINI_API_KEY" in st.secrets:
    api = st.secrets["GEMINI_API_KEY"]; st.sidebar.success("✅ API")
else:
    api = st.sidebar.text_input("API GEMINI", type="password")

st.sidebar.divider()
capital = st.sidebar.number_input("💰 Capital", min_value=100, value=10000, step=100)
risk_pct = st.sidebar.slider("📊 Risco %", 0.5, 3.0, 1.0, 0.1)
mode = st.sidebar.radio("⚙️", ["🔍 Análise", "🔎 Scanner"])

st.title("⚡ SI-APATECO V20.0 — STATISTICAL EDGE ENGINE")
st.caption("20 correções | VR Test | ACF | Vol Cluster | Sigma Calibrado | Smart TP | Kelly")

with st.spinner("Carregando..."): assets = get_assets()
if not assets: st.error("❌ FALHA"); st.stop()

if mode == "🔍 Análise":
    c1c,c2c = st.columns([1,2])
    with c1c:
        target = st.selectbox("🎯 ATIVO", list(assets.keys()))
        prof = get_profile(target)
        st.markdown(f"**{prof['vol_class']}** — `{prof.get('gen_type','?')}`")
        run = st.button("⚡ ANALISAR V20", use_container_width=True)

    with c2c:
        if run:
            if not api: st.error("API KEY"); st.stop()
            status = st.status("⚡ V20.0 STATISTICAL EDGE...", expanded=True)
            status.write("1️⃣ Dados MTF (H1+H4+M15+M5)...")
            h1r,h4r,m15r,m5r,err = asyncio.run(fetch_multi_tf(assets[target]))
            if err: status.update(state='error'); st.error(err); st.stop()
            status.write("2️⃣ Calibrando σ + Generator Model...")
            status.write("3️⃣ Variance Ratio + Autocorrelação + Vol Cluster...")
            status.write("4️⃣ Walk-Forward V20 (multi-setup) + MC Bootstrap...")
            status.write("5️⃣ Kelly + Adaptive + Score 16-factor...")
            data = sniper_core_v20(target,h1r,h4r,m15r,m5r,capital,risk_pct)
            imgs = data.pop("IMAGES")
            status.write("6️⃣ Gemini IA...")
            genai.configure(api_key=api); dc = convert_np(data)
            try:
                model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
                ai = model.generate_content([SYSTEM_PROMPT, f"V20 DATA: {json.dumps(dc)}"]+imgs).text
                status.update(label="✅ V20 COMPLETA",state="complete")
            except Exception as e:
                ai = f"⚠️ IA: {str(e)[:150]}"; status.update(label="⚠️",state="complete")

            g = data['SETUP_GRADE']
            gc = {"S":("score-s","👑"),"A++":("score-a-pp","🏆"),"A+":("score-a-p","💎"),"A":("score-a","⭐"),"B":("score-b","📊")}.get(g,("score-c","⚠️"))
            st.markdown(f"""<div style='text-align:center;padding:25px;background:rgba(168,85,247,0.08);border:3px solid #a855f7;border-radius:15px;'>
                <h1>{gc[1]} GRADE: <span class='{gc[0]}'>{g}</span></h1>
                <p style='font-size:28px;'><strong>SCORE: {data["SETUP_SCORE"]}/170</strong></p>
                <p>Base: {data["BASE_SCORE"]}/100 | Bonus: +{data["BONUS_SCORE"]}/70</p>
                <p style='color:#a855f7;'>⚡ {data["GEN_TYPE"]} — {data.get("SETUP_TYPE","N/A")}</p>
                <p>VR Edge: {'✅ '+data['VR_TEST'].get('dominant_type','') if data['VR_TEST'].get('has_edge') else '❌ Sem edge'} | ACF: {data['ACF_TEST'].get('dominant_type','?')}</p>
            </div>""", unsafe_allow_html=True)

            st.subheader("🧮 GENERATOR MODEL")
            ga = data.get('GEN_ANALYSIS',{})
            g1,g2,g3,g4 = st.columns(4)
            g1.metric("Tipo", data['GEN_TYPE']); g2.metric("Signal", data['GEN_SIGNAL'])
            g3.metric("σ Calibrado", f"{data.get('SIGMA_CALIBRATED',0) or 0:.4f}")
            g4.metric("Gen Bonus", f"+{data['GEN_BONUS']}")
            if data['GEN_TYPE']=='GBM':
                wins = ga.get('windows',{})
                w1,w2,w3 = st.columns(3)
                for col,lbl in [(w1,"SHORT"),(w2,"MEDIUM"),(w3,"LONG")]:
                    w = wins.get(lbl,{})
                    col.metric(f"Vol {lbl}", f"{w.get('vol_ratio',1):.3f}", w.get('signal','?'))
                p1,p2 = st.columns(2)
                p1.metric("Compress Dir", ga.get('compress_direction','?'))
                p2.metric("Price Z", f"{ga.get('z_price',0):.2f}")

            st.subheader("📐 EDGE ESTATÍSTICO")
            e1,e2,e3,e4 = st.columns(4)
            vrt = data.get('VR_TEST',{})
            e1.metric("VR Edge", "✅" if vrt.get('has_edge') else "❌", vrt.get('dominant_type','?'))
            acft = data.get('ACF_TEST',{})
            e2.metric("ACF", acft.get('dominant_type','?'), f"lag1={acft.get('acf_1',0):.4f}")
            vc = data.get('VOL_CLUSTER',{})
            e3.metric("Vol Cluster", vc.get('vol_regime','?'))
            e4.metric("Hurst", f"{data['HURST']:.3f}", f"R²={data.get('HURST_R2',0):.2f}")

            st.subheader("📊 DISTRIBUIÇÃO")
            da = data.get('DIST_ANALYSIS',{})
            d1,d2,d3,d4 = st.columns(4)
            d1.metric("Skew",f"{da.get('skewness',0):.3f}"); d2.metric("Kurt",f"{da.get('kurtosis',3):.3f}")
            d3.metric("Tails",da.get('tail_risk','?')); d4.metric("Percentil",f"{da.get('percentile',50):.0f}%")

            st.subheader("📊 VALIDAÇÃO")
            m1,m2,m3,m4,m5_c,m6 = st.columns(6)
            m1.metric("WR",f"{data['WIN_RATE']}%"); m2.metric("PF",f"{data['PROFIT_FACTOR']}")
            m3.metric("Sharpe",f"{data['SHARPE']}"); m4.metric("Sortino",f"{data['SORTINO']}")
            m5_c.metric("DD",f"{data['MAX_DRAWDOWN']}R"); m6.metric("Trades",f"{data['TOTAL_TRADES']}")
            if data.get('SETUP_STATS'):
                st.caption("Por Setup: " + " | ".join(f"{k}: {v['trades']}t {v['wr']}%" for k,v in data['SETUP_STATS'].items()))
            mc1,mc2,mc3 = st.columns(3)
            mc1.metric("MC Med",f"{data['MC_MEDIAN']}R"); mc2.metric("MC P5",f"{data['MC_P5']}R")
            mc3.metric("MC %+",f"{data['MC_POSITIVE']}%")

            if data['CONFLUENCES']:
                st.subheader("🔥 CONFLUÊNCIAS")
                for c in data['CONFLUENCES']: st.markdown(f"- {c}")
            if data['RISKS']:
                st.subheader("⚠️ RISCOS")
                for r in data['RISKS']: st.warning(r)

            st.divider()
            d = data['FINAL_DECISION']
            if any(x in d for x in ["SWING","DAY","BREAKOUT","STORM","REVERSION","COMPRESS","DRIFT","STEP","DEVIATION","PRICE"]):
                st.success(f"✅ {d}")
                st.dataframe(pd.DataFrame([
                    {"":"Entrada","V":f"{data['ENTRY']}","N":data['ENTRY_TYPE']},
                    {"":"Stop","V":f"{data['SL']}","N":f"Adaptive SL ×{data.get('ADAPTED_PROFILE',{}).get('sl_atr_mult','?')}"},
                    {"":"TP1","V":f"{data['TP1']}","N":"Smart TP (S/R aware)"},
                    {"":"TP2","V":f"{data['TP2']}","N":"Trail"},
                    {"":"M5 Trigger","V":"✅" if data.get('TRIGGER_OK') else "❌","N":data.get('TRIGGER_TYPE','?')},
                ]),hide_index=True,use_container_width=True)
                pyr = data.get('PYRAMID',{})
                if pyr.get('n_levels',0)>1:
                    st.subheader("📈 PIRÂMIDE")
                    for i,l in enumerate(pyr.get('levels',[])):
                        st.info(f"Nível {i+1}: {l['entry']} | {l['risk_pct']}% | {l['trigger']}")
            elif "BLOCKED" in d: st.error(f"🛑 {d}")
            else: st.warning(f"⏸️ {d}")

            tabs = st.tabs(["H4","H1","M15"])
            for i,t in enumerate(tabs):
                with t: st.image(imgs[i], use_container_width=True)
            st.divider(); st.subheader("🤖 IA"); st.markdown(ai)

elif mode == "🔎 Scanner":
    st.subheader("🔎 SCANNER V20")
    if st.button("⚡ ESCANEAR", use_container_width=True):
        with st.spinner("Escaneando..."):
            async def run_scan():
                return await asyncio.gather(*[quick_scan(c,n) for n,c in assets.items()])
            results = asyncio.run(run_scan())
            valid = sorted([r for r in results if r], key=lambda x:x['score'], reverse=True)
        if valid:
            st.success(f"✅ {len(valid)} ativos")
            for i,r in enumerate(valid[:12]):
                e = "🟢" if r['score']>=45 else "🟡" if r['score']>=25 else "🔴"
                vr_icon = "✅" if r.get('vr_edge') else "❌"
                st.markdown(f"""<div class='edge-card'>
                    <strong>{e} #{i+1} {r['name']}</strong> — Score: <b>{r['score']}</b> | {r['bias']} | VR: {vr_icon} {r.get('vr_type','')}<br>
                    <small>ADX:{r['adx']} | H:{r['hurst']} | Z:{r['zscore']} | {r['regime']} | Gen:{r['gen_signal']} | {r['profile']}</small>
                </div>""", unsafe_allow_html=True)
