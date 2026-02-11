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
import time
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# SI-APATECO V19.0 — GENERATOR CRACKER
# Resolve TODOS os 7 pontos fracos do V18:
#
# ✅ FIX #1: MODELA O GERADOR — GBM para Vol, Poisson para Crash/Boom, Bernoulli para Step
# ✅ FIX #2: SUBSTITUI dependência de indicadores clássicos por MODELOS ESTATÍSTICOS
# ✅ FIX #3: ANÁLISE DE DISTRIBUIÇÃO — skewness, kurtosis, probabilidade do preço atual
# ✅ FIX #4: SPIKE CYCLE DETECTOR — detecta tendência entre spikes no Crash/Boom
# ✅ FIX #5: MAIS DADOS — H1=800, H4=400, M15=2000 candles
# ✅ FIX #6: ADAPTIVE LEARNING — ajusta parâmetros baseado em performance recente
# ✅ FIX #7: MICROESTRUTURA — confirma entrada com análise tick-level do M5/M1 proxy
#
# NOVAS ARMAS V19:
# 🧮 Vol Realizada vs Teórica (edge MATEMÁTICO)
# 📊 Distribuição de Retornos (skewness, kurtosis, P-value)
# 💥 Crash/Boom Trend-Between-Spikes
# 🎲 Step Index Deviation Model
# 📈 Scaling In / Pirâmide
# 🔍 Multi-Asset Scanner
# 🧠 Adaptive Parameter Tuning
# + TUDO do V18 que funciona (Hurst, Z-Score, BB Cycle, etc.)
# ==============================================================================

