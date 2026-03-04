import streamlit as st
from playwright.sync_api import sync_playwright

# Configura a aba do navegador
st.set_page_config(page_title="Comparador de Mercado", page_icon="🛒")

# Interface visual
st.title("🛒 Leitor de Preços - Teste")
st.write("Cole o link direto de um produto para testarmos se o site tem bloqueio.")

url = st.text_input("Link do Produto:")

if st.button("Buscar Dados"):
    if url:
        with st.spinner("Acessando o mercado disfarçado de humano..."):
            try:
                with sync_playwright() as p:
                    # Prepara o navegador invisível
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    # Acessa o site e espera carregar
                    page.goto(url, wait_until="networkidle", timeout=20000)
                    
                    # Pega o título da aba do site para provar que entramos
                    title = page.title()
                    
                    st.success(f"✅ Sucesso! Passamos a barreira. Título da página do mercado: {title}")
                    
                    browser.close()
            except Exception as e:
                st.error("❌ O site bloqueou a leitura ou demorou demais para responder.")
    else:
        st.warning("Por favor, cole um link antes de buscar.")
