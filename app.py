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
# --- CORREÇÃO DE IMPORTAÇÃO (FIX DO ERRO SCIPY) ---
from scipy.stats import norm
# Removemos a importação problemática e criamos a função manualmente abaixo
import time
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# FUNÇÃO CORRETIVA PARA O ERRO 'ModuleNotFoundError'
# Substitui: from scipy.stats import median_abs_deviation as scipy_mad
# ==============================================================================
def scipy_mad(data, scale='normal'):
    """
    Calcula o Median Absolute Deviation (MAD) manualmente usando NumPy.
    Isso evita conflitos de versão da biblioteca SciPy no Streamlit Cloud.
    """
    arr = np.array(data)
    med = np.median(arr)
    mad = np.median(np.abs(arr - med))
    # Fator de consistência para distribuição normal (aprox 1.4826)
    if scale == 'normal':
        return mad * 1.4826022185056018
    return mad

# ==============================================================================
# SI-APATECO V20.0 — STATISTICAL EDGE ENGINE
# AUDITORIA CIRÚRGICA COMPLETA: 6 bugs, 5 falhas math, 8 edges, 6 precisões
#
# 🔴 BUG FIX #1: periods_per_year auto-detectado (365×24 para sintéticos)
# 🔴 BUG FIX #2: VOL_COMPRESS direção CONTRA o move recente
# 🔴 BUG FIX #3: Crash/Boom drift segue CÁLCULO não bias
# 🔴 BUG FIX #4: Backtest testa TODOS os tipos de setup
# 🔴 BUG FIX #5: Backtest roda 1× (não 2×)
# 🔴 BUG FIX #6: Monte Carlo com Bootstrap real
# 🟠 MATH FIX #1: Sigma calibrado dos DADOS (não inventado)
# 🟠 MATH FIX #2: Hurst com validação R²
# 🟠 MATH FIX #3: Step Index escala correta (log-returns)
# 🟠 MATH FIX #4: Spike detection com MAD (robusto a outliers)
# 🟠 MATH FIX #5: Drift via regressão linear (não média)
# 🟡 EDGE #1: Variance Ratio Test
# 🟡 EDGE #2: Autocorrelação de Retornos
# 🟡 EDGE #3: Volatility Clustering (GARCH proxy)
# 🟡 EDGE #4: Multi-TF Vol Ratio
# 🟡 EDGE #5: Spike Decay Model (Crash/Boom)
# 🟡 EDGE #6: Preço Teórico vs Real (GBM deviation)
# 🟡 EDGE #7: Regime-Specific Strategy Selection
# 🟡 EDGE #8: Trigger Candle Confirmation
# 🟢 PREC #1: Multi-Window Vol Analysis (30/100/300)
# 🟢 PREC #2: Trailing Stop por regime
# 🟢 PREC #3: Dynamic TP com S/R awareness
# 🟢 PREC #4: Scanner para TODOS os gen types
# 🟢 PREC #5: Adaptive Kelly Criterion
# 🟢 PREC #6: M5 entry timing
# ==============================================================================

