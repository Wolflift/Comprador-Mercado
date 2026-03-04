import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação automática do navegador no servidor do Streamlit
os.system("playwright install chromium")

st.set_page_config(page_title="Rancho Automático", page_icon="🛒", layout="wide")
st.title("🛒 Lista de Compras Inteligente - Beltrame")

lista_input = st.text_area("Sua Lista de Compras:", placeholder="Digite um item por linha (ex: Arroz 5kg)")

if st.button("Calcular Valor Total 🛒"):
    itens = [i.strip() for i in lista_input.split('\n') if i.strip()]
    
    if itens:
        with st.spinner(f"O robô está processando {len(itens)} itens..."):
            try:
                with sync_playwright() as p:
                    # Lança o navegador com disfarce humano para evitar bloqueios
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
                    page = context.new_page()
                    
                    resultados = []
                    total_compra = 0.0
                    
                    for item in itens:
                        try:
                            # 1. Busca direta via URL para evitar cliques falhos
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url, wait_until="domcontentloaded", timeout=45000)
                            
                            # 2. ESPERA CRÍTICA: Aguarda o símbolo R$ aparecer na tela
                            # Isso garante que o site já renderizou os preços
                            page.wait_for_selector("text=R$", timeout=15000)
                            page.wait_for_timeout(2000) # Pausa técnica de segurança
                            
                            # 3. EXTRAÇÃO: Captura o texto e limpa linhas vazias
                            conteudo = page.locator("body").inner_text()
                            linhas = [l.strip() for l in conteudo.split('\n') if l.strip()]
                            
                            item_foi_achado = False
                            for i, linha in enumerate(linhas):
                                # Se a linha contém o preço
                                if 'R$' in linha and any(c.isdigit() for c in linha):
                                    preco_raw = linha
                                    nome_item = "Desconhecido"
                                    
                                    # BUSCA 360: Procura o nome nas 5 linhas acima E 5 abaixo
                                    # Isso resolve o problema de o layout mudar na busca
                                    indices_vizinhos = [i-1,
