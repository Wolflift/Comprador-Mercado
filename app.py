import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Essa é a marretada: obriga o servidor a instalar o navegador fantasma
os.system("playwright install chromium")

st.set_page_config(page_title="Comparador de Mercado", page_icon="🛒")

st.title("🛒 Leitor de Preços - Teste")
st.write("Cole o link direto de uma categoria ou produto para testarmos.")

url = st.text_input("Link do Produto:")

if st.button("Buscar Dados"):
    if url:
        with st.spinner("Acessando o mercado disfarçado de humano (pode demorar uns segundos a mais na primeira vez)..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    title = page.title()
                    
                    st.success(f"✅ Sucesso absoluto! Passamos a barreira. Título da página: {title}")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ O erro real foi: {e}")
    else:
        st.warning("Por favor, cole um link antes de buscar.")
