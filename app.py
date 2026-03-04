import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação obrigatória do navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Minhas Compras", page_icon="🛒", layout="wide")
st.title("🛒 Lista de Compras - Beltrame")

# Caixa de texto limpa para a sua mãe digitar
lista_texto = st.text_area("Sua Lista de Compras:", placeholder="Digite os itens (um por linha).\nEx: Cebola\nArroz 5kg")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista_texto.split('\n') if i.strip()]
    
    if itens:
        with st.spinner(f"Pesquisando {len(itens)} itens no Beltrame..."):
            try:
                with sync_playwright() as p:
                    # Abre o navegador invisível
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
                    page = context.new_page()
                    
                    resultados = []
                    total_compra = 0.0
                    
                    for item in itens:
                        try:
                            # Vai direto para a busca do item
                            query = urllib.parse.quote(item)
                            url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url_busca, wait_until="domcontentloaded", timeout=45000)
                            
                            # Pequena pausa para o site carregar os preços
                            page.wait_for_timeout(3000)
                            
                            # Extrai o texto da página
                            corpo = page.locator("body").inner_text()
                            linhas = [l.strip() for l in corpo.split('\n') if l.strip()]
                            
                            encontrou = False
                            for i, linha in enumerate(linhas):
                                if 'R$' in linha and any(c.isdigit() for c in linha):
                                    # Procura o nome do produto nas próximas 8 linhas
                                    for j in range(i+1, min(i+9, len(linhas))):
                                        cand = linhas