st.set_page_config(
    page_title="SI-APATECO V20.0 STATISTICAL EDGE",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Teko:wght@300;600&family=Share+Tech+Mono&display=swap');
    .stApp { background-color:#050505; background-image:linear-gradient(0deg,#000,#0a0a0a); color:#d4d4d4; font-family:'Share Tech Mono',monospace; }
    h1,h2,h3 { font-family:'Teko',sans-serif!important; text-transform:uppercase; color:#fbbf24; letter-spacing:3px; text-shadow:0 0 10px rgba(251,191,36,0.3); }
    div[data-testid="stMetric"] { background-color:#111; border-right:4px solid #fbbf24; padding:15px; }
    .stButton>button { background:linear-gradient(45deg,#d97706,#fbbf24); color:black; font-weight:900; text-transform:uppercase; padding:20px; font-size:20px; border-radius:0; width:100%; border:1px solid #fbbf24; }
    .stButton>button:hover { box-shadow:0 0 30px rgba(251,191,36,0.6); }
    .score-s { color:#a855f7; font-weight:900; font-size:32px; }
    .score-a-pp { color:#10b981; font-weight:900; font-size:30px; }
    .score-a-p { color:#3b82f6; font-weight:900; font-size:28px; }
    .score-a { color:#22d3ee; font-weight:900; font-size:26px; }
    .score-b { color:#fbbf24; font-weight:900; font-size:24px; }
    .score-c { color:#6b7280; font-weight:900; font-size:22px; }
    .gen-model { background:rgba(168,85,247,0.1); border-left:4px solid #a855f7; padding:15px; margin:10px 0; border-radius:0 8px 8px 0; }
    .edge-box { background:rgba(16,185,129,0.08); border:1px solid #10b981; padding:12px; border-radius:8px; margin:5px 0; }
    .bug-fixed { background:rgba(239,68,68,0.05); border-left:3px solid #ef4444; padding:8px; margin:3px 0; }
</style>
""", unsafe_allow_html=True)

SAFETY_SETTINGS = [
    {"category": c, "threshold": "BLOCK_NONE"}
    for c in ["HARM_CATEGORY_HARASSMENT","HARM_CATEGORY_HATE_SPEECH",
              "HARM_CATEGORY_SEXUALLY_EXPLICIT","HARM_CATEGORY_DANGEROUS_CONTENT"]
]

# ==============================================================================
# PROFILES V20 — sigma_annual é REFERÊNCIA INICIAL, calibrado depois dos dados
# ==============================================================================

SYNTHETIC_PROFILES = {
    "VOLATILITY 10 INDEX": {
        "gen_type":"GBM","vol_class":"ULTRA_LOW","sigma_annual_ref":0.10,
        "spread":0.02,"adx_trend_min":12,"adx_strong":20,
        "sl_atr_mult":2.0,"tp1_r":2.5,"tp2_r":4.0,
        "bb_squeeze_threshold":0.5,"zscore_extreme":2.5,
        "hurst_trend_min":0.55,"consecutive_reversal":8,
        "roc_extreme_pct":0.3,"mean_reversion_bias":0.7,"risk_mult":1.3,
    },
    "VOLATILITY 10 (1S) INDEX": {
        "gen_type":"GBM","vol_class":"ULTRA_LOW","sigma_annual_ref":0.10,
        "spread":0.02,"adx_trend_min":12,"adx_strong":20,
        "sl_atr_mult":2.0,"tp1_r":2.5,"tp2_r":4.0,
        "bb_squeeze_threshold":0.5,"zscore_extreme":2.5,
        "hurst_trend_min":0.55,"consecutive_reversal":8,
        "roc_extreme_pct":0.3,"mean_reversion_bias":0.7,"risk_mult":1.3,
    },
    "VOLATILITY 25 INDEX": {
        "gen_type":"GBM","vol_class":"LOW","sigma_annual_ref":0.25,
        "spread":0.03,"adx_trend_min":14,"adx_strong":22,
        "sl_atr_mult":2.2,"tp1_r":2.5,"tp2_r":4.5,
        "bb_squeeze_threshold":0.55,"zscore_extreme":2.3,
        "hurst_trend_min":0.54,"consecutive_reversal":7,
        "roc_extreme_pct":0.5,"mean_reversion_bias":0.6,"risk_mult":1.2,
    },
    "VOLATILITY 25 (1S) INDEX": {
        "gen_type":"GBM","vol_class":"LOW","sigma_annual_ref":0.25,
        "spread":0.03,"adx_trend_min":14,"adx_strong":22,
        "sl_atr_mult":2.2,"tp1_r":2.5,"tp2_r":4.5,
        "bb_squeeze_threshold":0.55,"zscore_extreme":2.3,
        "hurst_trend_min":0.54,"consecutive_reversal":7,
        "roc_extreme_pct":0.5,"mean_reversion_bias":0.6,"risk_mult":1.2,
    },
    "VOLATILITY 50 INDEX": {
        "gen_type":"GBM","vol_class":"MEDIUM","sigma_annual_ref":0.50,
        "spread":0.05,"adx_trend_min":16,"adx_strong":25,
        "sl_atr_mult":2.5,"tp1_r":3.0,"tp2_r":5.0,
        "bb_squeeze_threshold":0.6,"zscore_extreme":2.0,
        "hurst_trend_min":0.53,"consecutive_reversal":6,
        "roc_extreme_pct":0.8,"mean_reversion_bias":0.5,"risk_mult":1.0,
    },
    "VOLATILITY 50 (1S) INDEX": {
        "gen_type":"GBM","vol_class":"MEDIUM","sigma_annual_ref":0.50,
        "spread":0.05,"adx_trend_min":16,"adx_strong":25,
        "sl_atr_mult":2.5,"tp1_r":3.0,"tp2_r":5.0,
        "bb_squeeze_threshold":0.6,"zscore_extreme":2.0,
        "hurst_trend_min":0.53,"consecutive_reversal":6,
        "roc_extreme_pct":0.8,"mean_reversion_bias":0.5,"risk_mult":1.0,
    },
    "VOLATILITY 75 INDEX": {
        "gen_type":"GBM","vol_class":"HIGH","sigma_annual_ref":0.75,
        "spread":0.10,"adx_trend_min":18,"adx_strong":28,
        "sl_atr_mult":3.0,"tp1_r":3.0,"tp2_r":5.0,
        "bb_squeeze_threshold":0.65,"zscore_extreme":1.8,
        "hurst_trend_min":0.52,"consecutive_reversal":5,
        "roc_extreme_pct":1.2,"mean_reversion_bias":0.4,"risk_mult":0.7,
    },
    "VOLATILITY 75 (1S) INDEX": {
        "gen_type":"GBM","vol_class":"HIGH","sigma_annual_ref":0.75,
        "spread":0.10,"adx_trend_min":18,"adx_strong":28,
        "sl_atr_mult":3.0,"tp1_r":3.0,"tp2_r":5.0,
        "bb_squeeze_threshold":0.65,"zscore_extreme":1.8,
        "hurst_trend_min":0.52,"consecutive_reversal":5,
        "roc_extreme_pct":1.2,"mean_reversion_bias":0.4,"risk_mult":0.7,
    },
    "VOLATILITY 100 INDEX": {
        "gen_type":"GBM","vol_class":"EXTREME","sigma_annual_ref":1.00,
        "spread":0.15,"adx_trend_min":20,"adx_strong":30,
        "sl_atr_mult":3.5,"tp1_r":3.0,"tp2_r":5.0,
        "bb_squeeze_threshold":0.7,"zscore_extreme":1.5,
        "hurst_trend_min":0.51,"consecutive_reversal":4,
        "roc_extreme_pct":1.5,"mean_reversion_bias":0.35,"risk_mult":0.5,
    },
    "VOLATILITY 100 (1S) INDEX": {
        "gen_type":"GBM","vol_class":"EXTREME","sigma_annual_ref":1.00,
        "spread":0.15,"adx_trend_min":20,"adx_strong":30,
        "sl_atr_mult":3.5,"tp1_r":3.0,"tp2_r":5.0,
        "bb_squeeze_threshold":0.7,"zscore_extreme":1.5,
        "hurst_trend_min":0.51,"consecutive_reversal":4,
        "roc_extreme_pct":1.5,"mean_reversion_bias":0.35,"risk_mult":0.5,
    },
    "BOOM 300 INDEX": {
        "gen_type":"BOOM","vol_class":"BOOM","spike_lambda":1/300,
        "spike_direction":"UP","drift_direction":"DOWN",
        "spread":0.10,"adx_trend_min":15,"adx_strong":25,
        "sl_atr_mult":2.0,"tp1_r":3.0,"tp2_r":6.0,
        "bb_squeeze_threshold":0.6,"zscore_extreme":2.0,
        "hurst_trend_min":0.52,"consecutive_reversal":5,
        "roc_extreme_pct":2.0,"mean_reversion_bias":0.3,"risk_mult":0.8,
        "sigma_annual_ref":0.50,
    },
    "BOOM 500 INDEX": {
        "gen_type":"BOOM","vol_class":"BOOM","spike_lambda":1/500,
        "spike_direction":"UP","drift_direction":"DOWN",
        "spread":0.10,"adx_trend_min":15,"adx_strong":25,
        "sl_atr_mult":2.0,"tp1_r":3.0,"tp2_r":6.0,
        "bb_squeeze_threshold":0.6,"zscore_extreme":2.0,
        "hurst_trend_min":0.52,"consecutive_reversal":5,
        "roc_extreme_pct":2.0,"mean_reversion_bias":0.3,"risk_mult":0.8,
        "sigma_annual_ref":0.50,
    },
    "BOOM 1000 INDEX": {
        "gen_type":"BOOM","vol_class":"BOOM","spike_lambda":1/1000,
        "spike_direction":"UP","drift_direction":"DOWN",
        "spread":0.10,"adx_trend_min":15,"adx_strong":25,
        "sl_atr_mult":2.5,"tp1_r":3.0,"tp2_r":7.0,
        "bb_squeeze_threshold":0.6,"zscore_extreme":2.0,
        "hurst_trend_min":0.52,"consecutive_reversal":6,
        "roc_extreme_pct":2.0,"mean_reversion_bias":0.3,"risk_mult":0.9,
        "sigma_annual_ref":0.50,
    },
    "CRASH 300 INDEX": {
        "gen_type":"CRASH","vol_class":"CRASH","spike_lambda":1/300,
        "spike_direction":"DOWN","drift_direction":"UP",
        "spread":0.10,"adx_trend_min":15,"adx_strong":25,
        "sl_atr_mult":2.0,"tp1_r":3.0,"tp2_r":6.0,
        "bb_squeeze_threshold":0.6,"zscore_extreme":2.0,
        "hurst_trend_min":0.52,"consecutive_reversal":5,
        "roc_extreme_pct":2.0,"mean_reversion_bias":0.3,"risk_mult":0.8,
        "sigma_annual_ref":0.50,
    },
    "CRASH 500 INDEX": {
        "gen_type":"CRASH","vol_class":"CRASH","spike_lambda":1/500,
        "spike_direction":"DOWN","drift_direction":"UP",
        "spread":0.10,"adx_trend_min":15,"adx_strong":25,
        "sl_atr_mult":2.0,"tp1_r":3.0,"tp2_r":6.0,
        "bb_squeeze_threshold":0.6,"zscore_extreme":2.0,
        "hurst_trend_min":0.52,"consecutive_reversal":5,
        "roc_extreme_pct":2.0,"mean_reversion_bias":0.3,"risk_mult":0.8,
        "sigma_annual_ref":0.50,
    },
    "CRASH 1000 INDEX": {
        "gen_type":"CRASH","vol_class":"CRASH","spike_lambda":1/1000,
        "spike_direction":"DOWN","drift_direction":"UP",
        "spread":0.10,"adx_trend_min":15,"adx_strong":25,
        "sl_atr_mult":2.5,"tp1_r":3.0,"tp2_r":7.0,
        "bb_squeeze_threshold":0.6,"zscore_extreme":2.0,
        "hurst_trend_min":0.52,"consecutive_reversal":6,
        "roc_extreme_pct":2.0,"mean_reversion_bias":0.3,"risk_mult":0.9,
        "sigma_annual_ref":0.50,
    },
    "STEP INDEX": {
        "gen_type":"STEP","vol_class":"STEP",
        "spread":0.01,"adx_trend_min":10,"adx_strong":18,
        "sl_atr_mult":1.5,"tp1_r":2.0,"tp2_r":3.0,
        "bb_squeeze_threshold":0.4,"zscore_extreme":2.0,
        "hurst_trend_min":0.55,"consecutive_reversal":10,
        "roc_extreme_pct":0.2,"mean_reversion_bias":0.8,"risk_mult":1.5,
        "sigma_annual_ref":0.20,
    },
}

DEFAULT_PROFILE = {
    "gen_type":"GBM","vol_class":"UNKNOWN","sigma_annual_ref":0.50,
    "spread":0.05,"adx_trend_min":15,"adx_strong":25,
    "sl_atr_mult":2.5,"tp1_r":3.0,"tp2_r":5.0,
    "bb_squeeze_threshold":0.6,"zscore_extreme":2.0,
    "hurst_trend_min":0.53,"consecutive_reversal":6,
    "roc_extreme_pct":1.0,"mean_reversion_bias":0.5,"risk_mult":1.0,
}

def get_profile(name: str) -> dict:
    for key, profile in SYNTHETIC_PROFILES.items():
        if key in name.upper():
            return profile
    return DEFAULT_PROFILE

# ==============================================================================
# UTILITY: Timeframe detection + Sigma calibration
# ==============================================================================

def detect_periods_per_year(df):
    """🔴 BUG FIX #1: Auto-detect timeframe, use 365 days (synthetic 24/7)"""
    if len(df) < 3:
        return 365 * 24
    avg_delta = (df.index[-1] - df.index[0]).total_seconds() / max(len(df) - 1, 1)
    if avg_delta < 120:
        return 365 * 24 * 60      # ~1min
    elif avg_delta < 1200:
        return 365 * 24 * 4       # ~15min
    elif avg_delta < 5000:
        return 365 * 24           # ~1h = 8760
    elif avg_delta < 20000:
        return 365 * 6            # ~4h = 2190
    else:
        return 365                # daily

def calibrate_sigma(df, periods_per_year):
    """🟠 MATH FIX #1: Calibra sigma real dos dados, não assume"""
    log_ret = np.log(df['close'] / df['close'].shift(1)).dropna()
    if len(log_ret) < 50:
        return 0.5
    return float(log_ret.std() * np.sqrt(periods_per_year))

# ==============================================================================
# 🟡 EDGE #1: VARIANCE RATIO TEST — Detecta se há edge operável
# ==============================================================================

def variance_ratio_test(series, periods=[2, 5, 10, 20]):
    """Se VR≠1, ativo NÃO é random walk → há edge"""
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {}, "INSUFFICIENT"
        var1 = log_ret.var()
        if var1 == 0:
            return {}, "ZERO_VAR"
        results = {}
        for q in periods:
            q_ret = np.log(series / series.shift(q)).dropna()
            if len(q_ret) < 20:
                continue
            var_q = q_ret.var()
            vr = var_q / (q * var1)
            n = len(log_ret)
            z = (vr - 1) / np.sqrt(2 * (2*q - 1) * (q - 1) / (3 * q * n)) if n > 0 else 0
            results[q] = {
                'vr': round(vr, 4), 'z': round(z, 2),
                'significant': abs(z) > 1.96,
                'type': 'MEAN_REVERT' if z < -1.96 else ('MOMENTUM' if z > 1.96 else 'RANDOM')
            }
        # Summary
        sig_results = [r for r in results.values() if r['significant']]
        if not sig_results:
            summary = "RANDOM_WALK"
        elif all(r['type'] == 'MEAN_REVERT' for r in sig_results):
            summary = "MEAN_REVERTING"
        elif all(r['type'] == 'MOMENTUM' for r in sig_results):
            summary = "MOMENTUM"
        else:
            summary = "MIXED"
        return results, summary
    except:
        return {}, "ERROR"

# ==============================================================================
# 🟡 EDGE #2: AUTOCORRELAÇÃO DE RETORNOS
# ==============================================================================

def autocorrelation_analysis(series, max_lag=5):
    """Detecta autocorrelação significativa nos retornos"""
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {}, "INSUFFICIENT"
        sig_threshold = 2.0 / np.sqrt(len(log_ret))
        results = {}
        for lag in range(1, max_lag + 1):
            acf = float(log_ret.autocorr(lag=lag))
            results[lag] = {
                'acf': round(acf, 4),
                'significant': abs(acf) > sig_threshold,
                'type': 'MEAN_REVERT' if acf < -sig_threshold else
                        ('MOMENTUM' if acf > sig_threshold else 'NOISE')
            }
        sig = [r for r in results.values() if r['significant']]
        if not sig:
            summary = "NO_PATTERN"
        elif results[1]['type'] == 'MEAN_REVERT':
            summary = "LAG1_MEAN_REVERT"
        elif results[1]['type'] == 'MOMENTUM':
            summary = "LAG1_MOMENTUM"
        else:
            summary = "WEAK_PATTERN"
        return results, summary
    except:
        return {}, "ERROR"

# ==============================================================================
# 🟡 EDGE #3: VOLATILITY CLUSTERING (GARCH proxy)
# ==============================================================================

def volatility_clustering_test(series, window=20):
    """Detecta se vol se agrupa (GARCH effect)"""
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {"cluster": False, "signal": "INSUFFICIENT"}
        abs_ret = log_ret.abs()
        acf_vol = float(abs_ret.autocorr(lag=1))
        sig = 2.0 / np.sqrt(len(abs_ret))
        has_cluster = acf_vol > sig
        current_vol = abs_ret.tail(window).mean()
        hist_vol = abs_ret.mean()
        vol_regime = current_vol / hist_vol if hist_vol > 0 else 1.0
        if has_cluster and vol_regime > 1.5:
            signal = "HIGH_VOL_CLUSTER"
        elif has_cluster and vol_regime < 0.6:
            signal = "LOW_VOL_CLUSTER"
        elif has_cluster:
            signal = "MODERATE_CLUSTER"
        else:
            signal = "NO_CLUSTER"
        return {
            "cluster": has_cluster, "acf_vol": round(acf_vol, 4),
            "vol_regime": round(vol_regime, 3), "signal": signal
        }
    except:
        return {"cluster": False, "signal": "ERROR"}

# ==============================================================================
# 🟡 EDGE #6: PREÇO TEÓRICO VS REAL (GBM deviation)
# ==============================================================================

def theoretical_price_deviation(df, sigma_calibrated, periods_per_year, lookback=200):
    """Quanto o preço desviou do esperado sob GBM com drift=0"""
    try:
        if len(df) < lookback:
            lookback = len(df) - 1
        if lookback < 20:
            return {"z_price": 0, "direction": "NEUTRAL", "confidence": 0}
        start_price = df['close'].iloc[-lookback]
        current_price = df['close'].iloc[-1]
        t = lookback / periods_per_year
        expected_var = sigma_calibrated**2 * t
        if expected_var <= 0:
            return {"z_price": 0, "direction": "NEUTRAL", "confidence": 0}
        actual_dev = np.log(current_price / start_price)
        z = actual_dev / np.sqrt(expected_var)
        if z > 2:
            direction = "OVERBOUGHT"
        elif z < -2:
            direction = "OVERSOLD"
        elif z > 1:
            direction = "STRETCHED_UP"
        elif z < -1:
            direction = "STRETCHED_DOWN"
        else:
            direction = "NEUTRAL"
        confidence = min(abs(z) / 3.0 * 100, 100)
        return {"z_price": round(z, 2), "direction": direction, "confidence": round(confidence, 1)}
    except:
        return {"z_price": 0, "direction": "NEUTRAL", "confidence": 0}

# ==============================================================================
# GENERATOR MODELS V20 — TODOS OS BUGS CORRIGIDOS
# ==============================================================================

class GeneratorModelV20:

    @staticmethod
    def analyze_gbm(df, profile, sigma_calibrated, ppy):
        """
        🔴 FIX #2: VOL_COMPRESS agora calcula DIREÇÃO contra o move recente
        🟠 FIX #1: Usa sigma calibrado, não sigma_annual_ref
        🟢 PREC #1: Multi-window analysis (30/100/300)
        """
        try:
            log_ret = np.log(df['close'] / df['close'].shift(1)).dropna()
            if len(log_ret) < 50:
                return {"signal": "NEUTRAL", "confidence": 0, "compress_direction": "NEUTRAL"}

            windows = [30, 100, min(300, len(log_ret))]
            analyses = []

            for w in windows:
                if w > len(log_ret):
                    continue
                recent = log_ret.tail(w)
                vol_realized = recent.std() * np.sqrt(ppy)
                ratio = vol_realized / sigma_calibrated if sigma_calibrated > 0 else 1.0

                # Chi² test
                expected_var = (sigma_calibrated / np.sqrt(ppy)) ** 2
                observed_var = recent.var()
                chi2 = (w - 1) * observed_var / expected_var if expected_var > 0 else w
                z_chi = (chi2 - (w - 1)) / np.sqrt(2 * (w - 1)) if w > 1 else 0
                p_value = 2 * (1 - norm.cdf(abs(z_chi)))

                analyses.append({
                    "window": w, "vol_realized": vol_realized,
                    "ratio": ratio, "z_chi": z_chi, "p_value": p_value,
                })

            if not analyses:
                return {"signal": "NEUTRAL", "confidence": 0, "compress_direction": "NEUTRAL"}

            # Use medium window as primary
            primary = analyses[1] if len(analyses) > 1 else analyses[0]
            ratio = primary['ratio']

            # Multi-window consensus
            compress_count = sum(1 for a in analyses if a['ratio'] > 1.25)
            expand_count = sum(1 for a in analyses if a['ratio'] < 0.75)

            if compress_count >= 2:
                signal = "VOL_COMPRESS"
                confidence = min((ratio - 1.0) / 0.5, 1.0) * 100
            elif compress_count == 1 and ratio > 1.3:
                signal = "VOL_COMPRESS"
                confidence = min((ratio - 1.0) / 0.5, 1.0) * 70
            elif expand_count >= 2:
                signal = "VOL_EXPAND"
                confidence = min((1.0 / ratio - 1.0) / 0.5, 1.0) * 100
            elif expand_count == 1 and ratio < 0.7:
                signal = "VOL_EXPAND"
                confidence = min((1.0 / ratio - 1.0) / 0.5, 1.0) * 70
            else:
                signal = "VOL_NORMAL"
                confidence = 0

            # 🔴 FIX #2: DIREÇÃO da compressão = CONTRA o move recente
            lookback = min(100, len(df) - 1)
            recent_move = df['close'].iloc[-1] - df['close'].iloc[-lookback]
            if signal == "VOL_COMPRESS":
                compress_direction = "BEARISH" if recent_move > 0 else "BULLISH"
            elif signal == "VOL_EXPAND":
                compress_direction = "NEUTRAL"  # breakout direction unknown
            else:
                compress_direction = "NEUTRAL"

            return {
                "signal": signal, "confidence": round(confidence, 1),
                "compress_direction": compress_direction,
                "vol_ratio_primary": round(ratio, 3),
                "vol_realized": round(primary['vol_realized'], 4),
                "sigma_calibrated": round(sigma_calibrated, 4),
                "multi_window": [{"w": a['window'], "ratio": round(a['ratio'], 3)} for a in analyses],
                "consensus": f"{compress_count}/{ len(analyses)} compress" if compress_count else f"{expand_count}/{len(analyses)} expand",
                "z_stat": round(primary['z_chi'], 2),
                "p_value": round(primary['p_value'], 4),
                "recent_move_direction": "UP" if recent_move > 0 else "DOWN",
            }
        except:
            return {"signal": "NEUTRAL", "confidence": 0, "compress_direction": "NEUTRAL"}

    @staticmethod
    def analyze_crash_boom(df, profile, ppy):
        """
        🟠 FIX #4: MAD-based spike detection (robusto)
        🟠 FIX #5: Drift via regressão linear
        🟡 EDGE #5: Spike Decay Model
        """
        try:
            if len(df) < 100:
                return {"signal": "NEUTRAL", "drift_direction": "UNKNOWN", "spikes_found": 0}
            returns = df['close'].pct_change().dropna()
            is_boom = profile.get('gen_type') == 'BOOM'

            # 🟠 FIX #4: MAD-based spike detection
            mad = float(scipy_mad(returns.values, scale='normal'))
            if mad == 0:
                mad = returns.std()
            spike_threshold = mad * 4.0

            spike_indices = []
            spike_magnitudes = []
            for i in range(len(returns)):
                r = returns.iloc[i]
                if is_boom and r > spike_threshold:
                    spike_indices.append(i)
                    spike_magnitudes.append(r)
                elif not is_boom and r < -spike_threshold:
                    spike_indices.append(i)
                    spike_magnitudes.append(r)

            last_spike_bars = (len(returns) - spike_indices[-1]) if spike_indices else 999

            # 🟠 FIX #5: Drift via regressão linear entre spikes
            slopes = []
            if len(spike_indices) >= 2:
                for i in range(len(spike_indices) - 1):
                    start = spike_indices[i] + 3
                    end = spike_indices[i + 1]
                    if end - start > 5:
                        segment = df['close'].iloc[start:end].values
                        x = np.arange(len(segment))
                        slope = np.polyfit(x, segment, 1)[0]
                        slopes.append(slope / df['close'].iloc[start])
            # Also add last segment (after last spike)
            if spike_indices:
                start = spike_indices[-1] + 3
                if start < len(df) - 5:
                    segment = df['close'].iloc[start:].values
                    x = np.arange(len(segment))
                    slope = np.polyfit(x, segment, 1)[0]
                    slopes.append(slope / df['close'].iloc[start])

            if slopes:
                drift_slope = float(np.median(slopes))
                drift_dir = "UP" if drift_slope > 0 else "DOWN"
                drift_strength = abs(drift_slope) * 10000
            else:
                drift_slope = 0
                drift_dir = profile.get('drift_direction', 'UNKNOWN')
                drift_strength = 0

            # 🟡 EDGE #5: Spike Decay Model
            avg_between = len(returns) / max(len(spike_indices), 1)
            if spike_indices:
                progress = last_spike_bars / avg_between
                if progress < 0.05:
                    decay_phase = "SPIKE_ABSORBING"
                    drift_multiplier = 0
                elif progress < 0.15:
                    decay_phase = "DRIFT_STRONG"
                    drift_multiplier = 1.5
                elif progress < 0.5:
                    decay_phase = "DRIFT_NORMAL"
                    drift_multiplier = 1.0
                elif progress < 0.8:
                    decay_phase = "DRIFT_WEAKENING"
                    drift_multiplier = 0.5
                else:
                    decay_phase = "SPIKE_ZONE"
                    drift_multiplier = 0
            else:
                progress = 0
                decay_phase = "NO_DATA"
                drift_multiplier = 0.5

            # Signal
            if decay_phase == "DRIFT_STRONG":
                signal = f"DRIFT_{drift_dir}_STRONG"
            elif decay_phase == "DRIFT_NORMAL" and drift_strength > 0.5:
                signal = f"DRIFT_{drift_dir}"
            elif decay_phase == "SPIKE_ZONE":
                signal = "SPIKE_DANGER"
            elif decay_phase == "SPIKE_ABSORBING":
                signal = "POST_SPIKE_WAIT"
            else:
                signal = "NEUTRAL"

            return {
                "signal": signal, "drift_direction": drift_dir,
                "drift_slope": round(drift_slope * 10000, 2),
                "drift_strength": round(drift_strength, 3),
                "spikes_found": len(spike_indices),
                "last_spike_bars": last_spike_bars,
                "avg_bars_between": round(avg_between, 0),
                "decay_phase": decay_phase, "progress": round(progress, 2),
                "drift_multiplier": drift_multiplier,
                "avg_spike_magnitude": round(float(np.mean(np.abs(spike_magnitudes))) * 100, 3) if spike_magnitudes else 0,
            }
        except:
            return {"signal": "NEUTRAL", "drift_direction": "UNKNOWN", "spikes_found": 0}

    @staticmethod
    def analyze_step(df, profile, ppy):
        """🟠 MATH FIX #3: Usa log-returns e escala correta"""
        try:
            if len(df) < 50:
                return {"signal": "NEUTRAL", "deviation_sigma": 0}
            log_ret = np.log(df['close'] / df['close'].shift(1)).dropna()
            # Reference: full series std = expected behavior
            full_std = log_ret.std()
            # Recent: last 100 candles
            window = min(100, len(log_ret))
            recent = log_ret.tail(window)
            recent_std = recent.std()
            # Price deviation from start
            price_change = np.log(df['close'].iloc[-1] / df['close'].iloc[-window])
            expected_std_price = full_std * np.sqrt(window)
            deviation_sigma = price_change / expected_std_price if expected_std_price > 0 else 0

            # Volatility deviation
            vol_ratio = recent_std / full_std if full_std > 0 else 1.0

            # Runs test
            dirs = (recent > 0).astype(int)
            runs = 1
            for i in range(1, len(dirs)):
                if dirs.iloc[i] != dirs.iloc[i - 1]:
                    runs += 1
            n1 = int(dirs.sum())
            n0 = len(dirs) - n1
            if n0 > 0 and n1 > 0 and (n0 + n1) > 1:
                exp_runs = (2 * n0 * n1) / (n0 + n1) + 1
                denom = (n0 + n1)**2 * (n0 + n1 - 1)
                std_runs = np.sqrt(2*n0*n1*(2*n0*n1 - n0 - n1) / denom) if denom > 0 else 1
                z_runs = (runs - exp_runs) / std_runs if std_runs > 0 else 0
            else:
                z_runs = 0
            if z_runs < -2:
                runs_test = "CLUSTERING"
            elif z_runs > 2:
                runs_test = "ALTERNATING"
            else:
                runs_test = "NORMAL"

            if abs(deviation_sigma) > 2.5:
                signal = "EXTREME_DEVIATION"
            elif abs(deviation_sigma) > 1.5:
                signal = "HIGH_DEVIATION"
            elif runs_test == "CLUSTERING":
                signal = "TREND_CLUSTER"
            elif runs_test == "ALTERNATING":
                signal = "MEAN_REVERT_PATTERN"
            else:
                signal = "NEUTRAL"

            return {
                "deviation_sigma": round(deviation_sigma, 2),
                "vol_ratio": round(vol_ratio, 3),
                "runs_test": runs_test, "runs_z": round(z_runs, 2),
                "signal": signal,
                "deviation_direction": "UP" if deviation_sigma > 0 else "DOWN",
            }
        except:
            return {"signal": "NEUTRAL", "deviation_sigma": 0}

# ==============================================================================
# DISTRIBUTION ANALYZER V20 (enhanced)
# ==============================================================================

class DistributionAnalyzerV20:
    @staticmethod
    def analyze(df, window=150):
        try:
            log_ret = np.log(df['close'] / df['close'].shift(1)).dropna()
            if len(log_ret) < window:
                window = len(log_ret)
            if window < 30:
                return {"skewness": 0, "kurtosis": 3, "tail_risk": "NORMAL",
                        "percentile": 50, "signal": "NEUTRAL", "is_normal": True}
            recent = log_ret.tail(window)
            skewness = float(recent.skew())
            kurtosis = float(recent.kurtosis()) + 3
            jb = (window / 6) * (skewness**2 + (1/4)*(kurtosis - 3)**2)
            is_normal = jb < 5.99
            if kurtosis > 5: tail_risk = "FAT_TAILS"
            elif kurtosis > 4: tail_risk = "HEAVY_TAILS"
            elif kurtosis < 2.5: tail_risk = "THIN_TAILS"
            else: tail_risk = "NORMAL"
            # Percentile of recent cumulative return
            recent_cum = recent.tail(10).sum()
            step = max(1, (len(log_ret) - 10) // 100)
            all_win = [log_ret.iloc[i:i+10].sum() for i in range(0, len(log_ret)-10, step)]
            percentile = sum(1 for w in all_win if w < recent_cum) / max(len(all_win), 1)
            signal = "NEUTRAL"
            if abs(skewness) > 0.5:
                signal = "POSITIVE_SKEW" if skewness > 0 else "NEGATIVE_SKEW"
            if tail_risk == "FAT_TAILS":
                signal = "FAT_TAIL_RISK"
            return {
                "skewness": round(skewness, 3), "kurtosis": round(kurtosis, 3),
                "jarque_bera": round(jb, 2), "is_normal": is_normal,
                "tail_risk": tail_risk, "percentile": round(percentile * 100, 1),
                "signal": signal
            }
        except:
            return {"skewness": 0, "kurtosis": 3, "tail_risk": "NORMAL",
                    "percentile": 50, "signal": "NEUTRAL", "is_normal": True}

# ==============================================================================
# ADAPTIVE LEARNER V20 — 🟢 PREC #5: Kelly Criterion
# ==============================================================================

class AdaptiveLearnerV20:
    @staticmethod
    def adjust_profile(profile, bt, dist):
        adj = profile.copy()
        if not bt or bt.get('TOTAL_TRADES', 0) < 8:
            return adj
        wr = bt.get('WR', 50) / 100
        pf = bt.get('PF', 1.0)
        dd = bt.get('DD', 0)
        # Kelly: f* = (p*b - q)/b
        b = pf if pf > 0 else 1.0
        q = 1 - wr
        kelly = (wr * b - q) / b if b > 0 else 0
        kelly = max(0, min(kelly, 0.25))
        dd_penalty = max(0.3, 1 - dd / 20)
        adj['risk_mult'] = round(profile['risk_mult'] * (0.5 + kelly * 2) * dd_penalty, 3)
        adj['risk_mult'] = max(0.3, min(adj['risk_mult'], 2.5))
        if dd > 10:
            adj['sl_atr_mult'] = min(profile['sl_atr_mult'] * 1.15, 4.0)
        elif dd < 3 and wr > 0.55:
            adj['sl_atr_mult'] = max(profile['sl_atr_mult'] * 0.9, 1.5)
        kurt = dist.get('kurtosis', 3)
        if kurt > 4.5:
            adj['tp2_r'] = min(profile['tp2_r'] * 1.3, 10.0)
        elif kurt < 2.5:
            adj['tp2_r'] = max(profile['tp2_r'] * 0.8, 3.0)
        adj['kelly_fraction'] = round(kelly, 4)
        return adj

# ==============================================================================
# SCALING ENGINE V20 (kept from V19, works correctly)
# ==============================================================================

class ScalingEngine:
    @staticmethod
    def calculate_pyramid(grade, score, capital, risk_pct, entry, sl, atr, profile):
        rpu = abs(entry - sl)
        if rpu == 0:
            return {"levels": [{"entry": entry, "risk_pct": risk_pct, "size": 0, "trigger": "BASE"}],
                    "total_risk_pct": risk_pct, "total_size": 0, "n_levels": 1}
        levels = []
        rm = profile.get('risk_mult', 1.0)
        if grade == "S" and score >= 140:
            for mult, rpct, off, trig in [(1.5, 1.5, 0, "STORM ENTRY"), (1.0, 1.0, 0.5, "+0.5 ATR → add"), (0.5, 0.5, 1.5, "+1.5 ATR → add (SL→BE)")]:
                br = capital * (risk_pct * rpct / 100) * rm
                e = entry + atr * off * (1 if entry > sl else -1)
                levels.append({"entry": round(e, 5), "risk_pct": round(risk_pct * rpct, 2),
                               "size": round(br / rpu, 2), "trigger": trig})
        elif grade in ["A++", "A+"] and score >= 90:
            for mult, rpct, off, trig in [(1.0, 1.0, 0, "BASE ENTRY"), (0.5, 0.5, 0.8, "+0.8 ATR → add (SL→BE)")]:
                br = capital * (risk_pct * rpct / 100) * rm
                e = entry + atr * off * (1 if entry > sl else -1)
                levels.append({"entry": round(e, 5), "risk_pct": round(risk_pct * rpct, 2),
                               "size": round(br / rpu, 2), "trigger": trig})
        else:
            br = capital * (risk_pct / 100) * rm
            levels.append({"entry": round(entry, 5), "risk_pct": risk_pct,
                           "size": round(br / rpu, 2), "trigger": "SINGLE ENTRY"})
        return {"levels": levels, "total_risk_pct": round(sum(l['risk_pct'] for l in levels), 2),
                "total_size": round(sum(l['size'] for l in levels), 2), "n_levels": len(levels)}

# ==============================================================================
# NETWORK — Deriv WebSocket
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

async def fetch_tri_force(code):
    reqs = [
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 800, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 400, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 2000, "end": "latest"}
    ]
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=20, close_timeout=15) as ws:
                results = []
                for r in reqs:
                    await ws.send(json.dumps(r))
                    results.append(json.loads(await asyncio.wait_for(ws.recv(), 15)))
                if all('candles' in x for x in results):
                    return results[0]['candles'], results[1]['candles'], results[2]['candles'], None
        except:
            continue
    return None, None, None, "CONNECTION LOST"

async def fetch_single(code, gran, count):
    req = {"ticks_history": code, "style": "candles", "granularity": gran, "count": count, "end": "latest"}
    for url in DERIV_SERVERS:
        res = await socket_req(url, req)
        if res and 'candles' in res:
            return res['candles']
    return None

# ==============================================================================
# TECHNICAL INDICATORS (kept + improved)
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

def calc_rsi(series, period=14):
    delta = series.diff(); gain = delta.where(delta > 0, 0.0); loss = -delta.where(delta < 0, 0.0)
    ag = gain.rolling(period, min_periods=period).mean(); al = loss.rolling(period, min_periods=period).mean()
    for i in range(period, len(series)):
        if pd.notna(ag.iloc[i-1]):
            ag.iloc[i] = (ag.iloc[i-1]*(period-1)+gain.iloc[i])/period
            al.iloc[i] = (al.iloc[i-1]*(period-1)+loss.iloc[i])/period
    return 100 - (100 / (1 + ag / al.replace(0, np.nan)))

def calc_adx(df, w=14):
    df['TR'] = pd.concat([df['high']-df['low'], (df['high']-df['close'].shift()).abs(), (df['low']-df['close'].shift()).abs()], axis=1).max(axis=1)
    pm = np.where((df['high']>df['high'].shift())&(df['low']<=df['low'].shift()), df['high']-df['high'].shift(), 0)
    nm = np.where((df['low']<df['low'].shift())&(df['high']>=df['high'].shift()), df['low'].shift()-df['low'], 0)
    pm = np.where(pm > nm, pm, 0); nm = np.where(nm > pm, nm, 0)
    df['+DM_E'] = pd.Series(pm, index=df.index).ewm(span=w, adjust=False).mean()
    df['-DM_E'] = pd.Series(nm, index=df.index).ewm(span=w, adjust=False).mean()
    df['TR_E'] = df['TR'].ewm(span=w, adjust=False).mean()
    df['+DI'] = (df['+DM_E']/df['TR_E'])*100; df['-DI'] = (df['-DM_E']/df['TR_E'])*100
    di_s = (df['+DI']+df['-DI']).replace(0, np.nan)
    df['ADX'] = ((df['+DI']-df['-DI']).abs()/di_s*100).ewm(span=w, adjust=False).mean()
    df.drop(columns=['TR','+DM_E','-DM_E','TR_E'], inplace=True, errors='ignore')
    return df

def calc_hurst(series, max_lag=100):
    """🟠 MATH FIX #2: Hurst com validação R²"""
    try:
        ts = series.dropna().values
        if len(ts) < 50:
            return 0.5, "INSUFFICIENT", 0
        lags = range(10, min(max_lag, len(ts)//3))
        rs_v = []
        for lag in lags:
            nc = len(ts) // lag
            if nc < 1: continue
            rsl = []
            for i in range(nc):
                ch = ts[i*lag:(i+1)*lag]; m = np.mean(ch); d = ch - m
                cu = np.cumsum(d); R = np.max(cu) - np.min(cu); S = np.std(ch, ddof=1)
                if S > 0: rsl.append(R/S)
            if rsl: rs_v.append((np.log(lag), np.log(np.mean(rsl))))
        if len(rs_v) < 4:
            return 0.5, "INSUFFICIENT", 0
        x = np.array([v[0] for v in rs_v]); y = np.array([v[1] for v in rs_v])
        coeffs = np.polyfit(x, y, 1); H = max(0.0, min(1.0, coeffs[0]))
        # R² validation
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred)**2); ss_tot = np.sum((y - np.mean(y))**2)
        r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        if r_sq < 0.6:
            return 0.5, "UNRELIABLE", round(r_sq, 3)
        if H > 0.6: reg = "STRONG_TREND"
        elif H > 0.53: reg = "WEAK_TREND"
        elif H > 0.47: reg = "RANDOM_WALK"
        elif H > 0.4: reg = "WEAK_MEAN_REVERT"
        else: reg = "STRONG_MEAN_REVERT"
        return round(H, 3), reg, round(r_sq, 3)
    except:
        return 0.5, "ERROR", 0

def indicators(df):
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['RSI'] = calc_rsi(df['close'])
    hl = df['high']-df['low']; hc = (df['high']-df['close'].shift()).abs(); lc = (df['low']-df['close'].shift()).abs()
    df['ATR'] = pd.concat([hl, hc, lc], axis=1).max(axis=1).ewm(span=14, adjust=False).mean()
    df = calc_adx(df)
    ema_f = df['close'].ewm(span=12, adjust=False).mean(); ema_s = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_f - ema_s; df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    df['BB_mid'] = df['close'].rolling(20).mean(); df['BB_std'] = df['close'].rolling(20).std()
    df['BB_upper'] = df['BB_mid'] + df['BB_std']*2; df['BB_lower'] = df['BB_mid'] - df['BB_std']*2
    df['BB_width'] = ((df['BB_upper']-df['BB_lower'])/df['BB_mid'].replace(0, np.nan))*100
    zmean = df['close'].rolling(50).mean(); zstd = df['close'].rolling(50).std()
    df['ZSCORE'] = (df['close'] - zmean) / zstd.replace(0, np.nan)
    df.dropna(inplace=True)
    return df

# ==============================================================================
# STRUCTURAL: Pivots, Divergence, S/R, Fib, Patterns
# ==============================================================================

def find_pivots(data, order=5, kind='high'):
    vals = data.values if hasattr(data, 'values') else np.array(data)
    pivots = []
    for i in range(order, len(vals)-order):
        if np.isnan(vals[i]): continue
        if kind == 'high' and all(vals[i] > vals[i-j] and vals[i] > vals[i+j] for j in range(1, order+1)):
            pivots.append(i)
        elif kind == 'low' and all(vals[i] < vals[i-j] and vals[i] < vals[i+j] for j in range(1, order+1)):
            pivots.append(i)
    return np.array(pivots)

def detect_divergence(df, ind='RSI', order=5):
    try:
        if len(df) < order*2+5 or ind not in df.columns: return None, 0, ""
        ph = find_pivots(df['high'], order, 'high'); pl = find_pivots(df['low'], order, 'low')
        ih = find_pivots(df[ind], order, 'high'); il = find_pivots(df[ind], order, 'low')
        if len(ph)>=2 and len(ih)>=2:
            p1,p2 = ph[-2],ph[-1]; i1 = ih[np.argmin(np.abs(ih-p1))]; i2 = ih[np.argmin(np.abs(ih-p2))]
            if abs(i1-p1)<=3 and abs(i2-p2)<=3:
                if df['high'].iloc[p2]>df['high'].iloc[p1] and df[ind].iloc[i2]<df[ind].iloc[i1]:
                    s = min((df['high'].iloc[p2]-df['high'].iloc[p1])/df['high'].iloc[p1]*100 + (df[ind].iloc[i1]-df[ind].iloc[i2])/max(df[ind].iloc[i1],1)*100, 10)
                    if s > 1: return "BEARISH_DIV", -int(min(s*3, 20)), f"Price HH vs {ind} LH"
        if len(pl)>=2 and len(il)>=2:
            p1,p2 = pl[-2],pl[-1]; i1 = il[np.argmin(np.abs(il-p1))]; i2 = il[np.argmin(np.abs(il-p2))]
            if abs(i1-p1)<=3 and abs(i2-p2)<=3:
                if df['low'].iloc[p2]<df['low'].iloc[p1] and df[ind].iloc[i2]>df[ind].iloc[i1]:
                    s = min((df['low'].iloc[p1]-df['low'].iloc[p2])/df['low'].iloc[p1]*100 + (df[ind].iloc[i2]-df[ind].iloc[i1])/max(abs(df[ind].iloc[i1]),1)*100, 10)
                    if s > 1: return "BULLISH_DIV", int(min(s*3, 20)), f"Price LL vs {ind} HL"
        if len(pl)>=2 and len(il)>=2:
            p1,p2 = pl[-2],pl[-1]; i1 = il[np.argmin(np.abs(il-p1))]; i2 = il[np.argmin(np.abs(il-p2))]
            if abs(i1-p1)<=3 and abs(i2-p2)<=3:
                if df['low'].iloc[p2]>df['low'].iloc[p1] and df[ind].iloc[i2]<df[ind].iloc[i1]:
                    return "HIDDEN_BULL", 15, "Hidden: Price HL vs ind LL"
        if len(ph)>=2 and len(ih)>=2:
            p1,p2 = ph[-2],ph[-1]; i1 = ih[np.argmin(np.abs(ih-p1))]; i2 = ih[np.argmin(np.abs(ih-p2))]
            if abs(i1-p1)<=3 and abs(i2-p2)<=3:
                if df['high'].iloc[p2]<df['high'].iloc[p1] and df[ind].iloc[i2]>df[ind].iloc[i1]:
                    return "HIDDEN_BEAR", -15, "Hidden: Price LH vs ind HH"
        return None, 0, ""
    except:
        return None, 0, ""

def detect_sr(df, window=100, min_touches=3):
    try:
        if len(df)<window or 'ATR' not in df.columns: return []
        rec = df.tail(window); atr = rec['ATR'].iloc[-1]
        if pd.isna(atr) or atr == 0: return []
        tol = atr * 0.3
        hp = find_pivots(rec['high'], 3, 'high'); lp = find_pivots(rec['low'], 3, 'low')
        prices = sorted([rec['high'].iloc[i] for i in hp] + [rec['low'].iloc[i] for i in lp])
        if not prices: return []
        clusters, cur = [], [prices[0]]
        for i in range(1, len(prices)):
            if prices[i] - cur[-1] <= tol: cur.append(prices[i])
            else:
                if len(cur) >= min_touches: clusters.append(cur)
                cur = [prices[i]]
        if len(cur) >= min_touches: clusters.append(cur)
        cp = df['close'].iloc[-1]
        levels = [{'price':round(np.mean(c),4), 'touches':len(c), 'type':'RESISTANCE' if np.mean(c)>cp else 'SUPPORT',
                   'strength':len(c)+(1 if max(c)-min(c)<tol*0.5 else 0),
                   'zone_high':round(max(c),4), 'zone_low':round(min(c),4)} for c in clusters]
        levels.sort(key=lambda x:x['strength'], reverse=True)
        return levels[:6]
    except:
        return []

def calc_fib(df, lookback=100):
    try:
        if len(df)<lookback: return {}, None, None
        rec = df.tail(lookback)
        hp = find_pivots(rec['high'], 7, 'high'); lp = find_pivots(rec['low'], 7, 'low')
        if len(hp)==0 or len(lp)==0: return {}, None, None
        sh = rec['high'].iloc[hp[-1]]; sl = rec['low'].iloc[lp[-1]]
        if pd.isna(sh) or pd.isna(sl) or sh == sl: return {}, None, None
        d = sh - sl
        if hp[-1] > lp[-1]:
            fibs = {'23.6%':sh-d*0.236, '38.2%':sh-d*0.382, '50%':sh-d*0.5, '61.8%':sh-d*0.618, '78.6%':sh-d*0.786}
            return fibs, "UP", {'high':sh, 'low':sl}
        else:
            fibs = {'23.6%':sl+d*0.236, '38.2%':sl+d*0.382, '50%':sl+d*0.5, '61.8%':sl+d*0.618, '78.6%':sl+d*0.786}
            return fibs, "DOWN", {'high':sh, 'low':sl}
    except:
        return {}, None, None

def check_fib(price, fibs, atr):
    try:
        if not fibs or pd.isna(price) or atr == 0: return None, 0
        for n, lv in fibs.items():
            if pd.notna(lv) and abs(price-lv) < atr*0.4:
                return n, (15 if '61.8' in n else 10 if '50' in n or '38.2' in n else 5)
        return None, 0
    except:
        return None, 0

def detect_patterns(df):
    pats, scores = [], []
    for i in range(1, len(df)):
        c, p = df.iloc[i], df.iloc[i-1]; pl, sc = [], 0
        body = abs(c['close']-c['open']); rng = c['high']-c['low']
        if rng > 0:
            uw = c['high']-max(c['open'],c['close']); lw = min(c['open'],c['close'])-c['low']
            if lw>0 and body/rng<0.35 and uw<body and lw/max(body,1e-8)>2:
                pl.append("PIN_BULL"); sc += 8
            elif uw>0 and body/rng<0.35 and lw<body and uw/max(body,1e-8)>2:
                pl.append("PIN_BEAR"); sc += 8
        cb = abs(c['close']-c['open']); pb = abs(p['close']-p['open'])
        if c['close']>c['open'] and p['close']<p['open'] and min(c['open'],c['close'])<min(p['open'],p['close']) and max(c['open'],c['close'])>max(p['open'],p['close']):
            pl.append("ENGULF_BULL"); sc += 8
        elif c['close']<c['open'] and p['close']>p['open'] and min(c['open'],c['close'])<min(p['open'],p['close']) and max(c['open'],c['close'])>max(p['open'],p['close']):
            pl.append("ENGULF_BEAR"); sc += 8
        if c['high']<=p['high'] and c['low']>=p['low']: pl.append("INSIDE"); sc += 5
        if rng > 0 and body/rng < 0.1: pl.append("DOJI"); sc += 3
        pats.append(pl); scores.append(sc)
    df['patterns'] = [[]] + pats; df['pattern_score'] = [0] + scores
    return df

# 🟡 EDGE #8: Trigger Candle Confirmation
def trigger_confirmed(df, direction):
    """Verifica se último candle confirma entrada"""
    try:
        if len(df) < 3: return False, "NO_DATA"
        last = df.iloc[-1]; prev = df.iloc[-2]
        rng = last['high'] - last['low']
        body_pct = abs(last['close']-last['open']) / rng if rng > 0 else 0
        if direction == "BULLISH":
            bull = last['close'] > last['open']
            above = last['close'] > prev['close']
            strong = body_pct > 0.5
            if bull and above and strong: return True, "STRONG_TRIGGER"
            elif bull and above: return True, "WEAK_TRIGGER"
            return False, "NO_TRIGGER"
        else:
            bear = last['close'] < last['open']
            below = last['close'] < prev['close']
            strong = body_pct > 0.5
            if bear and below and strong: return True, "STRONG_TRIGGER"
            elif bear and below: return True, "WEAK_TRIGGER"
            return False, "NO_TRIGGER"
    except:
        return False, "ERROR"

def detect_bb_cycle(df, profile, lookback=30):
    try:
        if len(df)<lookback: return "UNKNOWN", 0, 0
        rec = df.tail(lookback); bw = rec['BB_width']; avg = bw.mean(); cur = bw.iloc[-1]
        if avg == 0: return "UNKNOWN", 0, 0
        ratio = cur / avg; thr = profile['bb_squeeze_threshold']
        sc = int(sum(bw < avg * thr))
        if ratio < thr: return "SQUEEZE", ratio, sc
        elif ratio > 1.5: return "EXPANSION", ratio, 0
        return "NORMAL", ratio, 0
    except:
        return "UNKNOWN", 0, 0

def count_consecutive(df, lookback=20):
    try:
        rec = df.tail(lookback); dirs = (rec['close']>rec['open']).astype(int)
        cd = dirs.iloc[-1]; streak = 0
        for i in range(len(dirs)-1, -1, -1):
            if dirs.iloc[i] == cd: streak += 1
            else: break
        return streak, "BULL" if cd==1 else "BEAR"
    except:
        return 0, "UNK"

def detect_roc(df, profile, periods=[5,10,20]):
    try:
        res = {}; thr = profile['roc_extreme_pct']
        for p in periods:
            if len(df)<p+1: continue
            roc = ((df['close'].iloc[-1]-df['close'].iloc[-p-1])/df['close'].iloc[-p-1])*100
            st = "EXTREME" if abs(roc)>thr*2 else("ELEVATED" if abs(roc)>thr else "NORMAL")
            res[p] = {'value':round(roc,3), 'status':st}
        overall = "NORMAL"
        for r in res.values():
            if r['status']=="EXTREME": overall = "EXTREME"; break
            elif r['status']=="ELEVATED": overall = "ELEVATED"
        return overall, res
    except:
        return "NORMAL", {}

def micro_pullback(df, direction, atr):
    try:
        if len(df)<5 or 'EMA_20' not in df.columns: return None, "MARKET"
        c = df.iloc[-1]; p = df.iloc[-2]
        if direction=="BULLISH":
            if c['close']<p['close'] and c['close']>c['EMA_20'] and c['low']>c.get('EMA_50', c['EMA_20']):
                return (c['low']+c['EMA_20'])/2, "MICRO_PB"
            if abs(c['low']-c['EMA_20'])<atr*0.3 and c['close']>c['EMA_20']:
                return c['EMA_20']+atr*0.1, "EMA_RETEST"
        else:
            if c['close']>p['close'] and c['close']<c['EMA_20'] and c['high']<c.get('EMA_50', c['EMA_20']):
                return (c['high']+c['EMA_20'])/2, "MICRO_PB"
            if abs(c['high']-c['EMA_20'])<atr*0.3 and c['close']<c['EMA_20']:
                return c['EMA_20']-atr*0.1, "EMA_RETEST"
        return None, "MARKET"
    except:
        return None, "MARKET"

def classify_regime(df, lookback=50):
    try:
        if len(df)<lookback: return "UNKNOWN", 0
        rec = df.tail(lookback); c = rec.iloc[-1]; adx = c['ADX']
        slope = (rec['EMA_50'].iloc[-1]-rec['EMA_50'].iloc[-10])/(c['ATR']*10) if c['ATR']>0 else 0
        bw = c['BB_width']/rec['BB_width'].mean() if rec['BB_width'].mean()>0 else 1
        sc = 0
        if adx>30: sc+=3
        elif adx>20: sc+=2
        elif adx>15: sc+=1
        if abs(slope)>0.3: sc+=2
        elif abs(slope)>0.15: sc+=1
        if bw>1.3: sc+=1
        elif bw<0.7: sc-=1
        if sc>=4: return "TRENDING_STRONG", sc
        elif sc>=2: return "TRENDING_WEAK", sc
        elif sc<=0: return "RANGING", sc
        return "TRANSITIONAL", sc
    except:
        return "UNKNOWN", 0

def market_structure(df):
    try:
        ph = find_pivots(df['high'], 5, 'high'); pl = find_pivots(df['low'], 5, 'low')
        sh = df['high'].iloc[ph[-4:]] if len(ph)>=4 else df['high'].iloc[ph] if len(ph)>=2 else pd.Series()
        sl = df['low'].iloc[pl[-4:]] if len(pl)>=4 else df['low'].iloc[pl] if len(pl)>=2 else pd.Series()
        if len(sh)<2 or len(sl)<2: return "UNKNOWN"
        hh = sh.iloc[-1]>sh.iloc[-2]; hl = sl.iloc[-1]>sl.iloc[-2]
        ll = sl.iloc[-1]<sl.iloc[-2]; lh = sh.iloc[-1]<sh.iloc[-2]
        if hh and hl: return "UPTREND"
        elif ll and lh: return "DOWNTREND"
        return "RANGE"
    except:
        return "UNKNOWN"

def tick_volume(df, lookback=20):
    try:
        if len(df)<lookback: return "NORMAL", 1.0
        rec = df.tail(lookback)
        rr = (rec['high'].iloc[-1]-rec['low'].iloc[-1])/(rec['high']-rec['low']).mean() if (rec['high']-rec['low']).mean()>0 else 1
        br = abs(rec['close'].iloc[-1]-rec['open'].iloc[-1])/abs(rec['close']-rec['open']).mean() if abs(rec['close']-rec['open']).mean()>0 else 1
        p = (rr+br)/2
        if p>2: return "VERY_HIGH", p
        elif p>1.5: return "HIGH", p
        elif p>0.7: return "NORMAL", p
        return "LOW", p
    except:
        return "NORMAL", 1.0

# ==============================================================================
# 🔴 BUG FIX #4: WALK-FORWARD V20 — Testa TODOS os tipos de setup
# ==============================================================================

def detect_swing_sl(df, direction, atr_mult=1.5):
    ph = find_pivots(df['high'], 5, 'high'); pl = find_pivots(df['low'], 5, 'low')
    atr = df['ATR'].iloc[-1]
    if direction == "BUY":
        return (df['low'].iloc[pl[-1]] - atr * atr_mult) if len(pl) else df['low'].tail(20).min() - atr * atr_mult
    else:
        return (df['high'].iloc[ph[-1]] + atr * atr_mult) if len(ph) else df['high'].tail(20).max() + atr * atr_mult

def walk_forward_v20(df, trend_dir, profile, sigma_cal, ppy, n_folds=4):
    """🔴 BUG FIX #4: Tests ALL setup types including generator-based"""
    spread = profile['spread']; sl_mult = profile['sl_atr_mult']
    fold_size = len(df) // (n_folds + 1)
    all_trades = []
    fold_results = []

    for fold in range(n_folds):
        ts = fold_size * (fold + 1)
        te = fold_size * (fold + 2) if fold < n_folds - 1 else len(df)
        if ts >= len(df) - 60:
            break
        ft, fw, fb = 0, 0, 0.0
        si = max(250, ts)
        cooldown = 0

        for i in range(si, min(te, len(df) - 60)):
            if cooldown > 0:
                cooldown -= 1
                continue

            row = df.iloc[i]; atr = row['ATR']; sig = None
            if atr == 0: continue
            sub = df.iloc[:i+1]

            # === SETUP 1: Classic Swing (ADX + EMA) ===
            if trend_dir == "BULLISH" and row['ADX'] > profile['adx_strong']:
                if row['close'] > row['EMA_200'] and (abs(row['close']-row['EMA_50'])<atr*1.5 or row['RSI']<45):
                    sig = "BUY"
            elif trend_dir == "BEARISH" and row['ADX'] > profile['adx_strong']:
                if row['close'] < row['EMA_200'] and (abs(row['close']-row['EMA_50'])<atr*1.5 or row['RSI']>55):
                    sig = "SELL"

            # === SETUP 2: Mean Reversion (Z-Score) ===
            if not sig and 'ZSCORE' in row.index:
                z = row['ZSCORE']
                if pd.notna(z):
                    if z < -profile['zscore_extreme'] * 0.6 and trend_dir == "BULLISH":
                        sig = "BUY"
                    elif z > profile['zscore_extreme'] * 0.6 and trend_dir == "BEARISH":
                        sig = "SELL"

            # === SETUP 3: Vol Compress (GBM only) ===
            if not sig and profile.get('gen_type') == 'GBM' and i > si + 100:
                lr = np.log(sub['close'] / sub['close'].shift(1)).dropna().tail(100)
                if len(lr) >= 50:
                    vr = lr.std() * np.sqrt(ppy)
                    ratio = vr / sigma_cal if sigma_cal > 0 else 1
                    if ratio > 1.3:
                        recent_move = sub['close'].iloc[-1] - sub['close'].iloc[-50]
                        sig = "SELL" if recent_move > 0 else "BUY"

            if not sig:
                continue

            entry = row['close'] + (spread if sig == "BUY" else -spread)
            sl_c = detect_swing_sl(sub, sig)
            if sig == "BUY":
                sl = max(entry - sl_mult * atr, sl_c)
            else:
                sl = min(entry + sl_mult * atr, sl_c)
            risk = abs(entry - sl)
            if risk == 0: risk = atr
            tp1 = entry + (profile['tp1_r']*risk) if sig=="BUY" else entry - (profile['tp1_r']*risk)
            tp2 = entry + (profile['tp2_r']*risk) if sig=="BUY" else entry - (profile['tp2_r']*risk)

            # 🟢 PREC #3: Check S/R obstacles for TP
            # Simple: if strong S/R between entry and tp1, reduce tp1
            sr = detect_sr(sub, 80, 3)
            for s in sr:
                if sig == "BUY" and entry < s['price'] < tp1 and s['strength'] >= 4:
                    tp1 = s['price'] - risk * 0.1; break
                elif sig == "SELL" and tp1 < s['price'] < entry and s['strength'] >= 4:
                    tp1 = s['price'] + risk * 0.1; break

            p1ok, p2ok = True, True; r1, r2 = 0, 0; csl = sl; trailing = False

            # 🟢 PREC #2: Regime-based trailing
            reg, _ = classify_regime(sub)
            if "STRONG" in reg: trail_mult = 3.0
            elif "RANGING" in reg: trail_mult = 1.5
            else: trail_mult = 2.0

            for f in range(i+1, min(i+80, len(df))):
                nx = df.iloc[f]
                if sig == "BUY":
                    if nx['low'] <= csl:
                        if p1ok: r1 = (csl-entry)/risk
                        if p2ok: r2 = (csl-entry)/risk
                        break
                    if p1ok and nx['high'] >= tp1:
                        r1 = profile['tp1_r'] - spread/risk; p1ok = False
                        csl = entry + spread; trailing = True
                    if trailing and p2ok:
                        csl = max(csl, nx['high'] - trail_mult * atr)
                        if nx['high'] >= tp2:
                            r2 = profile['tp2_r'] - spread/risk; p2ok = False; break
                else:
                    if nx['high'] >= csl:
                        if p1ok: r1 = (entry-csl)/risk
                        if p2ok: r2 = (entry-csl)/risk
                        break
                    if p1ok and nx['low'] <= tp1:
                        r1 = profile['tp1_r'] - spread/risk; p1ok = False
                        csl = entry - spread; trailing = True
                    if trailing and p2ok:
                        csl = min(csl, nx['low'] + trail_mult * atr)
                        if nx['low'] <= tp2:
                            r2 = profile['tp2_r'] - spread/risk; p2ok = False; break

            result = r1 * 0.5 + r2 * 0.5
            if not (p1ok and p2ok):
                ft += 1; fb += result
                all_trades.append(result)
                if result > 0: fw += 1
                cooldown = 3

        if ft > 0:
            fold_results.append({'fold': fold, 'trades': ft, 'wr': fw/ft*100, 'balance': fb})

    if not all_trades:
        return {"WR":0,"NET":0,"DD":0,"PF":0,"SHARPE":0,"SORTINO":0,
                "WF_STABLE":False,"FOLD_WRS":[],"TOTAL_TRADES":0,"RESULTS":[]}
    results = np.array(all_trades)
    wins = results[results>0]; losses = results[results<=0]
    wr = len(wins)/len(results)*100; net = float(np.sum(results))
    gp = float(np.sum(wins)) if len(wins) else 0
    gl = float(np.abs(np.sum(losses))) if len(losses) else 0
    pf = gp/gl if gl>0 else (gp if gp>0 else 0)
    cum = np.cumsum(results); peak = np.maximum.accumulate(cum)
    dd = float((peak-cum).max()) if len(cum)>0 else 0
    rs = pd.Series(results)
    sharpe = float(rs.mean()/rs.std()*np.sqrt(252)) if len(rs)>=2 and rs.std()>0 else 0
    ds = rs[rs<0]; sortino = float(rs.mean()/ds.std()*np.sqrt(252)) if len(ds)>=2 and ds.std()>0 else 0
    fwrs = [f['wr'] for f in fold_results]
    return {"WR":round(wr,1),"NET":round(net,1),"DD":round(dd,1),"PF":round(pf,2),
            "SHARPE":round(sharpe,2),"SORTINO":round(sortino,2),
            "WF_STABLE":len(fwrs)>=2 and all(w>30 for w in fwrs),
            "FOLD_WRS":[round(w,1) for w in fwrs],"TOTAL_TRADES":len(results),
            "RESULTS":results.tolist()}

# ==============================================================================
# 🔴 BUG FIX #6: MONTE CARLO COM BOOTSTRAP REAL
# ==============================================================================

def monte_carlo_bootstrap(results, n_sim=1000, n_trades=50):
    """Bootstrap real dos resultados do backtest"""
    try:
        results = np.array(results)
        if len(results) < 5:
            return {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":0}
        sims = []
        for _ in range(n_sim):
            sampled = np.random.choice(results, size=min(n_trades, len(results)*2), replace=True)
            sims.append(float(np.sum(sampled)))
        sims = np.array(sims)
        return {"median":round(float(np.median(sims)),1),
                "p5":round(float(np.percentile(sims,5)),1),
                "p95":round(float(np.percentile(sims,95)),1),
                "p25":round(float(np.percentile(sims,25)),1),
                "p75":round(float(np.percentile(sims,75)),1),
                "positive_pct":round(float(np.mean(sims>0)*100),1)}
    except:
        return {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":0}

# ==============================================================================
# SCORING V20 + CONFLUENCE
# ==============================================================================

@dataclass
class Score20:
    trend:float; momentum:float; patterns:float; value:float; historical:float; base:float
    div_b:float; fib_b:float; sr_b:float; align_b:float; storm_b:float; regime_b:float
    vol_b:float; hurst_b:float; zscore_b:float; consec_b:float
    gen_b:float; dist_b:float; vr_b:float; acf_b:float
    bonus:float; total:float; grade:str

def calc_score(adx, mom, pat, dist_ema, atr, wr, pf, profile, **b):
    ts = 25 if adx>profile['adx_strong'] else(15 if adx>profile['adx_trend_min'] else 0)
    mp = (mom/3)*20; vs = 15 if dist_ema/atr<0.5 else(10 if dist_ema/atr<1 else(5 if dist_ema/atr<1.5 else 0)) if atr>0 else 0
    hs = min(wr*0.15+pf*5, 25); base = ts+mp+pat+vs+hs
    keys = ['div_b','fib_b','sr_b','align_b','storm_b','regime_b','vol_b','hurst_b','zscore_b','consec_b','gen_b','dist_b','vr_b','acf_b']
    bv = [b.get(k,0) for k in keys]
    bonus = min(sum(bv), 70)
    total = base + bonus
    if total>=160: g="S"
    elif total>=135: g="A++"
    elif total>=105: g="A+"
    elif total>=80: g="A"
    elif total>=60: g="B"
    elif total>=40: g="C"
    else: g="D"
    return Score20(ts,mp,pat,vs,hs,base,*[b.get(k,0) for k in keys],bonus,total,g)

def alignment_check(c4, c1, cm, d):
    sc = 0
    if d=="BULLISH":
        if c4['close']>c4['EMA_20']>c4['EMA_50']>c4['EMA_200']: sc+=10
        if c1['close']>c1['EMA_20']>c1['EMA_50']>c1['EMA_200']: sc+=10
        if cm['close']>cm['EMA_20']>cm['EMA_50']>cm['EMA_200']: sc+=10
    else:
        if c4['close']<c4['EMA_20']<c4['EMA_50']<c4['EMA_200']: sc+=10
        if c1['close']<c1['EMA_20']<c1['EMA_50']<c1['EMA_200']: sc+=10
        if cm['close']<cm['EMA_20']<cm['EMA_50']<cm['EMA_200']: sc+=10
    if sc==30: return "PERFECT",25
    elif sc>=20: return "STRONG",15
    elif sc>=10: return "WEAK",5
    return "NONE",0

def mom_check(h4, h1, m15, d):
    sc = 0
    if d=="BULLISH":
        if h4['MACD'].iloc[-1]>0: sc+=1
        if h1['MACD'].iloc[-1]>0: sc+=1
        if m15['MACD'].iloc[-1]>0: sc+=1
    else:
        if h4['MACD'].iloc[-1]<0: sc+=1
        if h1['MACD'].iloc[-1]<0: sc+=1
        if m15['MACD'].iloc[-1]<0: sc+=1
    return sc

def storm_check(sd):
    met, lst = 0, []
    checks = [
        (sd.get('adx',0)>30,"ADX>30"), (sd.get('mom',0)==3,"Mom3/3"),
        (sd.get('pat',0)>=8,"Patterns"), (sd.get('div'),"Divergence"),
        (sd.get('fib'),"Fib"), (sd.get('sr'),"S/R"),
        (sd.get('align'),"Alignment"), (sd.get('bb'),"BB Squeeze"),
        (sd.get('trend'),"Trending"), (sd.get('vol'),"Volume"),
        (sd.get('hurst'),"Hurst"), (sd.get('zscore'),"Z-Score"),
        (sd.get('gen'),"Generator"), (sd.get('dist'),"Distribution"),
        (sd.get('vr_edge'),"VR Edge"), (sd.get('acf_edge'),"ACF Edge"),
    ]
    for c, l in checks:
        if c: met+=1; lst.append(l)
    if met>=10: return "PERFECT_STORM",25,lst
    elif met>=8: return "STRONG",20,lst
    elif met>=6: return "GOOD",15,lst
    elif met>=4: return "MODERATE",10,lst
    return None,0,lst

# ==============================================================================
# CHART V20
# ==============================================================================

def plot_chart(df, title, entry=None, sl=None, tp1=None, tp2=None, sr_levels=None, fib_levels=None):
    fig,(ax1,ax2) = plt.subplots(2,1,figsize=(14,9),height_ratios=[3,1],facecolor='#0a0a0a')
    ax1.set_facecolor('#0a0a0a'); ax2.set_facecolor('#0a0a0a')
    for i in range(len(df)):
        c='#10b981' if df['close'].iloc[i]>=df['open'].iloc[i] else '#ef4444'
        ax1.plot([df.index[i]]*2,[df['low'].iloc[i],df['high'].iloc[i]],color=c,lw=0.8)
        ax1.plot([df.index[i]]*2,[df['open'].iloc[i],df['close'].iloc[i]],color=c,lw=3.5)
    ax1.plot(df.index,df['EMA_20'],color='cyan',ls='--',alpha=0.5,lw=1,label='E20')
    ax1.plot(df.index,df['EMA_50'],color='orange',ls='--',alpha=0.5,lw=1,label='E50')
    ax1.plot(df.index,df['EMA_200'],color='purple',alpha=0.4,lw=1.5,label='E200')
    ax1.fill_between(df.index,df['BB_upper'],df['BB_lower'],alpha=0.04,color='white')
    if sr_levels:
        for s in sr_levels[:4]:
            cl='#ef4444' if s['type']=='RESISTANCE' else '#10b981'
            ax1.axhspan(s['zone_low'],s['zone_high'],alpha=0.08,color=cl)
    if fib_levels:
        for n,p in fib_levels.items():
            if pd.notna(p): ax1.axhline(y=p,color='#fbbf24',ls='-.',alpha=0.2,lw=0.7)
    if entry: ax1.axhline(y=entry,color='cyan',lw=2,label='Entry')
    if sl: ax1.axhline(y=sl,color='#ef4444',lw=2,label='SL')
    if tp1: ax1.axhline(y=tp1,color='#10b981',ls='--',lw=1.5,label='TP1')
    if tp2: ax1.axhline(y=tp2,color='#059669',lw=2,label='TP2')
    ax1.set_title(title,fontsize=13,fontweight='bold',color='#fbbf24')
    ax1.legend(loc='upper left',fontsize=7,facecolor='#111',edgecolor='#333',labelcolor='white')
    ax1.grid(True,alpha=0.1,color='#333'); ax1.tick_params(colors='#666')
    colors=['#10b981' if x>0 else '#ef4444' for x in df['MACD_hist']]
    ax2.bar(df.index,df['MACD_hist'],color=colors,alpha=0.5,width=0.8)
    ax2.plot(df.index,df['MACD'],color='#3b82f6',lw=1)
    ax2.plot(df.index,df['MACD_signal'],color='#ef4444',lw=1)
    ax2.axhline(y=0,color='#333',lw=0.5)
    ax2.set_title('MACD',fontsize=10,color='#fbbf24')
    ax2.grid(True,alpha=0.1,color='#333'); ax2.tick_params(colors='#666')
    plt.xticks(rotation=45); plt.tight_layout()
    buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=120,facecolor='#0a0a0a',bbox_inches='tight')
    plt.close(fig); buf.seek(0); return Image.open(buf)

def cnp(obj):
    if isinstance(obj,dict): return {k:cnp(v) for k,v in obj.items()}
    elif isinstance(obj,list): return [cnp(i) for i in obj]
    elif isinstance(obj,np.integer): return int(obj)
    elif isinstance(obj,np.floating): return float(obj)
    elif isinstance(obj,np.ndarray): return obj.tolist()
    elif isinstance(obj,np.bool_): return bool(obj)
    elif isinstance(obj,float) and pd.isna(obj): return None
    return obj

# ==============================================================================
# PROMPT V20
# ==============================================================================

PROMPT_V20 = """
FUNÇÃO: ANALISTA V20.0 — STATISTICAL EDGE ENGINE [Gemini 3 Pro]
**RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO**

**CORREÇÕES V20 (vs V19):**
- Sigma calibrado dos dados reais (não assumido)
- VOL_COMPRESS indica direção CONTRA o move recente
- Crash/Boom drift via regressão linear + spike decay model
- Backtest testa TODOS os tipos de setup
- Monte Carlo com bootstrap real
- Variance Ratio Test + Autocorrelação

**NOVAS ARMAS V20:**
- 🔬 Variance Ratio: VR≠1 → edge real (não random walk)
- 📈 Autocorrelação: lag1<0 → mean reversion, lag1>0 → momentum
- 📊 Vol Clustering: detecta GARCH effect
- 🎯 Preço Teórico GBM: z_price = desvio do esperado
- 💥 Spike Decay: fase do ciclo entre spikes (Crash/Boom)
- ✅ Trigger Candle: confirmação de entrada
- 🧠 Kelly Criterion adaptativo

**FORMATO:**
## 🔬 VEREDICTO V20: [{DECISION}]
**Grade:** {GRADE} | **Score:** {SCORE}/170

### 🔬 STATISTICAL EDGES
- **Variance Ratio:** {VR summary} → {edge type}
- **Autocorrelação:** lag1={acf} → {type}
- **Vol Clustering:** {signal}
- **Preço vs Teórico:** z={z_price} → {direction}

### 🧮 MODELO DO GERADOR
{Generator analysis com dados corrigidos}

### 📊 PLANO COM PIRÂMIDE
{Tabela de entradas piramidadas}

### 🎯 TARGETS INTELIGENTES
{Calibrados por S/R + regime + distribuição}

*Insight V20:* {Baseado em evidência estatística, explique o edge
com probabilidades concretas. Foque no que o Variance Ratio e
Autocorrelação revelam sobre este ativo agora.}
"""

# ==============================================================================
# SNIPER CORE V20.0 — STATISTICAL EDGE ENGINE
# ==============================================================================

def sniper_v20(name, h1_raw, h4_raw, m15_raw, capital=10000, risk_pct=1.0):
    profile = get_profile(name)
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = detect_patterns(indicators(prep_df(m15_raw)))
    c1, c4, cm = h1.iloc[-1], h4.iloc[-1], m15.iloc[-1]

    bias = "BULLISH" if c4['close'] > c4['EMA_200'] else "BEARISH"
    adx = c4['ADX']
    struct = market_structure(h1)
    regime, regime_sc = classify_regime(h1)
    mom = mom_check(h4, h1, m15, bias)

    # ═══ CALIBRATE SIGMA (MATH FIX #1) ═══
    ppy = detect_periods_per_year(h1)
    sigma_cal = calibrate_sigma(h1, ppy)

    # ═══ STATISTICAL EDGES (NEW V20) ═══
    vr_results, vr_summary = variance_ratio_test(h1['close'])
    vr_bonus = 0; vr_edge = False
    if vr_summary in ["MEAN_REVERTING", "MOMENTUM"]:
        vr_bonus = 10; vr_edge = True
    elif vr_summary == "MIXED":
        vr_bonus = 5; vr_edge = True

    acf_results, acf_summary = autocorrelation_analysis(h1['close'])
    acf_bonus = 0; acf_edge = False
    if "MEAN_REVERT" in acf_summary:
        acf_bonus = 8; acf_edge = True
    elif "MOMENTUM" in acf_summary:
        acf_bonus = 8; acf_edge = True

    vol_cluster = volatility_clustering_test(h1['close'])
    price_dev = theoretical_price_deviation(h1, sigma_cal, ppy)

    # ═══ GENERATOR MODEL (ALL BUGS FIXED) ═══
    gen_type = profile.get('gen_type', 'GBM')
    gen = {}; gen_signal = "NEUTRAL"; gen_bonus = 0

    if gen_type == "GBM":
        gen = GeneratorModelV20.analyze_gbm(h1, profile, sigma_cal, ppy)
        gen_signal = gen['signal']
        if gen_signal == "VOL_COMPRESS" and gen['confidence'] > 30:
            gen_bonus = min(int(gen['confidence'] / 8), 12)
        elif gen_signal == "VOL_EXPAND" and gen['confidence'] > 30:
            gen_bonus = min(int(gen['confidence'] / 10), 8)
    elif gen_type in ["BOOM", "CRASH"]:
        gen = GeneratorModelV20.analyze_crash_boom(h1, profile, ppy)
        gen_signal = gen['signal']
        if "DRIFT" in gen_signal and "STRONG" in gen_signal: gen_bonus = 12
        elif "DRIFT" in gen_signal: gen_bonus = 8
        elif gen_signal == "SPIKE_DANGER": gen_bonus = -5
    elif gen_type == "STEP":
        gen = GeneratorModelV20.analyze_step(h1, profile, ppy)
        gen_signal = gen['signal']
        if gen_signal == "EXTREME_DEVIATION": gen_bonus = 10
        elif gen_signal == "HIGH_DEVIATION": gen_bonus = 7
        elif gen_signal == "MEAN_REVERT_PATTERN": gen_bonus = 6

    # ═══ DISTRIBUTION ═══
    dist = DistributionAnalyzerV20.analyze(h1)
    dist_bonus = 0; dist_fav = False
    if dist['tail_risk'] in ["FAT_TAILS","HEAVY_TAILS"]: dist_bonus += 3
    if dist['percentile'] < 10 and bias == "BULLISH": dist_bonus += 7; dist_fav = True
    elif dist['percentile'] > 90 and bias == "BEARISH": dist_bonus += 7; dist_fav = True

    # ═══ V18 STATS ═══
    hurst_val, hurst_reg, hurst_r2 = calc_hurst(h1['close'])
    hurst_bonus = 0; hurst_trending = False
    if hurst_reg != "UNRELIABLE":
        if hurst_val > profile['hurst_trend_min']: hurst_bonus = 10; hurst_trending = True
        elif hurst_val < 0.45: hurst_bonus = 5

    z_cur = cm['ZSCORE'] if pd.notna(cm.get('ZSCORE',np.nan)) else 0
    zscore_bonus = 0; zscore_fav = False
    if bias=="BULLISH" and z_cur < -profile['zscore_extreme']*0.6: zscore_bonus=10; zscore_fav=True
    elif bias=="BEARISH" and z_cur > profile['zscore_extreme']*0.6: zscore_bonus=10; zscore_fav=True

    bb_cyc, bb_rat, bb_sq = detect_bb_cycle(h1, profile)
    consec_n, consec_d = count_consecutive(m15)
    consec_bonus = 0; consec_risk = consec_n >= profile['consecutive_reversal']
    if consec_risk and ((bias=="BULLISH" and consec_d=="BEAR") or (bias=="BEARISH" and consec_d=="BULL")):
        consec_bonus = 10
    roc_st, roc_det = detect_roc(m15, profile)

    rsi_div, rsi_db, rsi_dd = detect_divergence(m15, 'RSI', 4)
    macd_div, macd_db, macd_dd = detect_divergence(m15, 'MACD', 4)
    divergence = rsi_div or macd_div
    div_bonus = max(rsi_db, macd_db); div_detail = rsi_dd or macd_dd

    sr_levels = detect_sr(h1)
    sr_bonus = 0; sr_touch = False; closest_sr = None
    if sr_levels:
        closest_sr = min(sr_levels, key=lambda x: abs(x['price'] - c1['close']))
        if abs(closest_sr['price'] - c1['close']) < c1['ATR'] * 0.5:
            sr_bonus = min(closest_sr['strength'] * 3, 15); sr_touch = True
    fibs, fib_dir, _ = calc_fib(h1)
    fib_level, fib_bonus = check_fib(c1['close'], fibs, c1['ATR'])

    align_type, align_bonus = alignment_check(c4, c1, cm, bias)
    vol_st, vol_proxy = tick_volume(m15)
    vol_confirmed = vol_proxy > 1.3; vol_bonus = 5 if vol_confirmed else 0
    regime_bonus = 5 if "TRENDING" in regime else 0
    pat_score = min(cm.get('pattern_score', 0), 15)

    # ═══ BACKTEST + ADAPTIVE (single run, FIX #5) ═══
    sim = walk_forward_v20(h1, bias, profile, sigma_cal, ppy, n_folds=4)
    adapted = AdaptiveLearnerV20.adjust_profile(profile, sim, dist)

    # ═══ MONTE CARLO BOOTSTRAP (FIX #6) ═══
    mc = monte_carlo_bootstrap(sim.get('RESULTS', []))

    # ═══ 🟡 EDGE #7: REGIME-SPECIFIC STRATEGY ═══
    # Determine best strategy for current regime + statistical edges
    mp_price, mp_type = micro_pullback(m15, bias, c1['ATR'])
    trig_ok, trig_type = trigger_confirmed(m15, bias)

    sig = "MONITORING"; entry = c1['close']; sl_val = c1['close']
    entry_type = "Wait"; sl_reason = "Structural"; trade_style = None; setup_type = None

    vc = profile['vol_class']
    if vc == "EXTREME" and roc_st == "EXTREME":
        sig = "BLOCKED (ROC EXTREMO)"
    elif gen_signal == "SPIKE_DANGER":
        sig = "BLOCKED (SPIKE ZONE — risco de spike iminente)"
    else:
        def try_setup(direction):
            nonlocal sig, sl_val, entry_type, trade_style, setup_type, entry
            is_long = direction == "BULLISH"
            opp_div = "BEARISH" if is_long else "BULLISH"

            if divergence and opp_div in str(divergence) and "HIDDEN" not in str(divergence):
                sig = f"BLOCKED ({opp_div}_DIV: {div_detail})"; return

            # === PRIORITY 1: Generator Edge ===
            if gen_type == "GBM" and gen_signal == "VOL_COMPRESS" and gen.get('confidence',0) > 40:
                cd = gen.get('compress_direction', 'NEUTRAL')
                if (is_long and cd == "BULLISH") or (not is_long and cd == "BEARISH"):
                    sig = f"{'LONG' if is_long else 'SHORT'} (VOL COMPRESS)"
                    sl_val = c1['close'] + (-1 if is_long else 1) * adapted['sl_atr_mult'] * c1['ATR']
                    entry_type = f"GBM Compress → {cd} (ratio={gen['vol_ratio_primary']:.2f})"
                    trade_style = "REVERSAL"; setup_type = "GEN_VOL_COMPRESS"; return

            # 🔴 FIX #3: Crash/Boom drift segue cálculo
            if gen_type in ["BOOM","CRASH"] and "DRIFT" in gen_signal:
                dd = gen.get('drift_direction','UNKNOWN')
                if (is_long and dd == "UP") or (not is_long and dd == "DOWN"):
                    phase = gen.get('decay_phase','')
                    sig = f"{'LONG' if is_long else 'SHORT'} (DRIFT {dd} — {phase})"
                    sl_val = c1['close'] + (-1 if is_long else 1) * adapted['sl_atr_mult'] * c1['ATR']
                    entry_type = f"Drift {dd} slope={gen.get('drift_slope',0):.1f} ({gen.get('last_spike_bars',0)} bars since spike)"
                    trade_style = "DAY"; setup_type = "GEN_DRIFT"; return

            if gen_type == "STEP" and gen_signal in ["EXTREME_DEVIATION","HIGH_DEVIATION"]:
                dev = gen.get('deviation_sigma',0)
                if (is_long and dev < -1.5) or (not is_long and dev > 1.5):
                    sig = f"{'LONG' if is_long else 'SHORT'} (STEP DEV {dev:.1f}σ)"
                    sl_val = c1['close'] + (-1 if is_long else 1) * adapted['sl_atr_mult'] * c1['ATR']
                    entry_type = f"Step deviation: {dev:.1f}σ"; trade_style = "REVERSAL"; setup_type = "GEN_STEP"; return

            # === PRIORITY 2: Statistical Edge ===
            if vr_summary == "MEAN_REVERTING" and abs(z_cur) > profile['zscore_extreme'] * 0.5:
                if (is_long and z_cur < 0) or (not is_long and z_cur > 0):
                    sig = f"{'LONG' if is_long else 'SHORT'} (STAT MEAN REVERT)"
                    sl_val = c1['close'] + (-1 if is_long else 1) * adapted['sl_atr_mult'] * c1['ATR']
                    entry_type = f"VR=MR + Z={z_cur:.1f}"; trade_style = "REVERSAL"; setup_type = "STAT_MEAN_REVERT"; return

            if price_dev['direction'] in ["OVERSOLD","OVERBOUGHT"]:
                if (is_long and price_dev['direction'] == "OVERSOLD") or (not is_long and price_dev['direction'] == "OVERBOUGHT"):
                    sig = f"{'LONG' if is_long else 'SHORT'} (PRICE DEVIATION z={price_dev['z_price']:.1f})"
                    sl_val = c1['close'] + (-1 if is_long else 1) * adapted['sl_atr_mult'] * c1['ATR']
                    entry_type = f"GBM price dev z={price_dev['z_price']:.1f}"; trade_style = "REVERSAL"; setup_type = "PRICE_DEV"; return

            # === PRIORITY 3: Classic Setups ===
            if adx > adapted['adx_strong'] and (abs(c1['close']-c1['EMA_50'])<c1['ATR']*1.5 or
                    (c1['RSI']<45 if is_long else c1['RSI']>55)):
                if "RANGING" in regime and not hurst_trending and not vr_edge:
                    sig = "BLOCKED (RANGING + NO EDGE)"; return
                sig = f"{'LONG' if is_long else 'SHORT'} (SWING)"
                sl_val = detect_swing_sl(h1, "BUY" if is_long else "SELL", adapted['sl_atr_mult'])
                entry_type = f"Swing — {mp_type} — {trig_type}"; trade_style = "SWING"; setup_type = "SWING"
                if mp_price and mp_type != "MARKET": entry = mp_price

            elif adx > adapted['adx_trend_min'] and ((c1['close'] > c1['EMA_20']) if is_long else (c1['close'] < c1['EMA_20'])):
                sig = f"{'LONG' if is_long else 'SHORT'} (DAY)"
                sl_val = detect_swing_sl(h1, "BUY" if is_long else "SELL", adapted['sl_atr_mult']*0.8)
                entry_type = f"Day — {mp_type}"; trade_style = "DAY"; setup_type = "DAY"
                if mp_price and mp_type != "MARKET": entry = mp_price

            elif sr_touch and closest_sr:
                from_sr = c1['close'] > closest_sr['price'] if is_long else c1['close'] < closest_sr['price']
                if from_sr:
                    rng_h1 = h1['high']-h1['low']; rng_ratio = rng_h1.iloc[-1]/rng_h1.iloc[-20:-1].mean() if rng_h1.iloc[-20:-1].mean()>0 else 1
                    if rng_ratio > 1.3:
                        sig = f"{'LONG' if is_long else 'SHORT'} (BREAKOUT)"
                        sl_val = closest_sr['price'] + (-1 if is_long else 1) * c1['ATR']
                        entry_type = f"Breakout S/R ×{rng_ratio:.1f}"; trade_style = "BREAKOUT"; setup_type = "BREAKOUT"

            elif z_cur and ((z_cur < -profile['zscore_extreme']*0.6 and is_long) or (z_cur > profile['zscore_extreme']*0.6 and not is_long)):
                if hurst_val < 0.48:
                    sig = f"{'LONG' if is_long else 'SHORT'} (MEAN REVERSION)"
                    sl_val = c1['close'] + (-1 if is_long else 1) * adapted['sl_atr_mult'] * c1['ATR']
                    entry_type = f"MR Z={z_cur:.1f}"; trade_style = "REVERSAL"; setup_type = "MEAN_REVERSION"

            # SL cap
            if "LONG" in sig or "SHORT" in sig:
                max_sl = adapted['sl_atr_mult'] * c1['ATR']
                if is_long and (entry - sl_val) > max_sl:
                    sl_val = entry - max_sl; sl_reason = f"Max {adapted['sl_atr_mult']:.1f}× ATR"
                elif not is_long and (sl_val - entry) > max_sl:
                    sl_val = entry + max_sl; sl_reason = f"Max {adapted['sl_atr_mult']:.1f}× ATR"

        try_setup(bias)

    # Spread
    if "LONG" in sig: entry += profile['spread']
    elif "SHORT" in sig: entry -= profile['spread']

    # Storm
    storm_data = {'adx':adx, 'mom':mom, 'pat':pat_score, 'div':divergence,
        'fib':fib_level, 'sr':sr_touch, 'align':align_type=="PERFECT",
        'bb':bb_cyc=="SQUEEZE", 'trend':"TRENDING" in regime, 'vol':vol_confirmed,
        'hurst':hurst_trending, 'zscore':zscore_fav, 'gen':gen_bonus>0,
        'dist':dist_fav, 'vr_edge':vr_edge, 'acf_edge':acf_edge}
    storm_lev, storm_bonus_v, storm_crit = storm_check(storm_data)
    if storm_lev == "PERFECT_STORM" and "BLOCKED" not in sig and sig != "MONITORING":
        sig = sig.replace("LONG","LONG ⭐STORM⭐").replace("SHORT","SHORT ⭐STORM⭐")
        setup_type = "PERFECT_STORM"

    final_db = 0
    if divergence:
        if ("LONG" in sig and "BULL" in str(divergence)) or ("SHORT" in sig and "BEAR" in str(divergence)):
            final_db = abs(div_bonus)

    score = calc_score(adx, mom, pat_score, abs(c1['close']-c1['EMA_50']), c1['ATR'],
        sim['WR'], sim['PF'], adapted,
        div_b=final_db, fib_b=fib_bonus, sr_b=sr_bonus, align_b=align_bonus,
        storm_b=storm_bonus_v, regime_b=regime_bonus, vol_b=vol_bonus,
        hurst_b=hurst_bonus, zscore_b=zscore_bonus, consec_b=consec_bonus,
        gen_b=max(gen_bonus,0), dist_b=dist_bonus, vr_b=vr_bonus, acf_b=acf_bonus)

    # Filters
    cfgs = {"PERFECT_STORM":(100,1.5),"BREAKOUT":(60,1.4),"MEAN_REVERSION":(50,1.2),
            "STAT_MEAN_REVERT":(40,1.0),"GEN_VOL_COMPRESS":(40,1.0),"GEN_DRIFT":(35,0.8),
            "GEN_STEP":(40,1.0),"PRICE_DEV":(40,1.0),"DAY":(45,1.3),"SWING":(70,1.4)}
    gen_types = ["GEN_VOL_COMPRESS","GEN_DRIFT","GEN_STEP","STAT_MEAN_REVERT","PRICE_DEV"]
    ms, mpf = cfgs.get(setup_type, (70, 1.4))
    if "BLOCKED" not in sig and sig != "MONITORING":
        fails = []
        if score.total < ms: fails.append(f"SCORE={score.total:.0f}<{ms}")
        if sim['NET'] <= 0 and setup_type not in gen_types: fails.append("NET≤0")
        if sim['PF'] < mpf and setup_type not in gen_types: fails.append(f"PF={sim['PF']}<{mpf}")
        if fails: sig = f"BLOCKED ({', '.join(fails)})"

    # 🟢 PREC #3: Dynamic TP with S/R awareness
    risk = abs(entry - sl_val)
    if risk == 0: risk = c1['ATR']
    tc = {"PERFECT_STORM":(5,10,30,70),"BREAKOUT":(adapted['tp1_r'],adapted['tp2_r']+2,50,50),
          "MEAN_REVERSION":(2,3,60,40),"STAT_MEAN_REVERT":(2.5,4,50,50),
          "GEN_VOL_COMPRESS":(2.5,4,50,50),"GEN_DRIFT":(2,5,50,50),
          "GEN_STEP":(1.5,2.5,70,30),"PRICE_DEV":(2,3.5,55,45),"DAY":(2,3,60,40)}
    r1,r2,p1,p2 = tc.get(setup_type,(adapted['tp1_r'],adapted['tp2_r'],50,50))
    is_long = "LONG" in sig
    if is_long: tp1=entry+r1*risk; tp2=entry+r2*risk
    elif "SHORT" in sig: tp1=entry-r1*risk; tp2=entry-r2*risk
    else: tp1=tp2=entry

    # S/R awareness for TP
    if sr_levels and ("LONG" in sig or "SHORT" in sig):
        for s in sr_levels:
            if is_long and entry < s['price'] < tp1 and s['strength'] >= 4:
                tp1 = s['price'] - risk * 0.05; break
            elif not is_long and tp1 < s['price'] < entry and s['strength'] >= 4:
                tp1 = s['price'] + risk * 0.05; break

    pyramid = ScalingEngine.calculate_pyramid(score.grade, score.total, capital, risk_pct, entry, sl_val, c1['ATR'], adapted)
    show = any(x in sig for x in ["SWING","DAY","BREAKOUT","STORM","REVERT","COMPRESS","DRIFT","STEP","DEV"])

    imgs = [
        plot_chart(h4.tail(150), f"{name} H4 — {regime} | Gen:{gen_signal}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels if show else None),
        plot_chart(h1.tail(200), f"{name} H1 — H:{hurst_val:.2f} Z:{z_cur:.1f} σr:{gen.get('vol_ratio_primary',1):.2f}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels, fibs if show else None),
        plot_chart(m15.tail(100), f"{name} M15 — BB:{bb_cyc} C:{consec_n} ROC:{roc_st}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None)
    ]

    confs = []
    if vr_edge: confs.append(f"🔬 VR: {vr_summary} (+{vr_bonus})")
    if acf_edge: confs.append(f"📈 ACF: {acf_summary} (+{acf_bonus})")
    if gen_bonus > 0: confs.append(f"🧮 Gen: {gen_signal} (+{gen_bonus})")
    if dist_fav: confs.append(f"📊 Dist: P{dist['percentile']:.0f}")
    if price_dev['direction'] not in ["NEUTRAL"]: confs.append(f"🎯 Price Dev: z={price_dev['z_price']}")
    if divergence: confs.append(f"🔍 {divergence}")
    if fib_level: confs.append(f"📐 Fib {fib_level}")
    if sr_touch and closest_sr: confs.append(f"🎯 S/R {closest_sr['touches']}x")
    if align_type != "NONE": confs.append(f"⭐ {align_type}")
    if storm_lev: confs.append(f"🌟 {storm_lev} ({len(storm_crit)}/16)")
    if hurst_trending: confs.append(f"🧬 Hurst {hurst_val:.2f} (R²={hurst_r2})")
    if zscore_fav: confs.append(f"📊 Z={z_cur:.1f}")
    if trig_ok: confs.append(f"✅ Trigger: {trig_type}")
    if vol_cluster['signal'] != "NO_CLUSTER": confs.append(f"📊 Vol Cluster: {vol_cluster['signal']}")

    risks = []
    if "RANGING" in regime: risks.append("⚠️ RANGING")
    if not sim['WF_STABLE']: risks.append("⚠️ WF instável")
    if mc.get('positive_pct',0)<60: risks.append(f"⚠️ MC {mc['positive_pct']}%")
    if roc_st=="EXTREME": risks.append("⚠️ ROC EXTREMO")
    if hurst_reg=="UNRELIABLE": risks.append(f"⚠️ Hurst unreliable (R²={hurst_r2})")
    if hurst_reg=="RANDOM_WALK": risks.append("⚠️ Random walk")
    if gen_signal=="VOL_EXPAND": risks.append("⚠️ Vol expandindo")
    if vol_cluster['signal']=="HIGH_VOL_CLUSTER": risks.append("⚠️ Vol cluster alto")
    if not trig_ok and show: risks.append("⚠️ Sem trigger candle")

    return cnp({
        "SIG":sig, "STYLE":trade_style or "N/A", "TYPE":setup_type or "N/A",
        "SCORE":score.total, "BASE":score.base, "BONUS":score.bonus, "GRADE":score.grade,
        "PROFILE":vc, "GEN_TYPE":gen_type, "GEN":gen, "GEN_SIG":gen_signal, "GEN_B":max(gen_bonus,0),
        "DIST":dist, "DIST_B":dist_bonus,
        "VR":vr_results, "VR_SUM":vr_summary, "VR_B":vr_bonus,
        "ACF":acf_results, "ACF_SUM":acf_summary, "ACF_B":acf_bonus,
        "VOL_CLUSTER":vol_cluster, "PRICE_DEV":price_dev,
        "SIGMA_CAL":sigma_cal, "SIGMA_REF":profile.get('sigma_annual_ref',0.5),
        "ADX_S":score.trend, "MOM_S":score.momentum, "PAT_S":score.patterns,
        "VAL_S":score.value, "HIST_S":score.historical,
        "DIV_B":score.div_b, "FIB_B":score.fib_b, "SR_B":score.sr_b,
        "ALIGN_B":score.align_b, "STORM_B":score.storm_b, "REG_B":score.regime_b,
        "VOL_B":score.vol_b, "HURST_B":score.hurst_b, "ZS_B":score.zscore_b,
        "CON_B":score.consec_b,
        "HURST":hurst_val, "HURST_R":hurst_reg, "HURST_R2":hurst_r2,
        "ZSCORE":z_cur, "BB_CYC":bb_cyc, "BB_RAT":bb_rat,
        "CONSEC":consec_n, "CONSEC_D":consec_d, "ROC":roc_st,
        "STRUCT":struct, "REGIME":regime, "TVOL":f"{vol_st} ×{vol_proxy:.1f}",
        "DIV":divergence or "None", "DIV_DET":div_detail or "",
        "FIB_LVL":fib_level or "N/A", "SR_N":len(sr_levels), "ALIGN":align_type,
        "STORM":storm_lev or "N/A", "STORM_CRIT":storm_crit,
        "CONFS":confs, "RISKS":risks, "MOM":f"{mom}/3",
        "ENTRY_T":entry_type, "SL_R":sl_reason, "TRIG":trig_type, "SPREAD":profile['spread'],
        "WR":sim['WR'], "NET":sim['NET'], "DD":sim['DD'], "PF":sim['PF'],
        "SHARPE":sim['SHARPE'], "SORTINO":sim['SORTINO'],
        "WF_STABLE":sim['WF_STABLE'], "FOLDS":sim['FOLD_WRS'], "N_TRADES":sim['TOTAL_TRADES'],
        "MC":mc,
        "ENTRY":round(entry,5), "SL":round(sl_val,5), "TP1":round(tp1,5), "TP2":round(tp2,5),
        "PCT1":p1, "PCT2":p2, "PYRAMID":pyramid,
        "ADAPTED_RM":adapted['risk_mult'], "ADAPTED_SL":adapted['sl_atr_mult'],
        "KELLY":adapted.get('kelly_fraction',0),
        "IMGS":imgs, "ATR":c1['ATR'], "RISK":risk,
    })

# ==============================================================================
# 🟢 PREC #4: SCANNER V20 — ALL gen types
# ==============================================================================

async def scan_asset(code, name):
    try:
        h1_raw = await fetch_single(code, 3600, 300)
        if not h1_raw: return None
        df = indicators(prep_df(h1_raw))
        if len(df) < 50: return None
        c = df.iloc[-1]; p = get_profile(name)
        ppy = detect_periods_per_year(df)
        sigma_cal = calibrate_sigma(df, ppy)
        h, _, hr2 = calc_hurst(df['close'])
        z = c['ZSCORE'] if pd.notna(c.get('ZSCORE',np.nan)) else 0
        vr, vr_sum = variance_ratio_test(df['close'], [2,5,10])
        reg, _ = classify_regime(df)

        gt = p.get('gen_type','GBM')
        if gt == 'GBM':
            gen = GeneratorModelV20.analyze_gbm(df, p, sigma_cal, ppy)
        elif gt in ['BOOM','CRASH']:
            gen = GeneratorModelV20.analyze_crash_boom(df, p, ppy)
        elif gt == 'STEP':
            gen = GeneratorModelV20.analyze_step(df, p, ppy)
        else:
            gen = {}

        qs = 0
        if c['ADX'] > p['adx_strong']: qs += 25
        elif c['ADX'] > p['adx_trend_min']: qs += 12
        if abs(z) > p['zscore_extreme'] * 0.6: qs += 15
        if h > p['hurst_trend_min'] or h < 0.45: qs += 10
        if gen.get('signal','NEUTRAL') not in ['NEUTRAL','VOL_NORMAL','NO_DATA']: qs += 20
        if vr_sum in ["MEAN_REVERTING","MOMENTUM"]: qs += 15
        if "TRENDING" in reg: qs += 8
        bias = "BULLISH" if c['close'] > c['EMA_200'] else "BEARISH"

        return {"name":name,"code":code,"score":qs,"bias":bias,
                "adx":round(c['ADX'],1),"hurst":round(h,3),"z":round(z,2),
                "regime":reg,"gen":gen.get('signal','N/A'),"vr":vr_sum,
                "profile":p['vol_class']}
    except:
        return None

# ==============================================================================
# STREAMLIT UI V20
# ==============================================================================

st.sidebar.title("🔬 SI-APATECO V20.0")
st.sidebar.caption("STATISTICAL EDGE ENGINE")
if "GEMINI_API_KEY" in st.secrets:
    api = st.secrets["GEMINI_API_KEY"]; st.sidebar.success("✅ API")
else:
    api = st.sidebar.text_input("GEMINI API KEY", type="password")
st.sidebar.divider()
capital = st.sidebar.number_input("💰 Capital ($)", 100, value=10000, step=100)
risk_pct = st.sidebar.slider("📊 Risco (%)", 0.5, 3.0, 1.0, 0.1)
st.sidebar.divider()
mode = st.sidebar.radio("⚙️", ["🔍 Análise", "🔎 Scanner", "📊 Monitor"])
st.sidebar.divider()
st.sidebar.info("**V20.0** — 6 bugs fixed, 5 math fixed, 8 edges, 6 precision improvements")

st.title("🔬 SI-APATECO V20.0 — STATISTICAL EDGE ENGINE")
st.caption("Variance Ratio | Autocorrelação | Sigma Calibrado | Vol Compress Fix | Bootstrap MC | Spike Decay")

with st.spinner("Assets..."):
    assets = get_assets()
if not assets: st.error("❌ CONN FAIL"); st.stop()

if mode == "🔍 Análise":
    c1c, c2c = st.columns([1,2])
    with c1c:
        target = st.selectbox("🎯 ATIVO", list(assets.keys()))
        pr = get_profile(target)
        st.markdown(f"**{pr['vol_class']}** — `{pr.get('gen_type','?')}`")
        run = st.button("🔬 ANALISAR V20", use_container_width=True)
    with c2c:
        if run:
            if not api: st.error("API KEY"); st.stop()
            status = st.status("🔬 V20 STATISTICAL EDGE...", expanded=True)
            status.write("1️⃣ Data (H1=800, H4=400, M15=2000)...")
            h1r, h4r, m15r, err = asyncio.run(fetch_tri_force(assets[target]))
            if err: status.update(state='error'); st.error(err); st.stop()
            status.write("2️⃣ Calibrating sigma + Statistical tests...")
            status.write("3️⃣ Generator Model + Distribution...")
            status.write("4️⃣ Walk-Forward (all setups) + Bootstrap MC...")
            status.write("5️⃣ Scoring + Pyramid...")
            d = sniper_v20(target, h1r, h4r, m15r, capital, risk_pct)
            imgs = d.pop("IMGS")
            status.write("6️⃣ Gemini 3 Pro...")
            genai.configure(api_key=api)
            try:
                model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
                ai = model.generate_content([PROMPT_V20, f"DATA V20: {json.dumps(d)}"] + imgs).text
                status.update(label="✅ V20 COMPLETE", state="complete")
            except Exception as e:
                ai = f"⚠️ IA: {str(e)[:150]}"; status.update(label="⚠️", state="complete")

            g = d['GRADE']
            gc = {"S":"score-s","A++":"score-a-pp","A+":"score-a-p","A":"score-a","B":"score-b"}.get(g,"score-c")
            st.markdown(f"""<div style='text-align:center;padding:25px;background:rgba(168,85,247,0.08);border:3px solid #a855f7;border-radius:15px;'>
                <h1 style='margin:0;'><span class='{gc}'>{g}</span> — SCORE: {d['SCORE']:.0f}/170</h1>
                <p>Base: {d['BASE']:.0f}/100 | Bonus: +{d['BONUS']:.0f}/70 | Type: {d['TYPE']}</p>
                <p style='color:#a855f7;'>σ calibrado: {d.get('SIGMA_CAL',0):.4f} vs ref: {d.get('SIGMA_REF',0):.4f}</p>
            </div>""", unsafe_allow_html=True)

            st.subheader("🔬 STATISTICAL EDGES (NEW V20)")
            e1,e2,e3,e4 = st.columns(4)
            e1.metric("Variance Ratio", d['VR_SUM'], f"+{d['VR_B']}pts")
            e2.metric("Autocorrelação", d['ACF_SUM'], f"+{d['ACF_B']}pts")
            e3.metric("Vol Cluster", d['VOL_CLUSTER'].get('signal','?'))
            e4.metric("Price Dev", f"z={d['PRICE_DEV']['z_price']}", d['PRICE_DEV']['direction'])
            if d.get('VR'):
                with st.expander("🔬 Variance Ratio Details"):
                    for q, r in d['VR'].items():
                        st.text(f"  q={q}: VR={r['vr']:.4f} z={r['z']:.2f} {'✅ '+r['type'] if r['significant'] else '⬜ random'}")
            if d.get('ACF'):
                with st.expander("📈 Autocorrelation Details"):
                    for lag, r in d['ACF'].items():
                        st.text(f"  lag-{lag}: ACF={r['acf']:.4f} {'✅ '+r['type'] if r['significant'] else '⬜ noise'}")

            st.subheader("🧮 GENERATOR MODEL")
            ga = d.get('GEN', {})
            g1,g2,g3 = st.columns(3)
            g1.metric("Type", d['GEN_TYPE']); g2.metric("Signal", d['GEN_SIG']); g3.metric("Bonus", f"+{d['GEN_B']}")
            if d['GEN_TYPE'] == 'GBM':
                v1,v2,v3,v4 = st.columns(4)
                v1.metric("Vol Ratio", f"{ga.get('vol_ratio_primary',1):.3f}")
                v2.metric("σ realized", f"{ga.get('vol_realized',0):.4f}")
                v3.metric("σ calibrated", f"{ga.get('sigma_calibrated',0):.4f}")
                v4.metric("Compress Dir", ga.get('compress_direction','N/A'))
                if ga.get('multi_window'):
                    st.caption("Multi-window: " + " | ".join([f"w{w['w']}:{w['ratio']:.3f}" for w in ga['multi_window']]))
            elif d['GEN_TYPE'] in ['BOOM','CRASH']:
                b1,b2,b3,b4 = st.columns(4)
                b1.metric("Drift", ga.get('drift_direction','?')); b2.metric("Spikes", ga.get('spikes_found',0))
                b3.metric("Last Spike", f"{ga.get('last_spike_bars',999)} bars"); b4.metric("Phase", ga.get('decay_phase','?'))
            elif d['GEN_TYPE'] == 'STEP':
                s1,s2,s3 = st.columns(3)
                s1.metric("Deviation", f"{ga.get('deviation_sigma',0):.1f}σ")
                s2.metric("Runs", ga.get('runs_test','?')); s3.metric("Vol Ratio", f"{ga.get('vol_ratio',1):.3f}")

            st.subheader("📊 STATS")
            s1,s2,s3,s4,s5 = st.columns(5)
            s1.metric("Hurst", f"{d['HURST']:.3f}", f"{d['HURST_R']} R²={d['HURST_R2']}")
            s2.metric("Z-Score", f"{d['ZSCORE']:.2f}"); s3.metric("BB", d['BB_CYC'])
            s4.metric("Consec", f"{d['CONSEC']}", d['CONSEC_D']); s5.metric("ROC", d['ROC'])

            st.subheader("📊 VALIDATION")
            m1,m2,m3,m4,m5,m6 = st.columns(6)
            m1.metric("WR",f"{d['WR']}%"); m2.metric("PF",f"{d['PF']}"); m3.metric("Sharpe",f"{d['SHARPE']}")
            m4.metric("Sortino",f"{d['SORTINO']}"); m5.metric("DD",f"{d['DD']}R"); m6.metric("Trades",f"{d['N_TRADES']}")
            if d['FOLDS']: st.caption("Folds: "+" | ".join([f"F{i+1}:{w}%" for i,w in enumerate(d['FOLDS'])]))
            mc = d.get('MC',{})
            mc1,mc2,mc3,mc4 = st.columns(4)
            mc1.metric("MC Med",f"{mc.get('median',0)}R"); mc2.metric("MC P5",f"{mc.get('p5',0)}R")
            mc3.metric("MC P95",f"{mc.get('p95',0)}R"); mc4.metric("MC %+",f"{mc.get('positive_pct',0)}%")

            st.subheader("🔬 SCORE BREAKDOWN")
            bc1,bc2 = st.columns(2)
            with bc1:
                st.dataframe(pd.DataFrame([
                    {"Item":"ADX","V":f"{d['ADX_S']}/25"},{"Item":"Momentum","V":f"{d['MOM_S']}/20"},
                    {"Item":"Patterns","V":f"{d['PAT_S']}/15"},{"Item":"Value","V":f"{d['VAL_S']}/15"},
                    {"Item":"Historical","V":f"{d['HIST_S']}/25"},
                ]),hide_index=True,use_container_width=True)
            with bc2:
                st.dataframe(pd.DataFrame([
                    {"Item":"🔬 VR","B":f"+{d['VR_B']}"},{"Item":"📈 ACF","B":f"+{d['ACF_B']}"},
                    {"Item":"🧮 Gen","B":f"+{d['GEN_B']}"},{"Item":"📊 Dist","B":f"+{d['DIST_B']}"},
                    {"Item":"Div","B":f"+{d['DIV_B']}"},{"Item":"Fib","B":f"+{d['FIB_B']}"},
                    {"Item":"S/R","B":f"+{d['SR_B']}"},{"Item":"Align","B":f"+{d['ALIGN_B']}"},
                    {"Item":"Storm","B":f"+{d['STORM_B']}"},{"Item":"Regime","B":f"+{d['REG_B']}"},
                    {"Item":"Volume","B":f"+{d['VOL_B']}"},{"Item":"Hurst","B":f"+{d['HURST_B']}"},
                    {"Item":"Z-Score","B":f"+{d['ZS_B']}"},{"Item":"Consec","B":f"+{d['CON_B']}"},
                ]),hide_index=True,use_container_width=True)

            if d['CONFS']:
                st.subheader("🔥 CONFLUENCES"); [st.markdown(f"- {c}") for c in d['CONFS']]
            if d['RISKS']:
                st.subheader("⚠️ RISKS"); [st.warning(r) for r in d['RISKS']]

            st.divider()
            sig = d['SIG']
            if any(x in sig for x in ["LONG","SHORT"]) and "BLOCKED" not in sig:
                st.success(f"✅ {sig}")
                st.subheader(f"📋 TRADE PLAN — {d['PROFILE']}")
                st.dataframe(pd.DataFrame([
                    {"P":"Entry","V":f"{d['ENTRY']}","N":d['ENTRY_T']},
                    {"P":"SL","V":f"{d['SL']}","N":d['SL_R']},
                    {"P":"TP1","V":f"{d['TP1']}","N":f"Close {d['PCT1']}%"},
                    {"P":"TP2","V":f"{d['TP2']}","N":f"Close {d['PCT2']}% + trail"},
                ]),hide_index=True,use_container_width=True)
                pyr = d.get('PYRAMID',{})
                if pyr.get('n_levels',0)>1:
                    st.subheader("📈 PYRAMID")
                    for i,l in enumerate(pyr.get('levels',[])):
                        st.info(f"**Lvl {i+1}:** {l['entry']} | Risk {l['risk_pct']}% | Size {l['size']} | {l['trigger']}")
                else:
                    l = pyr.get('levels',[{}])[0]
                    st.info(f"**Position:** Size {l.get('size',0)} | Risk {l.get('risk_pct',0)}%")
                st.caption(f"🧠 Kelly: {d.get('KELLY',0):.3f} | Risk ×{d.get('ADAPTED_RM',1):.2f} | SL ×{d.get('ADAPTED_SL',2.5):.2f}")
            elif "BLOCKED" in sig: st.error(f"🛑 {sig}")
            else: st.warning(f"⏸️ {sig}")

            tabs = st.tabs(["H4","H1","M15"])
            with tabs[0]: st.image(imgs[0],use_container_width=True)
            with tabs[1]: st.image(imgs[1],use_container_width=True)
            with tabs[2]: st.image(imgs[2],use_container_width=True)
            st.divider(); st.subheader("🤖 AI ANALYSIS"); st.markdown(ai)

elif mode == "🔎 Scanner":
    st.subheader("🔎 MULTI-ASSET SCANNER V20")
    if st.button("🔎 SCAN ALL", use_container_width=True):
        with st.spinner("Scanning..."):
            async def run_scan():
                return await asyncio.gather(*[scan_asset(c,n) for n,c in assets.items()])
            res = asyncio.run(run_scan())
            valid = sorted([r for r in res if r], key=lambda x:x['score'], reverse=True)
        if valid:
            st.success(f"✅ {len(valid)} scanned")
            for i, r in enumerate(valid[:10]):
                em = "🟢" if r['score']>=50 else "🟡" if r['score']>=25 else "🔴"
                st.markdown(f"""<div class='edge-box'>
                    <strong>{em} #{i+1} {r['name']}</strong> — Score: <strong>{r['score']}</strong> | {r['bias']}<br>
                    <small>ADX:{r['adx']} | H:{r['hurst']} | Z:{r['z']} | {r['regime']} | Gen:{r['gen']} | VR:{r['vr']} | {r['profile']}</small>
                </div>""", unsafe_allow_html=True)

elif mode == "📊 Monitor":
    st.subheader("📊 MONITOR V20")
    ms = st.selectbox("Asset", list(assets.keys()))
    md = st.selectbox("Dir", ["LONG","SHORT"])
    me = st.number_input("Entry",value=1000.0,step=0.1)
    msl = st.number_input("SL",value=990.0,step=0.1)
    mt1 = st.number_input("TP1",value=1030.0,step=0.1)
    mt2 = st.number_input("TP2",value=1050.0,step=0.1)
    if st.button("📊 START", use_container_width=True):
        ir = abs(me-msl); ph = st.empty(); mh = st.empty(); ch = st.empty()
        for _ in range(120):
            try:
                _,_,m15r,err = asyncio.run(fetch_tri_force(assets[ms]))
                if not err and m15r:
                    mdf = indicators(prep_df(m15r))
                    cp = mdf['close'].iloc[-1]
                    cr = ((cp-me) if md=="LONG" else (me-cp))/ir if ir>0 else 0
                    ph.metric("Current R", f"{cr:+.2f}")
                    with mh.container():
                        a,b = st.columns(2)
                        a.metric("Price",f"{cp:.4f}"); b.metric("Z",f"{mdf['ZSCORE'].iloc[-1]:.1f}" if 'ZSCORE' in mdf.columns else "?")
                    with ch.container():
                        st.image(plot_chart(mdf.tail(50),f"{ms} Live",me,msl,mt1,mt2),use_container_width=True)
                time.sleep(5)
            except: break
        st.success("✅ Done")