st.set_page_config(
    page_title="SI-APATECO V19.0 GENERATOR CRACKER",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Teko:wght@300;600&family=Share+Tech+Mono&display=swap');
    .stApp {
        background-color: #050505;
        background-image: linear-gradient(0deg, #000 0%, #0a0a0a 100%);
        color: #d4d4d4; font-family: 'Share Tech Mono', monospace;
    }
    h1, h2, h3 {
        font-family: 'Teko', sans-serif !important;
        text-transform: uppercase; color: #fbbf24;
        letter-spacing: 3px; text-shadow: 0 0 10px rgba(251,191,36,0.3);
    }
    div[data-testid="stMetric"] { background-color: #111; border-right: 4px solid #fbbf24; padding: 15px; }
    .stButton>button {
        background: linear-gradient(45deg, #d97706, #fbbf24);
        color: black; font-weight: 900; text-transform: uppercase;
        padding: 20px; font-size: 20px; border-radius: 0px; width: 100%;
        border: 1px solid #fbbf24; transition: 0.3s;
    }
    .stButton>button:hover { box-shadow: 0 0 30px rgba(251,191,36,0.6); transform: scale(1.02); }
    .score-s { color: #a855f7; font-weight: 900; font-size: 32px; animation: pulse 2s infinite; }
    .score-a-pp { color: #10b981; font-weight: 900; font-size: 30px; }
    .score-a-p { color: #3b82f6; font-weight: 900; font-size: 28px; }
    .score-a { color: #22d3ee; font-weight: 900; font-size: 26px; }
    .score-b { color: #fbbf24; font-weight: 900; font-size: 24px; }
    .score-c { color: #6b7280; font-weight: 900; font-size: 22px; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.7; } }
    .health-exc { background: linear-gradient(90deg,#10b981,#059669); color:white; padding:15px; border-radius:8px; font-weight:bold; }
    .health-good { background: linear-gradient(90deg,#3b82f6,#2563eb); color:white; padding:15px; border-radius:8px; font-weight:bold; }
    .health-warn { background: linear-gradient(90deg,#f59e0b,#d97706); color:white; padding:15px; border-radius:8px; font-weight:bold; }
    .health-danger { background: linear-gradient(90deg,#ef4444,#dc2626); color:white; padding:15px; border-radius:8px; font-weight:bold; animation: blink 1s infinite; }
    @keyframes blink { 0%,50%,100% { opacity:1; } 25%,75% { opacity:0.5; } }
    .gen-model { background: rgba(168,85,247,0.1); border-left: 4px solid #a855f7; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }
    .scanner-card { background: rgba(16,185,129,0.08); border: 1px solid #10b981; padding: 12px; border-radius: 8px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# FIX #1: MODELAGEM DO GERADOR — PERFIS COM PARÂMETROS DO CSPRNG
# ==============================================================================

SYNTHETIC_PROFILES = {
    # ── VOLATILITY INDICES: GBM — P(t) = P(t-1) × exp(σ×Z), Z~N(0,1) ──
    "VOLATILITY 10 INDEX": {
        "gen_type": "GBM", "vol_class": "ULTRA_LOW",
        "sigma_annual": 0.10, "sigma_tick": 0.10 / np.sqrt(252 * 24 * 60),
        "spread": 0.02, "adx_trend_min": 12, "adx_strong": 20,
        "sl_atr_mult": 2.0, "tp1_r": 2.5, "tp2_r": 4.0,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 2.5,
        "hurst_trend_min": 0.55, "consecutive_reversal": 8,
        "roc_extreme_pct": 0.3, "mean_reversion_bias": 0.7,
        "risk_mult": 1.3, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    "VOLATILITY 10 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "ULTRA_LOW",
        "sigma_annual": 0.10, "sigma_tick": 0.10 / np.sqrt(252 * 24 * 3600),
        "spread": 0.02, "adx_trend_min": 12, "adx_strong": 20,
        "sl_atr_mult": 2.0, "tp1_r": 2.5, "tp2_r": 4.0,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 2.5,
        "hurst_trend_min": 0.55, "consecutive_reversal": 8,
        "roc_extreme_pct": 0.3, "mean_reversion_bias": 0.7,
        "risk_mult": 1.3, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    "VOLATILITY 25 INDEX": {
        "gen_type": "GBM", "vol_class": "LOW",
        "sigma_annual": 0.25, "sigma_tick": 0.25 / np.sqrt(252 * 24 * 60),
        "spread": 0.03, "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 2.2, "tp1_r": 2.5, "tp2_r": 4.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 2.3,
        "hurst_trend_min": 0.54, "consecutive_reversal": 7,
        "roc_extreme_pct": 0.5, "mean_reversion_bias": 0.6,
        "risk_mult": 1.2, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    "VOLATILITY 25 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "LOW",
        "sigma_annual": 0.25, "sigma_tick": 0.25 / np.sqrt(252 * 24 * 3600),
        "spread": 0.03, "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 2.2, "tp1_r": 2.5, "tp2_r": 4.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 2.3,
        "hurst_trend_min": 0.54, "consecutive_reversal": 7,
        "roc_extreme_pct": 0.5, "mean_reversion_bias": 0.6,
        "risk_mult": 1.2, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    "VOLATILITY 50 INDEX": {
        "gen_type": "GBM", "vol_class": "MEDIUM",
        "sigma_annual": 0.50, "sigma_tick": 0.50 / np.sqrt(252 * 24 * 60),
        "spread": 0.05, "adx_trend_min": 16, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.53, "consecutive_reversal": 6,
        "roc_extreme_pct": 0.8, "mean_reversion_bias": 0.5,
        "risk_mult": 1.0, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    "VOLATILITY 50 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "MEDIUM",
        "sigma_annual": 0.50, "sigma_tick": 0.50 / np.sqrt(252 * 24 * 3600),
        "spread": 0.05, "adx_trend_min": 16, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.53, "consecutive_reversal": 6,
        "roc_extreme_pct": 0.8, "mean_reversion_bias": 0.5,
        "risk_mult": 1.0, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    "VOLATILITY 75 INDEX": {
        "gen_type": "GBM", "vol_class": "HIGH",
        "sigma_annual": 0.75, "sigma_tick": 0.75 / np.sqrt(252 * 24 * 60),
        "spread": 0.10, "adx_trend_min": 18, "adx_strong": 28,
        "sl_atr_mult": 3.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.65, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 1.2, "mean_reversion_bias": 0.4,
        "risk_mult": 0.7, "vol_revert_threshold": 1.25,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    "VOLATILITY 75 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "HIGH",
        "sigma_annual": 0.75, "sigma_tick": 0.75 / np.sqrt(252 * 24 * 3600),
        "spread": 0.10, "adx_trend_min": 18, "adx_strong": 28,
        "sl_atr_mult": 3.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.65, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 1.2, "mean_reversion_bias": 0.4,
        "risk_mult": 0.7, "vol_revert_threshold": 1.25,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    "VOLATILITY 100 INDEX": {
        "gen_type": "GBM", "vol_class": "EXTREME",
        "sigma_annual": 1.00, "sigma_tick": 1.00 / np.sqrt(252 * 24 * 60),
        "spread": 0.15, "adx_trend_min": 20, "adx_strong": 30,
        "sl_atr_mult": 3.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.7, "zscore_extreme": 1.5,
        "hurst_trend_min": 0.51, "consecutive_reversal": 4,
        "roc_extreme_pct": 1.5, "mean_reversion_bias": 0.35,
        "risk_mult": 0.5, "vol_revert_threshold": 1.2,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    "VOLATILITY 100 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "EXTREME",
        "sigma_annual": 1.00, "sigma_tick": 1.00 / np.sqrt(252 * 24 * 3600),
        "spread": 0.15, "adx_trend_min": 20, "adx_strong": 30,
        "sl_atr_mult": 3.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.7, "zscore_extreme": 1.5,
        "hurst_trend_min": 0.51, "consecutive_reversal": 4,
        "roc_extreme_pct": 1.5, "mean_reversion_bias": 0.35,
        "risk_mult": 0.5, "vol_revert_threshold": 1.2,
        "kurtosis_normal": 3.0, "skew_threshold": 0.5,
    },
    # ── CRASH/BOOM: Random Walk + Poisson Spikes ──
    "BOOM 300 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM",
        "spike_lambda": 1/300, "spike_direction": "UP",
        "drift_direction": "DOWN",  # tendência suave entre spikes é de BAIXA
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.8, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 5.0, "skew_threshold": 1.0,
        "sigma_annual": 0.50, "sigma_tick": 0.50 / np.sqrt(252 * 24 * 60),
    },
    "BOOM 500 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM",
        "spike_lambda": 1/500, "spike_direction": "UP",
        "drift_direction": "DOWN",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.8, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 5.0, "skew_threshold": 1.0,
        "sigma_annual": 0.50, "sigma_tick": 0.50 / np.sqrt(252 * 24 * 60),
    },
    "BOOM 1000 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM",
        "spike_lambda": 1/1000, "spike_direction": "UP",
        "drift_direction": "DOWN",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.9, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 5.0, "skew_threshold": 1.0,
        "sigma_annual": 0.50, "sigma_tick": 0.50 / np.sqrt(252 * 24 * 60),
    },
    "CRASH 300 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH",
        "spike_lambda": 1/300, "spike_direction": "DOWN",
        "drift_direction": "UP",  # tendência suave entre spikes é de ALTA
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.8, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 5.0, "skew_threshold": 1.0,
        "sigma_annual": 0.50, "sigma_tick": 0.50 / np.sqrt(252 * 24 * 60),
    },
    "CRASH 500 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH",
        "spike_lambda": 1/500, "spike_direction": "DOWN",
        "drift_direction": "UP",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.8, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 5.0, "skew_threshold": 1.0,
        "sigma_annual": 0.50, "sigma_tick": 0.50 / np.sqrt(252 * 24 * 60),
    },
    "CRASH 1000 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH",
        "spike_lambda": 1/1000, "spike_direction": "DOWN",
        "drift_direction": "UP",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.9, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 5.0, "skew_threshold": 1.0,
        "sigma_annual": 0.50, "sigma_tick": 0.50 / np.sqrt(252 * 24 * 60),
    },
    # ── STEP INDEX: Bernoulli(0.5) × 0.1 ──
    "STEP INDEX": {
        "gen_type": "STEP", "vol_class": "STEP",
        "step_size": 0.1, "step_prob": 0.5,
        "spread": 0.01, "adx_trend_min": 10, "adx_strong": 18,
        "sl_atr_mult": 1.5, "tp1_r": 2.0, "tp2_r": 3.0,
        "bb_squeeze_threshold": 0.4, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.55, "consecutive_reversal": 10,
        "roc_extreme_pct": 0.2, "mean_reversion_bias": 0.8,
        "risk_mult": 1.5, "vol_revert_threshold": 1.3,
        "kurtosis_normal": 3.0, "skew_threshold": 0.3,
        "sigma_annual": 0.20, "sigma_tick": 0.20 / np.sqrt(252 * 24 * 60),
    },
}

DEFAULT_PROFILE = {
    "gen_type": "GBM", "vol_class": "UNKNOWN",
    "sigma_annual": 0.50, "sigma_tick": 0.50 / np.sqrt(252 * 24 * 60),
    "spread": 0.05, "adx_trend_min": 15, "adx_strong": 25,
    "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
    "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
    "hurst_trend_min": 0.53, "consecutive_reversal": 6,
    "roc_extreme_pct": 1.0, "mean_reversion_bias": 0.5,
    "risk_mult": 1.0, "vol_revert_threshold": 1.3,
    "kurtosis_normal": 3.0, "skew_threshold": 0.5,
}

def get_profile(name: str) -> dict:
    name_upper = name.upper()
    for key, profile in SYNTHETIC_PROFILES.items():
        if key in name_upper:
            return profile
    return DEFAULT_PROFILE

# ==============================================================================
# FIX #1: GENERATOR MODELS — Modela o CSPRNG de cada tipo
# ==============================================================================

class GeneratorModel:
    """Modela o gerador algorítmico dos índices sintéticos"""

    @staticmethod
    def analyze_gbm(df, profile, window=100):
        """
        GBM: P(t) = P(t-1) × exp(σ×Z)
        Compara volatilidade REALIZADA vs TEÓRICA (σ fixo).
        Quando divergem → reversão é matematicamente provável.
        """
        try:
            log_returns = np.log(df['close'] / df['close'].shift(1)).dropna()
            if len(log_returns) < window:
                return {"vol_ratio": 1.0, "vol_realized": 0, "vol_theoretical": 0,
                        "signal": "NEUTRAL", "confidence": 0, "probability": 0.5}

            recent = log_returns.tail(window)

            # Vol realizada (anualizada baseada no timeframe)
            # Para H1: 252 dias × 24 horas = 6048 períodos/ano
            periods_per_year = 252 * 24  # para H1
            vol_realized = recent.std() * np.sqrt(periods_per_year)

            # Vol teórica do perfil
            vol_theoretical = profile['sigma_annual']

            # Ratio
            ratio = vol_realized / vol_theoretical if vol_theoretical > 0 else 1.0

            # Probabilidade: se ratio > threshold → vai comprimir (vender vol)
            threshold = profile['vol_revert_threshold']

            if ratio > threshold:
                signal = "VOL_COMPRESS"  # vol vai cair → reversão à média
                confidence = min((ratio - 1.0) / 0.5, 1.0) * 100
            elif ratio < 1.0 / threshold:
                signal = "VOL_EXPAND"  # vol vai subir → breakout
                confidence = min((1.0 / ratio - 1.0) / 0.5, 1.0) * 100
            else:
                signal = "VOL_NORMAL"
                confidence = 0

            # P-value: probabilidade de observar esta vol dado o modelo
            # Sob GBM, retornos ~ N(0, σ²), chi-squared test
            expected_var = (vol_theoretical / np.sqrt(periods_per_year)) ** 2
            observed_var = recent.var()
            chi2_stat = (window - 1) * observed_var / expected_var if expected_var > 0 else window
            # P-value aproximado via normal (para n grande)
            z_chi = (chi2_stat - (window - 1)) / np.sqrt(2 * (window - 1))
            from scipy.stats import norm
            try:
                p_value = 2 * (1 - norm.cdf(abs(z_chi)))
            except:
                p_value = 0.5

            return {
                "vol_ratio": round(ratio, 3),
                "vol_realized": round(vol_realized, 4),
                "vol_theoretical": round(vol_theoretical, 4),
                "signal": signal,
                "confidence": round(confidence, 1),
                "probability": round(1 - p_value, 3),  # prob de anomalia
                "z_stat": round(z_chi, 2),
            }
        except:
            return {"vol_ratio": 1.0, "vol_realized": 0, "vol_theoretical": 0,
                    "signal": "NEUTRAL", "confidence": 0, "probability": 0.5}

    @staticmethod
    def analyze_crash_boom(df, profile, window=200):
        """
        Crash/Boom: Random walk + Poisson spikes.
        Detecta spikes recentes, mede tendência entre spikes,
        e identifica zona segura para operar a drift.
        """
        try:
            if len(df) < window:
                return {"spikes_found": 0, "drift_direction": "UNKNOWN",
                        "drift_strength": 0, "last_spike_bars": 999,
                        "post_spike_zone": False, "signal": "NEUTRAL"}

            recent = df.tail(window)
            returns = recent['close'].pct_change().dropna()
            atr = recent['ATR'].mean()
            is_boom = profile.get('gen_type') == 'BOOM'

            # Detectar spikes: retornos > 3× std (outliers)
            ret_std = returns.std()
            spike_threshold = ret_std * 3.5

            spike_indices = []
            for i, r in enumerate(returns):
                if is_boom and r > spike_threshold:
                    spike_indices.append(i)
                elif not is_boom and r < -spike_threshold:
                    spike_indices.append(i)

            # Tempo desde último spike
            last_spike_bars = (len(returns) - spike_indices[-1]) if spike_indices else 999

            # Tendência entre spikes (drift)
            # Remover candles de spike e calcular drift
            non_spike_mask = pd.Series(True, index=returns.index)
            for si in spike_indices:
                # Marcar spike e 2 candles adjacentes
                for offset in range(-1, 3):
                    idx = si + offset
                    if 0 <= idx < len(non_spike_mask):
                        non_spike_mask.iloc[idx] = False

            drift_returns = returns[non_spike_mask]
            if len(drift_returns) > 10:
                drift_mean = drift_returns.mean()
                drift_strength = abs(drift_mean) / ret_std if ret_std > 0 else 0
                drift_dir = "UP" if drift_mean > 0 else "DOWN"
            else:
                drift_mean = 0
                drift_strength = 0
                drift_dir = profile.get('drift_direction', 'UNKNOWN')

            # Post-spike zone: 5-15 candles após spike = estabilização
            post_spike_zone = 5 <= last_spike_bars <= 20

            # Sinal
            if post_spike_zone:
                signal = "POST_SPIKE_ENTRY"  # Melhor momento para entrar na drift
            elif last_spike_bars < 5:
                signal = "SPIKE_RECOVERY"  # Ainda absorvendo o spike
            elif drift_strength > 0.3:
                signal = f"DRIFT_{drift_dir}"  # Operar na direção da drift
            else:
                signal = "NEUTRAL"

            return {
                "spikes_found": len(spike_indices),
                "drift_direction": drift_dir,
                "drift_mean": round(drift_mean * 100, 4),
                "drift_strength": round(drift_strength, 3),
                "last_spike_bars": last_spike_bars,
                "post_spike_zone": post_spike_zone,
                "signal": signal,
                "avg_bars_between_spikes": round(window / max(len(spike_indices), 1), 0),
            }
        except:
            return {"spikes_found": 0, "drift_direction": "UNKNOWN",
                    "drift_strength": 0, "last_spike_bars": 999,
                    "post_spike_zone": False, "signal": "NEUTRAL"}

    @staticmethod
    def analyze_step(df, profile, window=200):
        """
        Step Index: Bernoulli(0.5) × 0.1
        Mede desvio da média esperada e runs test.
        """
        try:
            if len(df) < window:
                return {"deviation_sigma": 0, "runs_test": "NORMAL",
                        "expected_std": 0, "actual_std": 0, "signal": "NEUTRAL"}

            recent = df.tail(window)
            step = profile.get('step_size', 0.1)

            # Desvio da média: esperado = 0, std = step × √N
            price_change = recent['close'].iloc[-1] - recent['close'].iloc[0]
            expected_std = step * np.sqrt(window)
            deviation_sigma = price_change / expected_std if expected_std > 0 else 0

            # Runs test: sequências consecutivas
            directions = (recent['close'].diff().dropna() > 0).astype(int)
            runs = 1
            for i in range(1, len(directions)):
                if directions.iloc[i] != directions.iloc[i-1]:
                    runs += 1

            # Esperado: E(runs) = 2n₁n₂/(n₁+n₂) + 1
            n1 = directions.sum()
            n0 = len(directions) - n1
            if n0 > 0 and n1 > 0:
                expected_runs = (2 * n0 * n1) / (n0 + n1) + 1
                std_runs = np.sqrt(2*n0*n1*(2*n0*n1-n0-n1) / ((n0+n1)**2 * (n0+n1-1)))
                z_runs = (runs - expected_runs) / std_runs if std_runs > 0 else 0
            else:
                z_runs = 0

            if z_runs < -2:
                runs_test = "CLUSTERING"  # Poucas runs = tendência
            elif z_runs > 2:
                runs_test = "ALTERNATING"  # Muitas runs = reversão
            else:
                runs_test = "NORMAL"

            # Sinal
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
                "runs_test": runs_test,
                "runs_z": round(z_runs, 2),
                "expected_std": round(expected_std, 4),
                "price_change": round(price_change, 4),
                "signal": signal,
            }
        except:
            return {"deviation_sigma": 0, "runs_test": "NORMAL",
                    "expected_std": 0, "actual_std": 0, "signal": "NEUTRAL"}

# ==============================================================================
# FIX #3: DISTRIBUIÇÃO DE RETORNOS — Skewness, Kurtosis, Probability
# ==============================================================================

class DistributionAnalyzer:
    """Analisa distribuição dos retornos vs modelo teórico"""

    @staticmethod
    def analyze(df, profile, window=100):
        try:
            log_returns = np.log(df['close'] / df['close'].shift(1)).dropna()
            if len(log_returns) < window:
                return {"skewness": 0, "kurtosis": 3, "jarque_bera": 0,
                        "is_normal": True, "tail_risk": "NORMAL", "signal": "NEUTRAL"}

            recent = log_returns.tail(window)

            # Momentos
            skewness = float(recent.skew())
            kurtosis = float(recent.kurtosis()) + 3  # pandas retorna excess kurtosis

            # Jarque-Bera test (normalidade)
            jb = (window / 6) * (skewness**2 + (1/4)*(kurtosis - 3)**2)

            # Interpretar
            is_normal = jb < 5.99  # chi2 df=2 at 5%
            skew_thresh = profile.get('skew_threshold', 0.5)

            # Tail risk
            if kurtosis > 5:
                tail_risk = "FAT_TAILS"
            elif kurtosis > 4:
                tail_risk = "HEAVY_TAILS"
            elif kurtosis < 2.5:
                tail_risk = "THIN_TAILS"
            else:
                tail_risk = "NORMAL"

            # Probabilidade do retorno atual dado a distribuição
            current_return = recent.iloc[-1]
            z_return = (current_return - recent.mean()) / recent.std() if recent.std() > 0 else 0

            # Sinal
            signal = "NEUTRAL"
            if abs(skewness) > skew_thresh:
                if skewness > 0:
                    signal = "POSITIVE_SKEW"  # Cauda direita → risco de queda rápida
                else:
                    signal = "NEGATIVE_SKEW"  # Cauda esquerda → risco de alta rápida

            if tail_risk == "FAT_TAILS" and abs(z_return) > 2:
                signal = "EXTREME_TAIL_EVENT"

            # Percentil do retorno recente acumulado (últimos 10 candles)
            recent_cum = recent.tail(10).sum()
            all_windows = [log_returns.iloc[i:i+10].sum()
                          for i in range(0, len(log_returns)-10, 5)]
            if all_windows:
                percentile = sum(1 for w in all_windows if w < recent_cum) / len(all_windows)
            else:
                percentile = 0.5

            return {
                "skewness": round(skewness, 3),
                "kurtosis": round(kurtosis, 3),
                "jarque_bera": round(jb, 2),
                "is_normal": is_normal,
                "tail_risk": tail_risk,
                "z_return": round(z_return, 2),
                "percentile": round(percentile * 100, 1),
                "signal": signal,
            }
        except:
            return {"skewness": 0, "kurtosis": 3, "jarque_bera": 0,
                    "is_normal": True, "tail_risk": "NORMAL", "signal": "NEUTRAL"}

# ==============================================================================
# FIX #6: ADAPTIVE LEARNING — Ajusta parâmetros baseado em performance
# ==============================================================================

class AdaptiveLearner:
    """Aprende com resultados do backtest e ajusta parâmetros"""

    @staticmethod
    def adjust_profile(profile, backtest_results, dist_analysis):
        """Retorna perfil ajustado baseado em dados reais"""
        adjusted = profile.copy()

        if not backtest_results or backtest_results.get('TOTAL_TRADES', 0) < 10:
            return adjusted

        wr = backtest_results.get('WR', 50)
        pf = backtest_results.get('PF', 1.0)
        dd = backtest_results.get('DD', 0)

        # Ajustar risco baseado em performance
        if wr > 65 and pf > 2.0:
            adjusted['risk_mult'] = min(profile['risk_mult'] * 1.2, 2.0)
        elif wr < 40 or pf < 1.0:
            adjusted['risk_mult'] = max(profile['risk_mult'] * 0.6, 0.3)

        # Ajustar SL baseado em drawdown
        if dd > 10:
            adjusted['sl_atr_mult'] = min(profile['sl_atr_mult'] * 1.15, 4.0)
        elif dd < 3 and wr > 55:
            adjusted['sl_atr_mult'] = max(profile['sl_atr_mult'] * 0.9, 1.5)

        # Ajustar targets baseado em distribuição
        kurtosis = dist_analysis.get('kurtosis', 3)
        if kurtosis > 4:  # Fat tails → targets maiores (moves extremos acontecem)
            adjusted['tp2_r'] = min(profile['tp2_r'] * 1.3, 10.0)
        elif kurtosis < 2.5:  # Thin tails → targets menores
            adjusted['tp2_r'] = max(profile['tp2_r'] * 0.8, 3.0)

        return adjusted

# ==============================================================================
# SCALING ENGINE — Pirâmide / Composição de Posição
# ==============================================================================

class ScalingEngine:
    """Calcula entradas piramidadas para setups de alta convicção"""

    @staticmethod
    def calculate_pyramid(grade, score, capital, risk_pct, entry, sl, atr, profile):
        risk_per_unit = abs(entry - sl)
        if risk_per_unit == 0:
            return [{"entry": entry, "risk_pct": risk_pct, "size": 0, "trigger": "BASE"}]

        levels = []

        if grade in ["S"] and score >= 140:
            # PERFECT STORM: 3 níveis
            base_risk = capital * (risk_pct / 100) * 1.5 * profile['risk_mult']
            levels.append({
                "entry": entry, "risk_pct": risk_pct * 1.5,
                "size": round(base_risk / risk_per_unit, 2),
                "trigger": "ENTRADA IMEDIATA (Storm)",
            })
            levels.append({
                "entry": entry + atr * 0.5 if entry > sl else entry - atr * 0.5,
                "risk_pct": risk_pct * 1.0,
                "size": round((capital * risk_pct / 100 * profile['risk_mult']) / risk_per_unit, 2),
                "trigger": "+0.5 ATR a favor → adicionar",
            })
            levels.append({
                "entry": entry + atr * 1.5 if entry > sl else entry - atr * 1.5,
                "risk_pct": risk_pct * 0.5,
                "size": round((capital * risk_pct / 100 * 0.5 * profile['risk_mult']) / risk_per_unit, 2),
                "trigger": "+1.5 ATR a favor → adicionar (SL → BE)",
            })

        elif grade in ["A++", "A+"] and score >= 90:
            # HIGH CONVICTION: 2 níveis
            base_risk = capital * (risk_pct / 100) * profile['risk_mult']
            levels.append({
                "entry": entry, "risk_pct": risk_pct,
                "size": round(base_risk / risk_per_unit, 2),
                "trigger": "ENTRADA BASE",
            })
            levels.append({
                "entry": entry + atr * 0.8 if entry > sl else entry - atr * 0.8,
                "risk_pct": risk_pct * 0.5,
                "size": round((capital * risk_pct / 100 * 0.5 * profile['risk_mult']) / risk_per_unit, 2),
                "trigger": "+0.8 ATR a favor → adicionar (SL → BE)",
            })

        else:
            # STANDARD: 1 nível
            base_risk = capital * (risk_pct / 100) * profile['risk_mult']
            levels.append({
                "entry": entry, "risk_pct": risk_pct,
                "size": round(base_risk / risk_per_unit, 2),
                "trigger": "ENTRADA ÚNICA",
            })

        total_risk = sum(l['risk_pct'] for l in levels)
        total_size = sum(l['size'] for l in levels)

        return {
            "levels": levels,
            "total_risk_pct": round(total_risk, 2),
            "total_size": round(total_size, 2),
            "total_value": round(total_size * entry, 2),
            "n_levels": len(levels),
        }

# ==============================================================================
# DERIV NETWORK — FIX #5: MAIS DADOS
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
    """FIX #5: Mais dados — H1=800, H4=400, M15=2000"""
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

async def fetch_single(code, granularity, count):
    """Fetch data para um timeframe/ativo"""
    req = {"ticks_history": code, "style": "candles", "granularity": granularity, "count": count, "end": "latest"}
    for url in DERIV_SERVERS:
        res = await socket_req(url, req)
        if res and 'candles' in res:
            return res['candles']
    return None

# ==============================================================================
# INDICADORES TÉCNICOS (V18 mantido + melhorias)
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

def calculate_rsi_wilder(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    for i in range(period, len(series)):
        if pd.notna(avg_gain.iloc[i-1]):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1]*(period-1)+gain.iloc[i])/period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1]*(period-1)+loss.iloc[i])/period
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_f = df['close'].ewm(span=fast, adjust=False).mean()
    ema_s = df['close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = ema_f - ema_s
    df['MACD_signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    return df

def calculate_adx(df, window=14):
    df['trh'] = df['high'] - df['low']
    df['trc'] = abs(df['high'] - df['close'].shift())
    df['trl'] = abs(df['low'] - df['close'].shift())
    df['TR'] = df[['trh','trc','trl']].max(axis=1)
    df['+DM'] = np.where((df['high']>df['high'].shift())&(df['low']<=df['low'].shift()),df['high']-df['high'].shift(),0)
    df['-DM'] = np.where((df['low']<df['low'].shift())&(df['high']>=df['high'].shift()),df['low'].shift()-df['low'],0)
    df['+DM'] = np.where(df['+DM']>df['-DM'],df['+DM'],0)
    df['-DM'] = np.where(df['-DM']>df['+DM'],df['-DM'],0)
    df['TR_E'] = df['TR'].ewm(span=window,adjust=False).mean()
    df['+DM_E'] = df['+DM'].ewm(span=window,adjust=False).mean()
    df['-DM_E'] = df['-DM'].ewm(span=window,adjust=False).mean()
    df['+DI'] = (df['+DM_E']/df['TR_E'])*100
    df['-DI'] = (df['-DM_E']/df['TR_E'])*100
    di_sum = (df['+DI']+df['-DI']).replace(0,np.nan)
    df['DX'] = (abs(df['+DI']-df['-DI'])/di_sum)*100
    df['ADX'] = df['DX'].ewm(span=window,adjust=False).mean()
    df.drop(columns=['trh','trc','trl','TR','+DM','-DM','TR_E','+DM_E','-DM_E','DX'],inplace=True)
    return df

def calculate_hurst_exponent(series, max_lag=100):
    try:
        ts = series.dropna().values
        if len(ts) < 50: return 0.5, "RANDOM_WALK"
        lags = range(10, min(max_lag, len(ts)//3))
        rs_values = []
        for lag in lags:
            n_chunks = len(ts)//lag
            if n_chunks < 1: continue
            rs_lag = []
            for i in range(n_chunks):
                chunk = ts[i*lag:(i+1)*lag]
                mean_val = np.mean(chunk)
                dev = chunk - mean_val
                cum = np.cumsum(dev)
                R = np.max(cum) - np.min(cum)
                S = np.std(chunk, ddof=1)
                if S > 0: rs_lag.append(R/S)
            if rs_lag: rs_values.append((np.log(lag), np.log(np.mean(rs_lag))))
        if len(rs_values) < 3: return 0.5, "INSUFFICIENT_DATA"
        x = np.array([v[0] for v in rs_values])
        y = np.array([v[1] for v in rs_values])
        H = np.polyfit(x, y, 1)[0]
        H = max(0.0, min(1.0, H))
        if H > 0.6: regime = "STRONG_TREND"
        elif H > 0.53: regime = "WEAK_TREND"
        elif H > 0.47: regime = "RANDOM_WALK"
        elif H > 0.4: regime = "WEAK_MEAN_REVERT"
        else: regime = "STRONG_MEAN_REVERT"
        return round(H, 3), regime
    except:
        return 0.5, "ERROR"

def calculate_zscore(series, window=50):
    try:
        mean = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        return (series - mean) / std.replace(0, np.nan)
    except:
        return pd.Series(0, index=series.index)

def find_pivot_highs(data, order=5):
    pivots = []
    values = data.values if hasattr(data, 'values') else np.array(data)
    for i in range(order, len(values)-order):
        if np.isnan(values[i]): continue
        if all(values[i]>values[i-j] and values[i]>values[i+j] for j in range(1,order+1)):
            pivots.append(i)
    return np.array(pivots)

def find_pivot_lows(data, order=5):
    pivots = []
    values = data.values if hasattr(data, 'values') else np.array(data)
    for i in range(order, len(values)-order):
        if np.isnan(values[i]): continue
        if all(values[i]<values[i-j] and values[i]<values[i+j] for j in range(1,order+1)):
            pivots.append(i)
    return np.array(pivots)

def detect_divergence_v17(df, indicator='RSI', order=5):
    try:
        if len(df) < (order*2+5) or indicator not in df.columns: return None, 0, ""
        ph = find_pivot_highs(df['high'], order=order)
        pl = find_pivot_lows(df['low'], order=order)
        ih = find_pivot_highs(df[indicator], order=order)
        il = find_pivot_lows(df[indicator], order=order)
        if len(ph)>=2 and len(ih)>=2:
            ph1,ph2=ph[-2],ph[-1]; ih1=ih[np.argmin(np.abs(ih-ph1))]; ih2=ih[np.argmin(np.abs(ih-ph2))]
            if abs(ih1-ph1)<=3 and abs(ih2-ph2)<=3:
                if df['high'].iloc[ph2]>df['high'].iloc[ph1] and df[indicator].iloc[ih2]<df[indicator].iloc[ih1]:
                    pd2=(df['high'].iloc[ph2]-df['high'].iloc[ph1])/df['high'].iloc[ph1]*100
                    id2=(df[indicator].iloc[ih1]-df[indicator].iloc[ih2])/max(df[indicator].iloc[ih1],1)*100
                    if min(pd2+id2,10)>1: return "BEARISH_DIVERGENCE",-int(min((pd2+id2)*3,20)),f"Preço HH vs {indicator} LH"
        if len(pl)>=2 and len(il)>=2:
            pl1,pl2=pl[-2],pl[-1]; il1=il[np.argmin(np.abs(il-pl1))]; il2=il[np.argmin(np.abs(il-pl2))]
            if abs(il1-pl1)<=3 and abs(il2-pl2)<=3:
                if df['low'].iloc[pl2]<df['low'].iloc[pl1] and df[indicator].iloc[il2]>df[indicator].iloc[il1]:
                    pd2=(df['low'].iloc[pl1]-df['low'].iloc[pl2])/df['low'].iloc[pl1]*100
                    id2=(df[indicator].iloc[il2]-df[indicator].iloc[il1])/max(abs(df[indicator].iloc[il1]),1)*100
                    if min(pd2+id2,10)>1: return "BULLISH_DIVERGENCE",int(min((pd2+id2)*3,20)),f"Preço LL vs {indicator} HL"
        if len(pl)>=2 and len(il)>=2:
            pl1,pl2=pl[-2],pl[-1]; il1=il[np.argmin(np.abs(il-pl1))]; il2=il[np.argmin(np.abs(il-pl2))]
            if abs(il1-pl1)<=3 and abs(il2-pl2)<=3:
                if df['low'].iloc[pl2]>df['low'].iloc[pl1] and df[indicator].iloc[il2]<df[indicator].iloc[il1]:
                    return "HIDDEN_BULLISH",15,"Hidden: Preço HL vs ind LL"
        if len(ph)>=2 and len(ih)>=2:
            ph1,ph2=ph[-2],ph[-1]; ih1=ih[np.argmin(np.abs(ih-ph1))]; ih2=ih[np.argmin(np.abs(ih-ph2))]
            if abs(ih1-ph1)<=3 and abs(ih2-ph2)<=3:
                if df['high'].iloc[ph2]<df['high'].iloc[ph1] and df[indicator].iloc[ih2]>df[indicator].iloc[ih1]:
                    return "HIDDEN_BEARISH",-15,"Hidden: Preço LH vs ind HH"
        return None, 0, ""
    except:
        return None, 0, ""

def detect_sr_clustered(df, window=100, min_touches=3):
    try:
        if len(df)<window or 'ATR' not in df.columns: return []
        recent=df.tail(window); atr=recent['ATR'].iloc[-1]
        if pd.isna(atr) or atr==0: return []
        tolerance=atr*0.3
        hp=find_pivot_highs(recent['high'],order=3); lp=find_pivot_lows(recent['low'],order=3)
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
        levels=[{'price':round(np.mean(c),4),'touches':len(c),'spread':round(max(c)-min(c),4),
                'type':'RESISTANCE' if np.mean(c)>cp else 'SUPPORT',
                'strength':len(c)+(1 if max(c)-min(c)<tolerance*0.5 else 0),
                'zone_high':round(max(c),4),'zone_low':round(min(c),4)} for c in clusters]
        levels.sort(key=lambda x:x['strength'],reverse=True)
        return levels[:6]
    except:
        return []

def calculate_fibonacci_from_swings(df, lookback=100):
    try:
        if len(df)<lookback: return {},None,None
        recent=df.tail(lookback)
        hp=find_pivot_highs(recent['high'],order=7); lp=find_pivot_lows(recent['low'],order=7)
        if len(hp)==0 or len(lp)==0: return {},None,None
        sh=recent['high'].iloc[hp[-1]]; sl_v=recent['low'].iloc[lp[-1]]
        if pd.isna(sh) or pd.isna(sl_v) or sh==sl_v: return {},None,None
        diff=sh-sl_v
        if hp[-1]>lp[-1]:
            d="UPTREND"
            fibs={'23.6%':sh-diff*0.236,'38.2%':sh-diff*0.382,'50.0%':sh-diff*0.50,'61.8%':sh-diff*0.618,'78.6%':sh-diff*0.786}
        else:
            d="DOWNTREND"
            fibs={'23.6%':sl_v+diff*0.236,'38.2%':sl_v+diff*0.382,'50.0%':sl_v+diff*0.50,'61.8%':sl_v+diff*0.618,'78.6%':sl_v+diff*0.786}
        return fibs,d,{'high':sh,'low':sl_v}
    except:
        return {},None,None

def check_fib_confluence(price, fibs, atr):
    try:
        if not fibs or pd.isna(price) or pd.isna(atr) or atr==0: return None,0
        tolerance=atr*0.4
        for name,lvl in fibs.items():
            if pd.notna(lvl) and abs(price-lvl)<tolerance:
                return name,(15 if '61.8' in name else 10 if '50.0' in name or '38.2' in name else 5)
        return None,0
    except:
        return None,0

def detect_bb_cycle(df, profile, lookback=30):
    try:
        if len(df)<lookback: return "UNKNOWN",0,0
        recent=df.tail(lookback); bw=recent['BB_width']; avg=bw.mean(); cur=bw.iloc[-1]
        if avg==0: return "UNKNOWN",0,0
        ratio=cur/avg; threshold=profile['bb_squeeze_threshold']
        sc=sum(bw<avg*threshold)
        if ratio<threshold: return "SQUEEZE",ratio,sc
        elif ratio>1.5: return "EXPANSION",ratio,0
        return "NORMAL",ratio,0
    except:
        return "UNKNOWN",0,0

def count_consecutive_candles(df, lookback=20):
    try:
        recent=df.tail(lookback)
        dirs=(recent['close']>recent['open']).astype(int)
        cd=dirs.iloc[-1]; streak=0
        for i in range(len(dirs)-1,-1,-1):
            if dirs.iloc[i]==cd: streak+=1
            else: break
        return streak, "BULLISH" if cd==1 else "BEARISH"
    except:
        return 0, "UNKNOWN"

def detect_roc_extreme(df, profile, periods=[5,10,20]):
    try:
        results={}; threshold=profile['roc_extreme_pct']
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
    except:
        return "NORMAL",{}

def detect_micro_pullback(df, direction, atr):
    try:
        if len(df)<5: return None,"MARKET"
        last_3=df.tail(3); curr=last_3.iloc[-1]; prev=last_3.iloc[-2]
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
    except:
        return None,"MARKET"

def detect_patterns_v18(df):
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
        # Engulfing
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
    df['patterns']=[[]]+patterns; df['pattern_score']=[0]+scores
    return df

def detect_swing_points(df, window=5):
    df['swing_high']=False; df['swing_low']=False
    for i in range(window,len(df)):
        lb=df.iloc[max(0,i-window):i+1]
        if df['high'].iloc[i]==lb['high'].max(): df.iloc[i,df.columns.get_loc('swing_high')]=True
        if df['low'].iloc[i]==lb['low'].min(): df.iloc[i,df.columns.get_loc('swing_low')]=True
    return df

def classify_market_structure(df):
    sh=df[df['swing_high']]['high'].tail(4); sl=df[df['swing_low']]['low'].tail(4)
    if len(sh)<2 or len(sl)<2: return "INSUFFICIENT_DATA"
    hh=sh.iloc[-1]>sh.iloc[-2]; hl=sl.iloc[-1]>sl.iloc[-2]
    ll=sl.iloc[-1]<sl.iloc[-2]; lh=sh.iloc[-1]<sh.iloc[-2]
    if hh and hl: return "UPTREND_STRONG"
    elif ll and lh: return "DOWNTREND_STRONG"
    elif hh or hl: return "UPTREND_WEAK"
    elif ll or lh: return "DOWNTREND_WEAK"
    return "RANGE_BOUND"

def classify_market_regime(df, lookback=50):
    try:
        if len(df)<lookback: return "UNKNOWN",0
        recent=df.tail(lookback); c=recent.iloc[-1]; adx=c['ADX']
        slope=(recent['EMA_50'].iloc[-1]-recent['EMA_50'].iloc[-10])/(c['ATR']*10) if c['ATR']>0 else 0
        bb_ratio=c['BB_width']/recent['BB_width'].mean() if recent['BB_width'].mean()>0 else 1
        score=0
        if adx>30: score+=3
        elif adx>20: score+=2
        elif adx>15: score+=1
        if abs(slope)>0.3: score+=2
        elif abs(slope)>0.15: score+=1
        if bb_ratio>1.3: score+=1
        elif bb_ratio<0.7: score-=1
        if score>=4: return "TRENDING_STRONG",score
        elif score>=2: return "TRENDING_WEAK",score
        elif score<=0: return "RANGING",score
        return "TRANSITIONAL",score
    except:
        return "UNKNOWN",0

def analyze_tick_volume(df, lookback=20):
    try:
        if len(df)<lookback: return "NORMAL",1.0
        recent=df.tail(lookback)
        ranges=recent['high']-recent['low']; bodies=abs(recent['close']-recent['open'])
        rr=ranges.iloc[-1]/ranges.mean() if ranges.mean()>0 else 1
        br=bodies.iloc[-1]/bodies.mean() if bodies.mean()>0 else 1
        proxy=(rr+br)/2
        if proxy>2.0: return "VERY_HIGH",proxy
        elif proxy>1.5: return "HIGH",proxy
        elif proxy>0.7: return "NORMAL",proxy
        return "LOW",proxy
    except:
        return "NORMAL",1.0

def confirm_breakout_volume(df):
    try:
        if len(df)<20: return False,0
        ranges=df['high']-df['low']
        ratio=ranges.iloc[-1]/ranges.iloc[-20:-1].mean() if ranges.iloc[-20:-1].mean()>0 else 1
        return ratio>1.3, ratio
    except:
        return False,0

def indicators(df):
    df['EMA_20']=df['close'].ewm(span=20,adjust=False).mean()
    df['EMA_50']=df['close'].ewm(span=50,adjust=False).mean()
    df['EMA_200']=df['close'].ewm(span=200,adjust=False).mean()
    df['RSI']=calculate_rsi_wilder(df['close'],period=14)
    hl=df['high']-df['low']; hc=(df['high']-df['close'].shift()).abs(); lc=(df['low']-df['close'].shift()).abs()
    df['tr']=pd.concat([hl,hc,lc],axis=1).max(axis=1)
    df['ATR']=df['tr'].ewm(span=14,adjust=False).mean()
    df=calculate_adx(df); df=calculate_macd(df)
    df['BB_middle']=df['close'].rolling(window=20).mean()
    df['BB_std']=df['close'].rolling(window=20).std()
    df['BB_upper']=df['BB_middle']+df['BB_std']*2
    df['BB_lower']=df['BB_middle']-df['BB_std']*2
    df['BB_width']=((df['BB_upper']-df['BB_lower'])/df['BB_middle'].replace(0,np.nan))*100
    df['ZSCORE']=calculate_zscore(df['close'],window=50)
    df=detect_patterns_v18(df); df=detect_swing_points(df)
    df.dropna(inplace=True)
    return df

# ==============================================================================
# ALIGNMENT, STORM, MOMENTUM
# ==============================================================================

def detect_perfect_alignment(h4r, h1r, m15r, d):
    sc=0
    if d=="BULLISH":
        if h4r['close']>h4r['EMA_20']>h4r['EMA_50']>h4r['EMA_200']: sc+=10
        if h1r['close']>h1r['EMA_20']>h1r['EMA_50']>h1r['EMA_200']: sc+=10
        if m15r['close']>m15r['EMA_20']>m15r['EMA_50']>m15r['EMA_200']: sc+=10
    else:
        if h4r['close']<h4r['EMA_20']<h4r['EMA_50']<h4r['EMA_200']: sc+=10
        if h1r['close']<h1r['EMA_20']<h1r['EMA_50']<h1r['EMA_200']: sc+=10
        if m15r['close']<m15r['EMA_20']<m15r['EMA_50']<m15r['EMA_200']: sc+=10
    if sc==30: return "PERFECT_ALIGNMENT",25
    elif sc>=20: return "STRONG_ALIGNMENT",15
    elif sc>=10: return "WEAK_ALIGNMENT",5
    return "NO_ALIGNMENT",0

def check_momentum_alignment(h4, h1, m15, d):
    sc=0
    if d=="BULLISH":
        if h4['MACD'].iloc[-1]>0: sc+=1
        if h1['MACD'].iloc[-1]>0: sc+=1
        if m15['MACD'].iloc[-1]>0: sc+=1
    else:
        if h4['MACD'].iloc[-1]<0: sc+=1
        if h1['MACD'].iloc[-1]<0: sc+=1
        if m15['MACD'].iloc[-1]<0: sc+=1
    return sc

def calculate_perfect_storm_bonus(sd):
    met,lst=0,[]
    checks=[
        (sd.get('adx',0)>30,"ADX>30"),(sd.get('momentum_score',0)==3,"Mom 3/3"),
        (sd.get('pattern_score',0)>=10,"Padrões"),(sd.get('divergence') is not None,"Divergência"),
        (sd.get('fib_confluence'),"Fib"),(sd.get('sr_touch'),"S/R"),
        (sd.get('perfect_alignment'),"Alignment"),(sd.get('bb_compression'),"BB Squeeze"),
        (sd.get('regime_trending'),"Trending"),(sd.get('volume_confirmed'),"Volume"),
        (sd.get('hurst_trending'),"Hurst"),(sd.get('zscore_favorable'),"Z-Score"),
        (sd.get('gen_model_signal'),"Generator Model"),  # V19
        (sd.get('dist_favorable'),"Distribution"),  # V19
    ]
    for c,l in checks:
        if c: met+=1; lst.append(l)
    if met>=9: return "PERFECT_STORM",25,lst
    elif met>=7: return "STRONG_CONFLUENCE",20,lst
    elif met>=5: return "GOOD_CONFLUENCE",15,lst
    elif met>=4: return "MODERATE_CONFLUENCE",10,lst
    return None,0,lst

# ==============================================================================
# WALK-FORWARD + MONTE CARLO
# ==============================================================================

def detect_swing_level(df, direction, atr_mult=1.5):
    if direction=="BUY":
        sw=df[df['swing_low']]['low']
        return (sw.iloc[-1]-df['ATR'].iloc[-1]*atr_mult) if not sw.empty else df['low'].tail(20).min()-df['ATR'].iloc[-1]*atr_mult
    else:
        sw=df[df['swing_high']]['high']
        return (sw.iloc[-1]+df['ATR'].iloc[-1]*atr_mult) if not sw.empty else df['high'].tail(20).max()+df['ATR'].iloc[-1]*atr_mult

def run_walk_forward_backtest(df, trend_dir, profile, n_folds=4):
    spread=profile['spread']; sl_mult=profile['sl_atr_mult']
    fold_size=len(df)//(n_folds+1); all_trades,fold_results=[],[]
    for fold in range(n_folds):
        ts=fold_size*(fold+1); te=fold_size*(fold+2) if fold<n_folds-1 else len(df)
        if ts>=len(df)-80: break
        ft,fw,fb,fr=0,0,0.0,[]
        si=max(200,ts)
        for i in range(si,min(te,len(df)-80)):
            row=df.iloc[i]; sig=None; adx_min=profile['adx_strong']
            if trend_dir=="BULLISH" and row['ADX']>adx_min:
                if row['close']>row['EMA_200'] and (row['low']<=row['EMA_50'] or row['RSI']<45): sig="BUY"
            elif trend_dir=="BEARISH" and row['ADX']>adx_min:
                if row['close']<row['EMA_200'] and (row['high']>=row['EMA_50'] or row['RSI']>55): sig="SELL"
            if not sig: continue
            entry=row['close']+(spread if sig=="BUY" else -spread)
            atr=row['ATR']; sl_c=detect_swing_level(df.iloc[:i+1],sig)
            if sig=="BUY": sl=max(entry-sl_mult*atr,sl_c)
            else: sl=min(entry+sl_mult*atr,sl_c)
            risk=abs(entry-sl)
            if risk==0: risk=atr
            tp1=entry+(profile['tp1_r']*risk) if sig=="BUY" else entry-(profile['tp1_r']*risk)
            tp2=entry+(profile['tp2_r']*risk) if sig=="BUY" else entry-(profile['tp2_r']*risk)
            p1,p2=True,True; r1,r2=0,0; csl=sl; trailing=False
            for f in range(i+1,min(i+80,len(df))):
                nx=df.iloc[f]
                if sig=="BUY":
                    if nx['low']<=csl:
                        if p1: r1=(csl-entry)/risk
                        if p2: r2=(csl-entry)/risk
                        break
                    if p1 and nx['high']>=tp1: r1=profile['tp1_r']-spread/risk; p1=False; csl=entry+spread; trailing=True
                    if trailing and p2:
                        csl=max(csl,nx['high']-2*atr)
                        if nx['high']>=tp2: r2=profile['tp2_r']-spread/risk; p2=False; break
                else:
                    if nx['high']>=csl:
                        if p1: r1=(entry-csl)/risk
                        if p2: r2=(entry-csl)/risk
                        break
                    if p1 and nx['low']<=tp1: r1=profile['tp1_r']-spread/risk; p1=False; csl=entry-spread; trailing=True
                    if trailing and p2:
                        csl=min(csl,nx['low']+2*atr)
                        if nx['low']<=tp2: r2=profile['tp2_r']-spread/risk; p2=False; break
            result=r1*0.5+r2*0.5
            if not(p1 and p2): ft+=1; fb+=result; fr.append(result); all_trades.append({'fold':fold,'result':result})
            if result>0: fw+=1
        if ft>0: fold_results.append({'fold':fold,'trades':ft,'wr':fw/ft*100,'balance':fb})
    if not all_trades:
        return {"WR":0,"NET":0,"DD":0,"PF":0,"SHARPE":0,"SORTINO":0,"RECOVERY":0,
                "MAX_CONS_WIN":0,"MAX_CONS_LOSS":0,"WF_STABLE":False,"FOLD_WRS":[],"TOTAL_TRADES":0}
    results=[t['result'] for t in all_trades]
    wins=[r for r in results if r>0]; losses=[r for r in results if r<=0]
    wr=len(wins)/len(results)*100; net=sum(results)
    gp=sum(wins) if wins else 0; gl=abs(sum(losses)) if losses else 0
    pf=gp/gl if gl>0 else(gp if gp>0 else 0)
    cum=np.cumsum(results); peak=np.maximum.accumulate(cum); dd=(peak-cum).max() if len(cum)>0 else 0
    mcw=mcl=cw=cl=0
    for r in results:
        if r>0: cw+=1; cl=0; mcw=max(mcw,cw)
        else: cl+=1; cw=0; mcl=max(mcl,cl)
    rs=pd.Series(results)
    sharpe=(rs.mean()/rs.std()*np.sqrt(252)) if len(rs)>=2 and rs.std()>0 else 0
    ds=rs[rs<0]; sortino=(rs.mean()/ds.std()*np.sqrt(252)) if len(ds)>=2 and ds.std()>0 else 0
    fwrs=[f['wr'] for f in fold_results]
    return {"WR":round(wr,1),"NET":round(net,1),"DD":round(dd,1),"PF":round(pf,2),
            "SHARPE":round(sharpe,2),"SORTINO":round(sortino,2),"RECOVERY":round(net/dd if dd>0 else 0,2),
            "MAX_CONS_WIN":mcw,"MAX_CONS_LOSS":mcl,
            "WF_STABLE":len(fwrs)>=2 and all(w>30 for w in fwrs),"FOLD_WRS":[round(w,1) for w in fwrs],"TOTAL_TRADES":len(results)}

def monte_carlo_simulation(bt, n_sim=1000, n_trades=50):
    try:
        wr=bt['WR']/100
        if wr==0 or bt['TOTAL_TRADES']<5: return {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":0}
        avg_w=bt.get('PF',2.0); fb=[]
        for _ in range(n_sim):
            b=0
            for _ in range(n_trades):
                b+=np.random.uniform(1.5,min(avg_w*1.5,5)) if np.random.random()<wr else -np.random.uniform(0.5,1.0)
            fb.append(b)
        fb=np.array(fb)
        return {"median":round(np.median(fb),1),"p5":round(np.percentile(fb,5),1),
                "p95":round(np.percentile(fb,95),1),"p25":round(np.percentile(fb,25),1),
                "p75":round(np.percentile(fb,75),1),"positive_pct":round(np.mean(fb>0)*100,1)}
    except:
        return {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":0}

# ==============================================================================
# SCORING V19.0 — Inclui Generator Model + Distribution
# ==============================================================================

@dataclass
class SetupScore:
    trend_strength:float; momentum_align:float; patterns:float
    value_zone:float; historical:float; base_total:float
    divergence_bonus:float; fib_bonus:float; sr_bonus:float
    alignment_bonus:float; storm_bonus:float; regime_bonus:float
    volume_bonus:float; hurst_bonus:float; zscore_bonus:float
    consecutive_bonus:float; generator_bonus:float; distribution_bonus:float
    bonus_total:float; total:float; grade:str

def calculate_setup_score(adx, momentum_score, pattern_score, dist_ema50, atr,
                           win_rate, profit_factor, profile, **bonuses):
    ts=25 if adx>profile['adx_strong'] else(15 if adx>profile['adx_trend_min'] else 0)
    mp=(momentum_score/3)*20
    dr=dist_ema50/atr if atr>0 else 999
    vs=15 if dr<0.5 else(10 if dr<1.0 else(5 if dr<1.5 else 0))
    hs=min((win_rate*0.15)+(profit_factor*5),25)
    base=ts+mp+pattern_score+vs+hs
    bonus_vals=[bonuses.get(k,0) for k in ['divergence_bonus','fib_bonus','sr_bonus',
        'alignment_bonus','storm_bonus','regime_bonus','volume_bonus','hurst_bonus',
        'zscore_bonus','consecutive_bonus','generator_bonus','distribution_bonus']]
    bonus=min(sum(bonus_vals),60)  # V19: max bonus 60 (was 50)
    total=base+bonus
    if total>=150: g="S"
    elif total>=125: g="A++"
    elif total>=95: g="A+"
    elif total>=75: g="A"
    elif total>=55: g="B"
    elif total>=35: g="C"
    else: g="D"
    return SetupScore(ts,mp,pattern_score,vs,hs,base,
        bonuses.get('divergence_bonus',0),bonuses.get('fib_bonus',0),bonuses.get('sr_bonus',0),
        bonuses.get('alignment_bonus',0),bonuses.get('storm_bonus',0),bonuses.get('regime_bonus',0),
        bonuses.get('volume_bonus',0),bonuses.get('hurst_bonus',0),bonuses.get('zscore_bonus',0),
        bonuses.get('consecutive_bonus',0),bonuses.get('generator_bonus',0),bonuses.get('distribution_bonus',0),
        bonus,total,g)

# ==============================================================================
# CHART V19.0
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp1=None, tp2=None, sr_levels=None, fib_levels=None, patterns=None):
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
            ax1.axhline(y=sr['price'],color=c,ls=':',alpha=0.4,lw=0.8)
    if fib_levels:
        for n,p in fib_levels.items():
            if pd.notna(p): ax1.axhline(y=p,color='#fbbf24',ls='-.',alpha=0.25,lw=0.7)
    if entry: ax1.axhline(y=entry,color='cyan',ls='-',label='Entry',lw=2)
    if sl: ax1.axhline(y=sl,color='#ef4444',ls='-',label='SL',lw=2)
    if tp1: ax1.axhline(y=tp1,color='#10b981',ls='--',label='TP1',lw=1.5)
    if tp2: ax1.axhline(y=tp2,color='#059669',ls='-',label='TP2',lw=2)
    if patterns and 'patterns' in df.columns:
        last=df['patterns'].iloc[-1]
        if last: ax1.text(df.index[-1],df['high'].iloc[-1]*1.001," ".join(last),fontsize=7,color='#fbbf24',fontweight='bold')
    ax1.set_title(title,fontsize=14,fontweight='bold',color='#fbbf24')
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
    buf=io.BytesIO()
    plt.savefig(buf,format='png',dpi=120,facecolor='#0a0a0a',bbox_inches='tight')
    plt.close(fig); buf.seek(0)
    return Image.open(buf)

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
# PROMPT V19.0 — GENERATOR CRACKER
# ==============================================================================

SYSTEM_PROMPT = """
FUNÇÃO: ANALISTA V19.0 — GENERATOR CRACKER [Gemini 3 Pro]
Missão: Decifrar os algoritmos dos sintéticos Deriv para lucro máximo

**RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO**

**COMO OS SINTÉTICOS FUNCIONAM (MODELOS DO GERADOR):**
- **Volatility Indices (GBM):** P(t)=P(t-1)×exp(σ×Z), σ FIXO. Quando vol realizada ≠ teórica → reversão garantida.
- **Crash/Boom (Poisson):** Drift suave + spikes aleatórios. Drift é previsível, operar ENTRE spikes.
- **Step (Bernoulli):** 50/50 × 0.1. Desvio > 2σ = reversão altíssima probabilidade.

**ARMAS V19.0:**
- 🧮 Generator Model: Vol Realizada vs Teórica, Chi² test
- 📊 Distribuição: Skewness, Kurtosis, Percentil, Fat Tails
- 💥 Spike Cycle: Drift direction, Post-spike entry, Avg bars between
- 🎲 Step Stats: Deviation sigma, Runs test
- 📈 Scaling/Pirâmide: Multi-level entry para setups A+/S
- 🧠 Adaptive Learning: Parâmetros ajustados por backtest
- + Hurst, Z-Score, BB Cycle, Consecutive, ROC, S/R, Fib, Divergências

**FORMATO:**

## 🧮 VEREDICTO V19.0: [ {DECISION} ]
**Grade:** {GRADE} | **Score:** {SCORE}/160
**Tipo:** {STYLE} | **Perfil:** {PROFILE}

### 🧮 MODELO DO GERADOR
- **Tipo:** {GBM/BOOM/CRASH/STEP}
- **Vol Realizada:** {X}% vs Teórica {Y}% → Ratio {Z} → {SIGNAL}
- **Distribuição:** Skew={S}, Kurt={K}, Tails={TIPO}, Percentil={P}%
- **Spike Cycle:** {se Crash/Boom: drift, último spike, zona}
- **Step Stats:** {se Step: deviation, runs test}

### 📊 ANÁLISE ESTATÍSTICA
- Hurst, Z-Score, BB Cycle, Consecutive, ROC, Regime

### 📈 PLANO COM PIRÂMIDE
| Nível | Entrada | Risco | Trigger |
{Tabela de entradas piramidadas}

### 🎯 TARGETS + STOPS (CALIBRADOS)
{Calibrados pelo perfil + ajuste adaptativo}

### 🔥 CONFLUÊNCIAS + ⚠️ RISCOS
{Tudo}

*Insight V19.0:* {Análise baseada no MODELO DO GERADOR.
Explique como a vol realizada vs teórica, distribuição e spike cycle
influenciam a decisão. Dê probabilidades concretas.}
"""

# ==============================================================================
# SNIPER CORE V19.0 — THE GENERATOR CRACKER
# ==============================================================================

def sniper_core_v19(name, h1_raw, h4_raw, m15_raw, capital=10000, risk_pct=1.0):
    profile = get_profile(name)
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = indicators(prep_df(m15_raw))
    c1, c4, cm = h1.iloc[-1], h4.iloc[-1], m15.iloc[-1]

    bias = "BULLISH" if c4['close'] > c4['EMA_200'] else "BEARISH"
    adx = c4['ADX']
    structure = classify_market_structure(h1)
    regime, regime_sc = classify_market_regime(h1)
    momentum = check_momentum_alignment(h4, h1, m15, bias)

    # ═══ V19.0 FIX #1: GENERATOR MODEL ═══
    gen_type = profile.get('gen_type', 'GBM')
    gen_analysis = {}
    gen_signal = "NEUTRAL"
    gen_bonus = 0

    if gen_type == "GBM":
        gen_analysis = GeneratorModel.analyze_gbm(h1, profile, window=150)
        gen_signal = gen_analysis['signal']
        if gen_signal == "VOL_COMPRESS" and gen_analysis['confidence'] > 30:
            gen_bonus = min(int(gen_analysis['confidence'] / 10), 10)
        elif gen_signal == "VOL_EXPAND" and gen_analysis['confidence'] > 30:
            gen_bonus = min(int(gen_analysis['confidence'] / 10), 10)
    elif gen_type in ["BOOM", "CRASH"]:
        gen_analysis = GeneratorModel.analyze_crash_boom(h1, profile, window=200)
        gen_signal = gen_analysis['signal']
        if gen_signal == "POST_SPIKE_ENTRY": gen_bonus = 10
        elif "DRIFT" in gen_signal: gen_bonus = 8
    elif gen_type == "STEP":
        gen_analysis = GeneratorModel.analyze_step(h1, profile, window=200)
        gen_signal = gen_analysis['signal']
        if gen_signal in ["EXTREME_DEVIATION", "HIGH_DEVIATION"]: gen_bonus = 10
        elif gen_signal == "MEAN_REVERT_PATTERN": gen_bonus = 7

    # ═══ V19.0 FIX #3: DISTRIBUIÇÃO ═══
    dist_analysis = DistributionAnalyzer.analyze(h1, profile, window=150)
    dist_bonus = 0
    dist_favorable = False
    if dist_analysis['tail_risk'] in ["FAT_TAILS", "HEAVY_TAILS"]:
        dist_bonus += 3
    if dist_analysis['percentile'] < 10 and bias == "BULLISH":
        dist_bonus += 7; dist_favorable = True
    elif dist_analysis['percentile'] > 90 and bias == "BEARISH":
        dist_bonus += 7; dist_favorable = True

    # ═══ V18 STATS ═══
    hurst_val, hurst_regime = calculate_hurst_exponent(h1['close'])
    hurst_bonus = 0; hurst_trending = False
    if hurst_val > profile['hurst_trend_min']: hurst_bonus = 10; hurst_trending = True
    elif hurst_val < 0.45: hurst_bonus = 5

    z_current = cm['ZSCORE'] if pd.notna(cm['ZSCORE']) else 0
    zscore_bonus = 0; zscore_favorable = False
    if bias == "BULLISH" and z_current < -profile['zscore_extreme'] * 0.6:
        zscore_bonus = 10; zscore_favorable = True
    elif bias == "BEARISH" and z_current > profile['zscore_extreme'] * 0.6:
        zscore_bonus = 10; zscore_favorable = True

    bb_cycle, bb_ratio, bb_squeeze_count = detect_bb_cycle(h1, profile)
    bb_compression = bb_cycle == "SQUEEZE"
    consec_count, consec_dir = count_consecutive_candles(m15)
    consecutive_bonus = 0; consec_reversal_risk = consec_count >= profile['consecutive_reversal']
    if consec_reversal_risk:
        if (bias=="BULLISH" and consec_dir=="BEARISH") or (bias=="BEARISH" and consec_dir=="BULLISH"):
            consecutive_bonus = 10
    roc_status, roc_details = detect_roc_extreme(m15, profile)

    # Divergências
    rsi_div, rsi_db, rsi_dd = detect_divergence_v17(m15, 'RSI', order=4)
    macd_div, macd_db, macd_dd = detect_divergence_v17(m15, 'MACD', order=4)
    divergence = rsi_div or macd_div
    div_bonus = max(rsi_db, macd_db); div_detail = rsi_dd or macd_dd

    # S/R, Fib
    sr_levels = detect_sr_clustered(h1)
    sr_bonus, sr_touch, closest_sr = 0, False, None
    if sr_levels:
        closest_sr = min(sr_levels, key=lambda x: abs(x['price'] - c1['close']))
        if abs(closest_sr['price'] - c1['close']) < c1['ATR'] * 0.5:
            sr_bonus = min(closest_sr['strength'] * 3, 15); sr_touch = True
    fibs, fib_dir, _ = calculate_fibonacci_from_swings(h1)
    fib_level, fib_bonus = check_fib_confluence(c1['close'], fibs, c1['ATR'])

    align_type, align_bonus = detect_perfect_alignment(c4, c1, cm, bias)
    vol_st, vol_proxy = analyze_tick_volume(m15)
    vol_confirmed = vol_proxy > 1.3; vol_bonus = 5 if vol_confirmed else 0
    regime_bonus = 5 if "TRENDING" in regime else 0
    pat_score = min(cm.get('pattern_score', 0), 15)

    # ═══ V19.0 FIX #6: ADAPTIVE LEARNING ═══
    # Primeiro backtest para ter dados, depois adapta
    sim_initial = run_walk_forward_backtest(h1, bias, profile, n_folds=4)
    adapted_profile = AdaptiveLearner.adjust_profile(profile, sim_initial, dist_analysis)

    # ═══ SETUP DETECTION ═══
    sig = "MONITORING"; entry = c1['close']; sl_val = c1['close']
    entry_type = "Wait"; sl_reason = "Structural Pivot"
    trade_style = setup_type = None
    vc = profile['vol_class']

    if vc == "EXTREME" and roc_status == "EXTREME":
        sig = "BLOCKED (ROC EXTREMO em EXTREME VOL)"
    elif regime == "RANGING" and consec_reversal_risk and not zscore_favorable and gen_signal == "NEUTRAL":
        sig = "BLOCKED (RANGING + SEM EDGE)"
    else:
        mp_price, mp_type = detect_micro_pullback(m15, bias, c1['ATR'])

        def try_setup_bullish():
            nonlocal sig, sl_val, entry_type, trade_style, setup_type, entry
            if divergence and "BEARISH" in str(divergence) and "HIDDEN" not in str(divergence):
                sig = f"BLOCKED (BEARISH_DIV: {div_detail})"; return

            # V19: Generator-driven setups PRIMEIRO
            if gen_type == "GBM" and gen_signal == "VOL_COMPRESS" and gen_analysis.get('confidence', 0) > 50:
                sig = "LONG (VOL COMPRESSION)"
                sl_val = c1['close'] - adapted_profile['sl_atr_mult'] * c1['ATR']
                entry_type = f"GBM Vol Compress: ratio={gen_analysis['vol_ratio']:.2f}"
                trade_style = "REVERSAL"; setup_type = "GEN_VOL_COMPRESS"
                return

            if gen_type in ["BOOM", "CRASH"] and gen_signal == "POST_SPIKE_ENTRY":
                drift = gen_analysis.get('drift_direction', 'UP')
                if drift == "UP":
                    sig = "LONG (POST-SPIKE DRIFT)"
                    sl_val = c1['close'] - adapted_profile['sl_atr_mult'] * c1['ATR']
                    entry_type = f"Post-spike drift UP ({gen_analysis.get('last_spike_bars',0)} bars)"
                    trade_style = "DAY"; setup_type = "GEN_SPIKE_DRIFT"
                    return

            if gen_type == "STEP" and gen_signal in ["EXTREME_DEVIATION", "HIGH_DEVIATION"]:
                dev = gen_analysis.get('deviation_sigma', 0)
                if dev < -1.5:
                    sig = "LONG (STEP DEVIATION)"
                    sl_val = c1['close'] - adapted_profile['sl_atr_mult'] * c1['ATR']
                    entry_type = f"Step deviation: {dev:.1f}σ (mean reversion)"
                    trade_style = "REVERSAL"; setup_type = "GEN_STEP_REVERT"
                    return

            # Setups clássicos (V18)
            if adx > adapted_profile['adx_strong'] and (abs(c1['close']-c1['EMA_50'])<c1['ATR']*1.5 or c1['RSI']<45):
                if "RANGING" in regime and not hurst_trending and gen_bonus == 0:
                    sig = "BLOCKED (RANGING + HURST + SEM GEN EDGE)"; return
                sig = "LONG (SWING)"; sl_val = detect_swing_level(h1, "BUY", adapted_profile['sl_atr_mult'])
                entry_type = f"Swing — {mp_type}"; trade_style = "SWING"; setup_type = "SWING"
                if mp_price and mp_type != "MARKET": entry = mp_price
            elif adx > adapted_profile['adx_trend_min'] and (c1['close'] > c1['EMA_20'] or pat_score > 0):
                sig = "LONG (DAY)"; sl_val = detect_swing_level(h1, "BUY", adapted_profile['sl_atr_mult']*0.8)
                entry_type = f"Day — {mp_type}"; trade_style = "DAY"; setup_type = "DAY"
                if mp_price and mp_type != "MARKET": entry = mp_price
            elif sr_touch and closest_sr and c1['close'] > closest_sr['price']:
                bk_ok, bk_r = confirm_breakout_volume(m15)
                if bk_ok:
                    sig = "LONG (BREAKOUT)"; sl_val = closest_sr['price'] - c1['ATR']
                    entry_type = f"Breakout S/R (Vol ×{bk_r:.1f})"; trade_style = "BREAKOUT"; setup_type = "BREAKOUT"
            elif z_current < -profile['zscore_extreme'] * 0.6 and hurst_val < 0.48:
                sig = "LONG (MEAN REVERSION)"
                sl_val = c1['close'] - adapted_profile['sl_atr_mult'] * c1['ATR']
                entry_type = f"Mean Reversion Z={z_current:.1f}"; trade_style = "REVERSAL"; setup_type = "MEAN_REVERSION"

            if "LONG" in sig and (entry - sl_val) > adapted_profile['sl_atr_mult'] * c1['ATR']:
                sl_val = entry - adapted_profile['sl_atr_mult'] * c1['ATR']
                sl_reason = f"Max {adapted_profile['sl_atr_mult']:.1f}× ATR ({vc})"

        def try_setup_bearish():
            nonlocal sig, sl_val, entry_type, trade_style, setup_type, entry
            if divergence and "BULLISH" in str(divergence) and "HIDDEN" not in str(divergence):
                sig = f"BLOCKED (BULLISH_DIV: {div_detail})"; return

            if gen_type == "GBM" and gen_signal == "VOL_COMPRESS" and gen_analysis.get('confidence', 0) > 50:
                sig = "SHORT (VOL COMPRESSION)"
                sl_val = c1['close'] + adapted_profile['sl_atr_mult'] * c1['ATR']
                entry_type = f"GBM Vol Compress: ratio={gen_analysis['vol_ratio']:.2f}"
                trade_style = "REVERSAL"; setup_type = "GEN_VOL_COMPRESS"
                return

            if gen_type in ["BOOM", "CRASH"] and gen_signal == "POST_SPIKE_ENTRY":
                drift = gen_analysis.get('drift_direction', 'DOWN')
                if drift == "DOWN":
                    sig = "SHORT (POST-SPIKE DRIFT)"
                    sl_val = c1['close'] + adapted_profile['sl_atr_mult'] * c1['ATR']
                    entry_type = f"Post-spike drift DOWN ({gen_analysis.get('last_spike_bars',0)} bars)"
                    trade_style = "DAY"; setup_type = "GEN_SPIKE_DRIFT"
                    return

            if gen_type == "STEP" and gen_signal in ["EXTREME_DEVIATION", "HIGH_DEVIATION"]:
                dev = gen_analysis.get('deviation_sigma', 0)
                if dev > 1.5:
                    sig = "SHORT (STEP DEVIATION)"
                    sl_val = c1['close'] + adapted_profile['sl_atr_mult'] * c1['ATR']
                    entry_type = f"Step deviation: {dev:.1f}σ (mean reversion)"
                    trade_style = "REVERSAL"; setup_type = "GEN_STEP_REVERT"
                    return

            if adx > adapted_profile['adx_strong'] and (abs(c1['close']-c1['EMA_50'])<c1['ATR']*1.5 or c1['RSI']>55):
                if "RANGING" in regime and not hurst_trending and gen_bonus == 0:
                    sig = "BLOCKED (RANGING + HURST + SEM GEN EDGE)"; return
                sig = "SHORT (SWING)"; sl_val = detect_swing_level(h1, "SELL", adapted_profile['sl_atr_mult'])
                entry_type = f"Swing — {mp_type}"; trade_style = "SWING"; setup_type = "SWING"
                if mp_price and mp_type != "MARKET": entry = mp_price
            elif adx > adapted_profile['adx_trend_min'] and (c1['close'] < c1['EMA_20'] or pat_score > 0):
                sig = "SHORT (DAY)"; sl_val = detect_swing_level(h1, "SELL", adapted_profile['sl_atr_mult']*0.8)
                entry_type = f"Day — {mp_type}"; trade_style = "DAY"; setup_type = "DAY"
                if mp_price and mp_type != "MARKET": entry = mp_price
            elif sr_touch and closest_sr and c1['close'] < closest_sr['price']:
                bk_ok, bk_r = confirm_breakout_volume(m15)
                if bk_ok:
                    sig = "SHORT (BREAKOUT)"; sl_val = closest_sr['price'] + c1['ATR']
                    entry_type = f"Breakout S/R (Vol ×{bk_r:.1f})"; trade_style = "BREAKOUT"; setup_type = "BREAKOUT"
            elif z_current > profile['zscore_extreme'] * 0.6 and hurst_val < 0.48:
                sig = "SHORT (MEAN REVERSION)"
                sl_val = c1['close'] + adapted_profile['sl_atr_mult'] * c1['ATR']
                entry_type = f"Mean Reversion Z={z_current:.1f}"; trade_style = "REVERSAL"; setup_type = "MEAN_REVERSION"

            if "SHORT" in sig and (sl_val - entry) > adapted_profile['sl_atr_mult'] * c1['ATR']:
                sl_val = entry + adapted_profile['sl_atr_mult'] * c1['ATR']
                sl_reason = f"Max {adapted_profile['sl_atr_mult']:.1f}× ATR ({vc})"

        if bias == "BULLISH": try_setup_bullish()
        elif bias == "BEARISH": try_setup_bearish()

    # Spread
    if "LONG" in sig: entry += profile['spread']
    elif "SHORT" in sig: entry -= profile['spread']

    # Backtest final (com perfil adaptado)
    if "BLOCKED" not in sig and sig != "MONITORING":
        sim = run_walk_forward_backtest(h1, bias, adapted_profile, n_folds=4)
    else:
        sim = sim_initial

    mc = monte_carlo_simulation(sim) if sim['TOTAL_TRADES'] >= 5 else \
        {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":0}

    # Perfect Storm V19 (14 fatores agora)
    storm_data = {
        'adx': adx, 'momentum_score': momentum, 'pattern_score': pat_score,
        'divergence': divergence, 'fib_confluence': fib_level is not None,
        'sr_touch': sr_touch, 'perfect_alignment': align_type == "PERFECT_ALIGNMENT",
        'bb_compression': bb_compression, 'regime_trending': "TRENDING" in regime,
        'volume_confirmed': vol_confirmed, 'hurst_trending': hurst_trending,
        'zscore_favorable': zscore_favorable,
        'gen_model_signal': gen_bonus > 0, 'dist_favorable': dist_favorable,
    }
    storm_level, storm_bonus, storm_criteria = calculate_perfect_storm_bonus(storm_data)

    if storm_level == "PERFECT_STORM" and "BLOCKED" not in sig and sig != "MONITORING":
        sig = sig.replace("LONG", "LONG (⭐STORM⭐)").replace("SHORT", "SHORT (⭐STORM⭐)")
        setup_type = "PERFECT_STORM"

    # Div bonus direction-aware
    final_db = 0
    if divergence:
        if ("LONG" in sig and "BULLISH" in str(divergence)) or ("SHORT" in sig and "BEARISH" in str(divergence)):
            final_db = abs(div_bonus)

    # Score V19
    score = calculate_setup_score(
        adx=adx, momentum_score=momentum, pattern_score=pat_score,
        dist_ema50=abs(c1['close']-c1['EMA_50']), atr=c1['ATR'],
        win_rate=sim['WR'], profit_factor=sim['PF'], profile=adapted_profile,
        divergence_bonus=final_db, fib_bonus=fib_bonus, sr_bonus=sr_bonus,
        alignment_bonus=align_bonus, storm_bonus=storm_bonus,
        regime_bonus=regime_bonus, volume_bonus=vol_bonus,
        hurst_bonus=hurst_bonus, zscore_bonus=zscore_bonus,
        consecutive_bonus=consecutive_bonus,
        generator_bonus=gen_bonus, distribution_bonus=dist_bonus)

    # Filtros
    configs = {"PERFECT_STORM":(100,1.5),"BREAKOUT":(60,1.4),"MEAN_REVERSION":(50,1.2),
               "GEN_VOL_COMPRESS":(45,1.1),"GEN_SPIKE_DRIFT":(40,1.0),"GEN_STEP_REVERT":(40,1.0),
               "DAY":(45,1.3),"SWING":(75,1.5)}
    ms,mpf = configs.get(setup_type,(75,1.5))
    if "BLOCKED" not in sig and sig != "MONITORING":
        fails = []
        if score.total < ms: fails.append(f"SCORE={score.total:.0f}<{ms}")
        if sim['NET'] <= 0 and setup_type not in ["GEN_VOL_COMPRESS","GEN_SPIKE_DRIFT","GEN_STEP_REVERT"]:
            fails.append("NET≤0")
        if sim['PF'] < mpf and setup_type not in ["GEN_VOL_COMPRESS","GEN_SPIKE_DRIFT","GEN_STEP_REVERT"]:
            fails.append(f"PF={sim['PF']}<{mpf}")
        if fails: sig = f"BLOCKED ({', '.join(fails)})"

    # Targets
    risk = abs(entry - sl_val)
    if risk == 0: risk = c1['ATR']
    tc = {
        "PERFECT_STORM":(5,10,"TP1 (1:5)","TP2 (1:10)",30,70),
        "BREAKOUT":(adapted_profile['tp1_r'],adapted_profile['tp2_r']+2,f"TP1 (1:{adapted_profile['tp1_r']:.0f})",f"TP2 (1:{adapted_profile['tp2_r']+2:.0f})",50,50),
        "MEAN_REVERSION":(2,3,"TP1 (1:2)","TP2 (1:3)",60,40),
        "GEN_VOL_COMPRESS":(2.5,4,"TP1 Vol","TP2 Vol",50,50),
        "GEN_SPIKE_DRIFT":(2,5,"TP1 Drift","TP2 Drift",50,50),
        "GEN_STEP_REVERT":(1.5,2.5,"TP1 Step","TP2 Step",70,30),
        "DAY":(2,3,"TP1","TP2",60,40),
    }
    r1,r2,l1,l2,p1,p2 = tc.get(setup_type,(adapted_profile['tp1_r'],adapted_profile['tp2_r'],
        f"TP1 (1:{adapted_profile['tp1_r']:.0f})",f"TP2 (1:{adapted_profile['tp2_r']:.0f})",50,50))
    if "LONG" in sig: tp1,tp2=entry+r1*risk,entry+r2*risk
    elif "SHORT" in sig: tp1,tp2=entry-r1*risk,entry-r2*risk
    else: tp1=tp2=entry

    # Scaling / Pirâmide
    pyramid = ScalingEngine.calculate_pyramid(score.grade, score.total, capital, risk_pct, entry, sl_val, c1['ATR'], adapted_profile)

    show = any(x in sig for x in ["SWING","DAY","BREAKOUT","STORM","REVERSION","COMPRESSION","DRIFT","DEVIATION"])

    imgs = [
        plot_candles(h4, f"{name} H4 — Regime: {regime} | Gen: {gen_signal}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels=sr_levels if show else None),
        plot_candles(h1, f"{name} H1 — Hurst:{hurst_val:.2f} Z:{z_current:.1f} VolR:{gen_analysis.get('vol_ratio',1):.2f}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels=sr_levels, fib_levels=fibs if show else None),
        plot_candles(m15, f"{name} M15 — BB:{bb_cycle} Consec:{consec_count} ROC:{roc_status}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, patterns=True)
    ]

    confs = []
    if gen_bonus > 0: confs.append(f"🧮 Generator: {gen_signal} (+{gen_bonus}pts)")
    if dist_favorable: confs.append(f"📊 Distribuição: P{dist_analysis['percentile']:.0f} ({dist_analysis['tail_risk']})")
    if divergence: confs.append(f"🔍 {divergence}: {div_detail}")
    if fib_level: confs.append(f"📐 Fib {fib_level}")
    if sr_touch and closest_sr: confs.append(f"🎯 S/R {closest_sr['touches']}x @ {closest_sr['price']:.2f}")
    if align_type != "NO_ALIGNMENT": confs.append(f"⭐ {align_type}")
    if storm_level: confs.append(f"🌟 {storm_level} ({len(storm_criteria)}/14)")
    if vol_confirmed: confs.append(f"📊 Volume ×{vol_proxy:.1f}")
    if hurst_trending: confs.append(f"🧬 Hurst trending ({hurst_val:.2f})")
    if zscore_favorable: confs.append(f"📊 Z-Score ({z_current:.1f})")
    if consecutive_bonus > 0: confs.append(f"🔢 {consec_count} candles {consec_dir}")
    if bb_compression: confs.append(f"💥 BB Squeeze ({bb_squeeze_count})")

    risks = []
    if "RANGING" in regime: risks.append("⚠️ Regime RANGING")
    if not sim['WF_STABLE']: risks.append("⚠️ Walk-Forward instável")
    if mc.get('positive_pct',0)<60: risks.append(f"⚠️ MC {mc.get('positive_pct',0)}%")
    if roc_status == "EXTREME": risks.append("⚠️ ROC EXTREMO")
    if consec_reversal_risk and consecutive_bonus==0: risks.append(f"⚠️ {consec_count} consecutivas")
    if hurst_regime == "RANDOM_WALK": risks.append("⚠️ Random walk")
    if gen_signal == "VOL_EXPAND": risks.append("⚠️ Vol expandindo — breakout possível")
    if dist_analysis.get('tail_risk') == "FAT_TAILS": risks.append("⚠️ Fat tails — risco de move extremo")

    return {
        "FINAL_DECISION": sig, "TRADE_STYLE": trade_style or "N/A", "SETUP_TYPE": setup_type or "N/A",
        "SETUP_SCORE": float(round(score.total,1)), "BASE_SCORE": float(round(score.base_total,1)),
        "BONUS_SCORE": float(round(score.bonus_total,1)), "SETUP_GRADE": score.grade,
        "INDEX_PROFILE": vc, "GEN_TYPE": gen_type,
        "GEN_ANALYSIS": convert_np(gen_analysis), "GEN_SIGNAL": gen_signal, "GEN_BONUS": gen_bonus,
        "DIST_ANALYSIS": convert_np(dist_analysis), "DIST_BONUS": dist_bonus,
        "ADX_SCORE":float(round(score.trend_strength,1)),"MOMENTUM_SCORE":float(round(score.momentum_align,1)),
        "PATTERN_SCORE":float(round(score.patterns,1)),"VALUE_SCORE":float(round(score.value_zone,1)),
        "HIST_SCORE":float(round(score.historical,1)),
        "DIVERGENCE_BONUS":float(round(score.divergence_bonus,1)),
        "FIB_BONUS":float(round(score.fib_bonus,1)),"SR_BONUS":float(round(score.sr_bonus,1)),
        "ALIGNMENT_BONUS":float(round(score.alignment_bonus,1)),
        "STORM_BONUS":float(round(score.storm_bonus,1)),
        "REGIME_BONUS":float(round(score.regime_bonus,1)),
        "VOLUME_BONUS":float(round(score.volume_bonus,1)),
        "HURST_BONUS":float(round(score.hurst_bonus,1)),
        "ZSCORE_BONUS":float(round(score.zscore_bonus,1)),
        "CONSECUTIVE_BONUS":float(round(score.consecutive_bonus,1)),
        "GENERATOR_BONUS":float(round(score.generator_bonus,1)),
        "DISTRIBUTION_BONUS":float(round(score.distribution_bonus,1)),
        "HURST":float(hurst_val),"HURST_REGIME":hurst_regime,
        "ZSCORE":float(round(z_current,2)),
        "BB_CYCLE":bb_cycle,"BB_RATIO":float(round(bb_ratio,2)),
        "CONSECUTIVE":int(consec_count),"CONSECUTIVE_DIR":consec_dir,
        "ROC_STATUS":roc_status,"MARKET_STRUCTURE":structure,"MARKET_REGIME":regime,
        "TICK_VOLUME":f"{vol_st} (×{vol_proxy:.1f})",
        "PATTERNS": ", ".join(cm.get('patterns',[])) if isinstance(cm.get('patterns',[]),list) and cm.get('patterns',[]) else "Nenhum",
        "DIVERGENCE": divergence or "Nenhuma", "DIVERGENCE_DETAIL": div_detail or "",
        "FIB_LEVEL": fib_level or "N/A", "FIB_DIR": fib_dir or "N/A",
        "SR_LEVELS": int(len(sr_levels)), "ALIGNMENT": align_type,
        "STORM_LEVEL": storm_level or "N/A", "STORM_CRITERIA": storm_criteria,
        "CONFLUENCES": confs, "RISKS": risks, "MOMENTUM": f"{momentum}/3",
        "ENTRY_TYPE": entry_type, "SL_REASON": sl_reason, "SPREAD": float(profile['spread']),
        "WIN_RATE":float(sim['WR']),"NET_PROFIT":float(sim['NET']),
        "MAX_DRAWDOWN":float(sim['DD']),"PROFIT_FACTOR":float(sim['PF']),
        "SHARPE":float(sim['SHARPE']),"SORTINO":float(sim['SORTINO']),
        "WF_STABLE":sim['WF_STABLE'],"FOLD_WRS":sim['FOLD_WRS'],
        "TOTAL_TRADES":int(sim['TOTAL_TRADES']),
        "MC_MEDIAN":float(mc.get('median',0)),"MC_P5":float(mc.get('p5',0)),
        "MC_P95":float(mc.get('p95',0)),"MC_POSITIVE":float(mc.get('positive_pct',0)),
        "ENTRY":float(round(entry,5)),"SL":float(round(sl_val,5)),
        "TP1":float(round(tp1,5)),"TP2":float(round(tp2,5)),
        "TP1_LABEL":l1,"TP2_LABEL":l2,"PCT1":int(p1),"PCT2":int(p2),
        "PYRAMID": convert_np(pyramid),
        "ADAPTED_RISK_MULT": adapted_profile['risk_mult'],
        "ADAPTED_SL_MULT": adapted_profile['sl_atr_mult'],
        "IMAGES": imgs, "ATR": float(c1['ATR']), "INITIAL_RISK": float(risk),
    }

# ==============================================================================
# MULTI-ASSET SCANNER
# ==============================================================================

async def quick_scan_asset(code, name):
    """Scan rápido: H1 apenas para ranking"""
    try:
        h1_raw = await fetch_single(code, 3600, 300)
        if not h1_raw: return None
        df = indicators(prep_df(h1_raw))
        if len(df) < 50: return None
        c = df.iloc[-1]; profile = get_profile(name)
        hurst_val, _ = calculate_hurst_exponent(df['close'])
        z = c['ZSCORE'] if pd.notna(c['ZSCORE']) else 0
        gen = GeneratorModel.analyze_gbm(df, profile, 100) if profile.get('gen_type')=='GBM' else {}
        regime, _ = classify_market_regime(df)
        quick_score = 0
        if c['ADX'] > profile['adx_strong']: quick_score += 30
        elif c['ADX'] > profile['adx_trend_min']: quick_score += 15
        if abs(z) > profile['zscore_extreme'] * 0.6: quick_score += 20
        if hurst_val > profile['hurst_trend_min'] or hurst_val < 0.45: quick_score += 15
        if gen.get('signal') not in [None, 'NEUTRAL', 'VOL_NORMAL']: quick_score += 20
        if "TRENDING" in regime: quick_score += 10
        bias = "BULLISH" if c['close'] > c['EMA_200'] else "BEARISH"
        return {"name": name, "code": code, "score": quick_score, "bias": bias,
                "adx": round(c['ADX'], 1), "hurst": round(hurst_val, 3), "zscore": round(z, 2),
                "regime": regime, "gen_signal": gen.get('signal', 'N/A'),
                "profile": profile['vol_class']}
    except:
        return None

# ==============================================================================
# STREAMLIT UI V19.0
# ==============================================================================

st.sidebar.title("🧮 SI-APATECO V19.0")
st.sidebar.caption("GENERATOR CRACKER")

if "GEMINI_API_KEY" in st.secrets:
    api = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ API ATIVA")
else:
    api = st.sidebar.text_input("CHAVE API GEMINI", type="password")

st.sidebar.divider()
capital = st.sidebar.number_input("💰 Capital ($)", min_value=100, value=10000, step=100)
risk_pct = st.sidebar.slider("📊 Risco Base (%)", 0.5, 3.0, 1.0, 0.1)

st.sidebar.divider()
mode = st.sidebar.radio("⚙️ Modo", ["🔍 Análise", "🔎 Scanner", "📊 Monitor"])

st.sidebar.divider()
st.sidebar.info("""
**V19.0 — GENERATOR CRACKER:**
- 🧮 Modela GBM/Poisson/Bernoulli
- 📊 Vol Realizada vs Teórica
- 💥 Spike Cycle Detector
- 📈 Distribuição: Skew/Kurt/P-val
- 🔢 Step Deviation + Runs Test
- 📈 Scaling In / Pirâmide
- 🧠 Adaptive Parameter Learning
- 🔎 Multi-Asset Scanner
- + Tudo do V18
""")

st.title("🧮 SI-APATECO V19.0 — GENERATOR CRACKER")
st.caption("Modelagem do Gerador | Vol Realizada vs Teórica | Distribuição | Pirâmide | Scanner")

with st.spinner("Carregando ativos..."):
    assets = get_assets()
if not assets:
    st.error("❌ FALHA NA CONEXÃO"); st.stop()

# ──────────────────────────────────────────────
# MODO ANÁLISE
# ──────────────────────────────────────────────
if mode == "🔍 Análise":
    c1_col, c2_col = st.columns([1, 2])
    with c1_col:
        target = st.selectbox("🎯 ATIVO", list(assets.keys()))
        prof = get_profile(target)
        st.markdown(f"**{prof['vol_class']}** — Gen: `{prof.get('gen_type','?')}`")
        st.caption(f"σ={prof.get('sigma_annual',0):.2f} | SL:{prof['sl_atr_mult']}×ATR | Risk:×{prof['risk_mult']}")
        run = st.button("🧮 CRACKEAR", use_container_width=True)

    with c2_col:
        if run:
            if not api: st.error("⚠️ API KEY"); st.stop()
            status = st.status("🧮 V19.0 GENERATOR CRACKER...", expanded=True)
            status.write("1️⃣ Dados MTF (H1=800, H4=400, M15=2000)...")
            h1r, h4r, m15r, err = asyncio.run(fetch_tri_force(assets[target]))
            if err: status.update(state='error'); st.error(err); st.stop()
            status.write("2️⃣ Modelando Gerador...")
            status.write("3️⃣ Análise de Distribuição...")
            status.write("4️⃣ Hurst + Z-Score + BB + ROC...")
            status.write("5️⃣ Walk-Forward (4 folds) + Monte Carlo...")
            status.write("6️⃣ Adaptive Learning + Scaling...")
            data = sniper_core_v19(target, h1r, h4r, m15r, capital, risk_pct)
            imgs = data.pop("IMAGES")
            status.write("7️⃣ Gemini 3 Pro...")
            genai.configure(api_key=api)
            dc = convert_np(data)
            try:
                model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
                ai = model.generate_content([SYSTEM_PROMPT, f"DADOS V19.0: {json.dumps(dc)}"] + imgs).text
                status.update(label="✅ V19.0 COMPLETA", state="complete")
            except Exception as e:
                ai = f"⚠️ IA indisponível: {str(e)[:150]}"; status.update(label="⚠️ Sem IA", state="complete")

            # DISPLAY
            g = data['SETUP_GRADE']
            gc = {"S":("score-s","👑"),"A++":("score-a-pp","🏆"),"A+":("score-a-p","💎"),
                  "A":("score-a","⭐"),"B":("score-b","📊")}.get(g,("score-c","⚠️"))

            st.markdown(f"""
            <div style='text-align:center;padding:25px;background:rgba(168,85,247,0.08);border:3px solid #a855f7;border-radius:15px;'>
                <h1 style='margin:0;'>{gc[1]} GRADE: <span class='{gc[0]}'>{g}</span></h1>
                <p style='font-size:28px;margin:15px 0;'><strong>SCORE: {data["SETUP_SCORE"]}/160</strong></p>
                <p style='font-size:16px;'>Base: {data["BASE_SCORE"]}/100 | Bonus: +{data["BONUS_SCORE"]}/60</p>
                <p style='font-size:18px;color:#a855f7;'>🧮 {data["GEN_TYPE"]} — {data.get("SETUP_TYPE","N/A")}</p>
            </div>""", unsafe_allow_html=True)

            if data.get('SETUP_TYPE') == "PERFECT_STORM": st.success("🌟 PERFECT STORM!"); st.balloons()

            # Generator Model Display
            st.subheader("🧮 MODELO DO GERADOR")
            ga = data.get('GEN_ANALYSIS', {})
            st.markdown(f"<div class='gen-model'>", unsafe_allow_html=True)
            g1,g2,g3,g4 = st.columns(4)
            g1.metric("Tipo", data['GEN_TYPE'])
            g2.metric("Sinal", data['GEN_SIGNAL'])
            g3.metric("Bonus", f"+{data['GEN_BONUS']}pts")
            if data['GEN_TYPE'] == 'GBM':
                g4.metric("Vol Ratio", f"{ga.get('vol_ratio',1):.3f}")
                vr1,vr2,vr3 = st.columns(3)
                vr1.metric("Vol Realizada", f"{ga.get('vol_realized',0)*100:.2f}%")
                vr2.metric("Vol Teórica", f"{ga.get('vol_theoretical',0)*100:.2f}%")
                vr3.metric("Confiança", f"{ga.get('confidence',0):.0f}%")
            elif data['GEN_TYPE'] in ['BOOM','CRASH']:
                g4.metric("Último Spike", f"{ga.get('last_spike_bars',999)} bars")
                cb1,cb2,cb3 = st.columns(3)
                cb1.metric("Drift", ga.get('drift_direction','?'))
                cb2.metric("Spikes Detectados", ga.get('spikes_found',0))
                cb3.metric("Avg Between", f"{ga.get('avg_bars_between_spikes',0):.0f}")
            elif data['GEN_TYPE'] == 'STEP':
                g4.metric("Deviation", f"{ga.get('deviation_sigma',0):.1f}σ")
                st1,st2 = st.columns(2)
                st1.metric("Runs Test", ga.get('runs_test','?'))
                st2.metric("Runs Z", f"{ga.get('runs_z',0):.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

            # Distribution
            st.subheader("📊 DISTRIBUIÇÃO DE RETORNOS")
            da = data.get('DIST_ANALYSIS', {})
            d1,d2,d3,d4,d5 = st.columns(5)
            d1.metric("Skewness", f"{da.get('skewness',0):.3f}")
            d2.metric("Kurtosis", f"{da.get('kurtosis',3):.3f}")
            d3.metric("Tails", da.get('tail_risk','NORMAL'))
            d4.metric("Percentil", f"{da.get('percentile',50):.0f}%")
            d5.metric("Normal?", "✅" if da.get('is_normal',True) else "❌")

            # Stats
            st.subheader("🧬 ESTATÍSTICA SINTÉTICO")
            s1,s2,s3,s4,s5 = st.columns(5)
            s1.metric("Hurst", f"{data['HURST']:.3f}", data['HURST_REGIME'])
            s2.metric("Z-Score", f"{data['ZSCORE']:.2f}")
            s3.metric("BB Cycle", data['BB_CYCLE'])
            s4.metric("Consecutivas", f"{data['CONSECUTIVE']}", data['CONSECUTIVE_DIR'])
            s5.metric("ROC", data['ROC_STATUS'])

            # WF + MC
            st.subheader("📊 VALIDAÇÃO")
            m1,m2,m3,m4,m5,m6 = st.columns(6)
            m1.metric("WR",f"{data['WIN_RATE']}%"); m2.metric("PF",f"{data['PROFIT_FACTOR']}")
            m3.metric("Sharpe",f"{data['SHARPE']}"); m4.metric("Sortino",f"{data['SORTINO']}")
            m5.metric("DD",f"{data['MAX_DRAWDOWN']}R"); m6.metric("Trades",f"{data['TOTAL_TRADES']}")
            if data['FOLD_WRS']: st.caption("Folds: "+" | ".join([f"F{i+1}: {w}%" for i,w in enumerate(data['FOLD_WRS'])]))
            mc1,mc2,mc3,mc4 = st.columns(4)
            mc1.metric("MC Mediana",f"{data['MC_MEDIAN']}R"); mc2.metric("MC P5",f"{data['MC_P5']}R")
            mc3.metric("MC P95",f"{data['MC_P95']}R"); mc4.metric("MC %+",f"{data['MC_POSITIVE']}%")

            # Breakdown
            st.subheader("🔬 BREAKDOWN SCORE")
            bc1,bc2 = st.columns(2)
            with bc1:
                st.markdown("**Base (100):**")
                st.dataframe(pd.DataFrame([
                    {"Item":"ADX","Score":f"{data['ADX_SCORE']}/25"},
                    {"Item":"Momentum","Score":f"{data['MOMENTUM_SCORE']}/20"},
                    {"Item":"Padrões","Score":f"{data['PATTERN_SCORE']}/15"},
                    {"Item":"Zona Valor","Score":f"{data['VALUE_SCORE']}/15"},
                    {"Item":"Histórico WF","Score":f"{data['HIST_SCORE']}/25"},
                ]),hide_index=True,use_container_width=True)
            with bc2:
                st.markdown("**Bonus (60):**")
                st.dataframe(pd.DataFrame([
                    {"Item":"🧮 Generator","Bonus":f"+{data['GENERATOR_BONUS']}"},
                    {"Item":"📊 Distribuição","Bonus":f"+{data['DISTRIBUTION_BONUS']}"},
                    {"Item":"Divergência","Bonus":f"+{data['DIVERGENCE_BONUS']}"},
                    {"Item":"Fibonacci","Bonus":f"+{data['FIB_BONUS']}"},
                    {"Item":"S/R","Bonus":f"+{data['SR_BONUS']}"},
                    {"Item":"Alignment","Bonus":f"+{data['ALIGNMENT_BONUS']}"},
                    {"Item":"Storm","Bonus":f"+{data['STORM_BONUS']}"},
                    {"Item":"Regime","Bonus":f"+{data['REGIME_BONUS']}"},
                    {"Item":"Volume","Bonus":f"+{data['VOLUME_BONUS']}"},
                    {"Item":"Hurst","Bonus":f"+{data['HURST_BONUS']}"},
                    {"Item":"Z-Score","Bonus":f"+{data['ZSCORE_BONUS']}"},
                    {"Item":"Consecutive","Bonus":f"+{data['CONSECUTIVE_BONUS']}"},
                ]),hide_index=True,use_container_width=True)

            if data['CONFLUENCES']:
                st.subheader("🔥 CONFLUÊNCIAS")
                for c in data['CONFLUENCES']: st.markdown(f"- {c}")
            if data['RISKS']:
                st.subheader("⚠️ RISCOS")
                for r in data['RISKS']: st.warning(r)

            st.divider()
            d = data['FINAL_DECISION']
            if any(x in d for x in ["SWING","DAY","BREAKOUT","STORM","REVERSION","COMPRESSION","DRIFT","DEVIATION"]):
                st.success(f"✅ {d}")
            elif "BLOCKED" in d: st.error(f"🛑 {d}")
            else: st.warning(f"⏸️ {d}")

            if any(x in d for x in ["SWING","DAY","BREAKOUT","STORM","REVERSION","COMPRESSION","DRIFT","DEVIATION"]):
                st.subheader(f"📋 PLANO — {data['INDEX_PROFILE']}")
                st.dataframe(pd.DataFrame([
                    {"P":"Entrada","V":f"{data['ENTRY']}","N":data['ENTRY_TYPE']},
                    {"P":"Stop Loss","V":f"{data['SL']}","N":data['SL_REASON']},
                    {"P":data['TP1_LABEL'],"V":f"{data['TP1']}","N":f"Realizar {data['PCT1']}%"},
                    {"P":data['TP2_LABEL'],"V":f"{data['TP2']}","N":f"Realizar {data['PCT2']}% + trail"},
                    {"P":"Spread","V":f"{data['SPREAD']}","N":"Incluído"},
                ]),hide_index=True,use_container_width=True)

                # Pirâmide
                pyr = data.get('PYRAMID',{})
                if pyr.get('n_levels',0) > 1:
                    st.subheader("📈 PIRÂMIDE / SCALING IN")
                    st.caption(f"Total: {pyr['n_levels']} níveis | Risco: {pyr['total_risk_pct']:.1f}% | Size: {pyr['total_size']} un")
                    for i, lvl in enumerate(pyr.get('levels',[])):
                        st.info(f"**Nível {i+1}:** Entrada {lvl['entry']:.4f} | Risco {lvl['risk_pct']:.1f}% | Size {lvl['size']} | {lvl['trigger']}")
                else:
                    lvl = pyr.get('levels',[{}])[0]
                    st.info(f"**Posição:** Size {lvl.get('size',0)} un | Risco {lvl.get('risk_pct',risk_pct):.1f}% | {lvl.get('trigger','')}")

                st.caption(f"🧠 Adaptive: Risk ×{data.get('ADAPTED_RISK_MULT',1):.2f} | SL ×{data.get('ADAPTED_SL_MULT',2.5):.2f}")

            st.divider()
            tabs = st.tabs(["H4","H1","M15"])
            with tabs[0]: st.image(imgs[0], use_container_width=True)
            with tabs[1]: st.image(imgs[1], use_container_width=True)
            with tabs[2]: st.image(imgs[2], use_container_width=True)

            st.divider()
            st.subheader("🤖 ANÁLISE IA")
            st.markdown(ai)

# ──────────────────────────────────────────────
# MODO SCANNER
# ──────────────────────────────────────────────
elif mode == "🔎 Scanner":
    st.subheader("🔎 MULTI-ASSET SCANNER V19.0")
    st.caption("Escaneia todos os sintéticos e ranqueia por oportunidade")

    if st.button("🔎 ESCANEAR TODOS", use_container_width=True):
        with st.spinner("Escaneando todos os ativos..."):
            async def run_scanner():
                tasks = [quick_scan_asset(code, name) for name, code in assets.items()]
                return await asyncio.gather(*tasks)
            results = asyncio.run(run_scanner())
            valid = [r for r in results if r is not None]
            valid.sort(key=lambda x: x['score'], reverse=True)

        if valid:
            st.success(f"✅ {len(valid)} ativos escaneados")
            for i, r in enumerate(valid[:10]):
                emoji = "🟢" if r['score'] >= 40 else "🟡" if r['score'] >= 20 else "🔴"
                st.markdown(f"""
                <div class='scanner-card'>
                    <strong>{emoji} #{i+1} {r['name']}</strong> — Score: <strong>{r['score']}</strong> | Bias: {r['bias']}<br>
                    <small>ADX: {r['adx']} | Hurst: {r['hurst']} | Z: {r['zscore']} | Regime: {r['regime']} | Gen: {r['gen_signal']} | {r['profile']}</small>
                </div>""", unsafe_allow_html=True)
        else:
            st.warning("Nenhum ativo disponível")

# ──────────────────────────────────────────────
# MODO MONITOR
# ──────────────────────────────────────────────
elif mode == "📊 Monitor":
    st.subheader("📊 TRADE MONITOR V19.0")
    c1_m,c2_m = st.columns(2)
    with c1_m:
        ms = st.selectbox("Ativo", list(assets.keys()))
        md = st.selectbox("Direção", ["LONG","SHORT"])
    with c2_m:
        me = st.number_input("Entrada", value=1000.0, step=0.1)
        msl = st.number_input("Stop", value=990.0, step=0.1)
    c3_m,c4_m = st.columns(2)
    with c3_m: mt1 = st.number_input("TP1", value=1030.0, step=0.1)
    with c4_m: mt2 = st.number_input("TP2", value=1050.0, step=0.1)

    if st.button("🧮 MONITORAR", use_container_width=True):
        @dataclass
        class ActiveTrade:
            symbol:str; direction:str; entry_price:float; current_price:float
            sl:float; tp1:float; tp2:float; entry_time:datetime
            atr:float; initial_risk:float
            sl_moved_to_be:bool=False; tp1_hit:bool=False; realized_pct:float=0.0
            highest_price:float=0.0; lowest_price:float=999999.0
            def update_price(self,p):
                self.current_price=p
                if self.direction=="LONG": self.highest_price=max(self.highest_price,p)
                else: self.lowest_price=min(self.lowest_price,p)
            def get_current_r(self):
                profit=(self.current_price-self.entry_price) if self.direction=="LONG" else (self.entry_price-self.current_price)
                return profit/self.initial_risk if self.initial_risk!=0 else 0

        trade = ActiveTrade(ms,md,me,me,msl,mt1,mt2,datetime.now(),abs(me-msl)/2.5,abs(me-msl))
        if md=="LONG": trade.highest_price=me
        else: trade.lowest_price=me
        sph,mph,cph = st.empty(),st.empty(),st.empty()
        for _ in range(120):
            try:
                _,_,m15r,err = asyncio.run(fetch_tri_force(assets[ms]))
                if not err and m15r:
                    mdf = indicators(prep_df(m15r))
                    trade.update_price(mdf['close'].iloc[-1])
                    cr = trade.get_current_r()
                    hs = 100
                    alerts = []
                    if not trade.sl_moved_to_be and cr>=1.5: alerts.append("🟢 MOVER SL → BE")
                    if 'ZSCORE' in mdf.columns:
                        z = mdf['ZSCORE'].iloc[-1]
                        if (md=="LONG" and z>2) or (md=="SHORT" and z<-2):
                            alerts.append(f"⚠️ Z-Score {z:.1f}"); hs-=15
                    hcl = "health-exc" if hs>=80 else "health-good" if hs>=60 else "health-warn" if hs>=40 else "health-danger"
                    sph.markdown(f"<div class='{hcl}'><h3>R: {cr:+.2f} | Score: {hs}/100</h3></div>",unsafe_allow_html=True)
                    with mph.container():
                        a,b,c = st.columns(3)
                        a.metric("Preço",f"{trade.current_price:.4f}")
                        b.metric("R",f"{cr:+.2f}")
                        c.metric("Z-Score",f"{mdf['ZSCORE'].iloc[-1]:.1f}" if 'ZSCORE' in mdf.columns else "N/A")
                    if alerts:
                        for al in alerts: st.warning(al)
                    with cph.container():
                        st.image(plot_candles(mdf.tail(50),f"{ms} Monitor",trade.entry_price,trade.sl,trade.tp1,trade.tp2),use_container_width=True)
                time.sleep(5)
            except: break
        st.success("✅ Monitor finalizado")
