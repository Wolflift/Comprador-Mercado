import os
import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright

os.system("playwright install chromium")

st.set_page_config(page_title="Beltrame Pro v17", page_icon="🛒", layout="wide")

# 1. MAPEAMENTO DAS CATEGORIAS (Sem a URL de Promoções)
CATEGORIAS = {
    "Mercearia": "https://beltramesupermercados.com.br/categorias/mercearia",
    "Carnes e Aves": "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "Hortifruti": "https://beltramesupermercados.com.br/categorias/hortifruti",
    "Bebidas": "https://beltramesupermercados.com.br/categorias/bebidas",
    "Laticínios e Frios": "https://beltramesupermercados.com.br/categorias/laticinios-e-frios",
    "Higiene e Beleza": "https://beltramesupermercados.com.br/categorias/higiene-e-beleza",
    "Limpeza": "https://beltramesupermercados.com.br/categorias/limpeza",
    "Peixes e Frutos do Mar": "https://beltramesupermercados.com.br/categorias/peixes-e-frutos-do-mar"
}

def limpar_valor(texto):
    try: return float(texto.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except: return 0.0

st.title("🛒 Engine Beltrame - Filtro de Negativação Absoluto (v17)")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Controle")
    if st.button("🚀 Iniciar Varredura"):
        with st.spinner("Limpando ruídos e sincronizando dados..."):
            try:
                with sync_play
