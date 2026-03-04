import streamlit as st
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Comparador de Mercado", page_icon="🛒")

st.title("🛒 Leitor de Preços - Teste")
st.write("Cole o link direto de um produto para testarmos se o site tem bloqueio.")

url = st.text_input("Link do Produto:")

if st.button("Buscar Dados"):
    if url:
        with st.spinner("Acessando o mercado disfarçado de humano..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    # Mudamos para 'domcontentloaded' (espera carregar o básico) e aumentamos para 30s
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    title = page.title()
                    
                    st.success(f"✅ Sucesso! Passamos a barreira. Título da página do mercado: {title}")
                    
                    browser.close()
            except Exception as e:
                # Agora ele vai cuspir o erro real na tela
                st.error(f"❌ O site barrou ou demorou. O erro real foi: {e}")
    else:
        st.warning("Por favor, cole um link antes de buscar.")
