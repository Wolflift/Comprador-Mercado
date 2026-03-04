import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação do motor de navegação no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras Pro", layout="wide")
st.title("🛒 Engine V10 - Seleção por Escopo (Beltrame)")

# Entrada de dados
lista_txt = st.text_area("Digite sua lista (um por linha):", placeholder="Cebola\nArroz\nFeijão")

if st.button("Executar Busca Profissional 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Mapeando componentes e isolando produtos..."):
            try:
                with sync_playwright() as p:
                    # Lançamento do navegador com disfarce de usuário real
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"
                    )
                    page = context.new_page()
                    
                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # 1. Geração da URL de busca
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            # 2. Navegação com espera de carregamento do DOM
                            page.goto(url, wait_until="domcontentloaded", timeout=30000)
                            
                            # 3. Sincronismo: aguarda o elemento de preço aparecer
                            page.wait_for_selector("text=R$", timeout=10000)
                            page.wait_for_timeout(2000) # Estabilização final

                            # 4. A MÁGICA DO DOM: O robô isola os blocos (cards) de produtos.
                            # Retorna apenas o texto de cada 'quadrado' de produto individualmente.
                            cards_data = page.evaluate("""
                                () => {
                                    return Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 300)
                                        .map(el => el.innerText);
                                }
                            """)

                            if cards_data:
                                # Analisamos
