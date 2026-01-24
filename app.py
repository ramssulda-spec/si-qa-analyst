import streamlit as st
import asyncio
import websockets
import json
import requests
import google.generativeai as genai
import traceback

st.set_page_config(page_title="Diagnóstico SI-QA", page_icon="🚑")

st.title("🚑 Modo de Diagnóstico SI-QA")
st.write("Vamos testar cada componente do sistema separadamente para achar o erro.")

# --- INPUTS ---
st.subheader("1. Configuração")
api_key = st.text_input("Gemini API Key", type="password")
if "GEMINI_API_KEY" in st.secrets and not api_key:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.success("Chave detectada nos Secrets!")

# --- TESTE 1: GOOGLE GEMINI ---
st.divider()
st.subheader("2. Teste de Inteligência (Gemini)")
if st.button("Testar Gemini"):
    if not api_key:
        st.error("Coloque a API Key primeiro.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("models/gemini-3-flash-preview")
            response = model.generate_content("Diga apenas 'Operante'.")
            st.success(f"✅ Gemini Respondeu: {response.text}")
        except Exception as e:
            st.error(f"❌ Falha no Gemini: {str(e)}")
            st.code(traceback.format_exc())

# --- TESTE 2: DERIV API ---
st.divider()
st.subheader("3. Teste de Dados (Deriv API)")
async def test_deriv():
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as ws:
            # Teste simples: Pedir lista de ativos
            await ws.send(json.dumps({"ping": 1}))
            res = await ws.recv()
            return f"Conectado! Resposta: {res}"
    except Exception as e:
        return f"Erro: {str(e)}"

if st.button("Testar Conexão Deriv"):
    try:
        res = asyncio.run(test_deriv())
        if "Erro" in res:
            st.error(f"❌ Falha na Deriv: {res}")
        else:
            st.success(f"✅ Deriv Operante: {res}")
    except Exception as e:
        st.error(f"❌ Erro Crítico Python: {str(e)}")
        st.code(traceback.format_exc())

# --- TESTE 3: BIBLIOTECAS ---
st.divider()
st.subheader("4. Verificação de Bibliotecas")
try:
    import pandas as pd
    import numpy as np
    from PIL import Image
    st.success("✅ Pandas, Numpy e Pillow instalados corretamente.")
except ImportError as e:
    st.error(f"❌ Falta instalar biblioteca: {str(e)}")
    st.info("Verifique seu requirements.txt")

