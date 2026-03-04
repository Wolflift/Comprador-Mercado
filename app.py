import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Garante que o motor do navegador seja instalado no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Rancho da Mãe", page_icon="🛒", layout="wide")
st.title("🛒 Lista de Compras Inteligente - Beltrame")

# Interface limpa para digitar os itens
lista_texto = st.text_area("Sua Lista de Compras:", placeholder="Digite um item por linha.\nEx: Arroz 5kg\nCebola\nLeite")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista_texto.split('\n') if i.strip()]
    
    if itens:
        with st.spinner(f"O robô está no Beltrame procurando {len(itens)} itens..."):
            try:
                with sync_playwright() as p:
                    # Lança o navegador invisível
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
                    page = context.new_page()
                    
                    resultados_lista = []
                    valor_total = 0.0
                    
                    for item in itens:
                        try:
                            # Busca direta para ganhar velocidade
                            query = urllib.parse.quote(item)
                            url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url_busca, wait_until="domcontentloaded", timeout=45000)
                            
                            # Espera os preços carregarem na tela
                            page.wait_for_timeout(3000)
                            
                            # Extrai o conteúdo visível para análise
                            conteudo = page.locator("body").inner_text()
                            linhas = [l.strip() for l in conteudo.split('\n') if l.strip()]
                            
                            item_encontrado = False
                            for i, linha in enumerate(linhas):
                                if 'R$' in linha and any(c.isdigit() for c in linha):
                                    # Encontrou um preço, agora busca o nome nas linhas próximas
                                    for j in range(i+1, min(i+10, len(linhas))):
                                        candidato_nome = linhas[j]
                                        # Filtra termos que não são nomes de produtos
                                        termos_lixo = ['ofer
