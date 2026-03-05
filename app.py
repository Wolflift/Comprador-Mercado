import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor do Streamlit
os.system("playwright install chromium")

st.set_page_config(page_title="Comparador Beltrame Pro", page_icon="🛒", layout="wide")

st.title("🛒 Engine de Busca por Categorias - Beltrame")
st.write("O robô irá percorrer as categorias mapeadas para encontrar o seu item com precisão.")

# 1. MAPEAMENTO DAS URLs (Sistematização de dados conforme fontes [1, 2])
CATEGORIAS = [
    "https://beltramesupermercados.com.br/promocoes",
    "https://beltramesupermercados.com.br/categorias/mercearia",
    "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "https://beltramesupermercados.com.br/categorias/hortifruti",
    "https://beltramesupermercados.com.br/categorias/bebidas-alcoolicas",
    "https://beltramesupermercados.com.br/categorias/bebidas",
    "https://beltramesupermercados.com.br/categorias/laticinios-e-frios",
    "https://beltramesupermercados.com.br/categorias/higiene-e-beleza",
    "https://beltramesupermercados.com.br/categorias/limpeza",
    "https://beltramesupermercados.com.br/categorias/peixes-e-frutos-do-mar"
]

item_alvo = st.text_input("Qual item você deseja encontrar?", placeholder="Ex: cebola, arroz, sabão...")

if st.button("Executar Varredura Geral 🚀"):
    if not item_alvo:
        st.warning("Por favor, digite o nome de um item.")
    else:
        with st.spinner(f"O robô está percorrendo todas as seções em busca de '{item_alvo}'..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    resultados_finais = []

                    # 2. LOOP DE AUTOMAÇÃO (Percorre cada link fornecido)
                    for url in CATEGORIAS:
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=30000)
                            
                            # Espera mínima para carregar preços
                            page.wait_for_selector("text=R$", timeout=10000)
                            
                            # Captura o texto e transforma em lista para processamento [5, 6]
                            text_content = page.locator("body").inner_text()
                            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                            
                            # 3. LÓGICA DE EXTRAÇÃO E FILTRO
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    preco = line
                                    nome = "Desconhecido"
                                    
                                    # Busca o nome olhando para cima (sua lógica funcional)
                                    for j in range(i-1, -1, -1):
                                        text_prev = lines[j].lower()
                                        ignore = ['carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 'off', 'ver mais', 'comprar']
                                        if not any(word in text_prev for word in ignore):
                                            nome = lines[j]
                                            break
                                    
                                    # FILTRO INTELIGENTE: Só adiciona se o nome contiver o que o usuário busca
                                    if item_alvo.lower() in nome.lower():
                                        if not any(r['Produto'] == nome.title() for r in resultados_finais):
                                            resultados_finais.append({
                                                "Categoria": url.split('/')[-1].title(),
                                                "Produto": nome.title(), 
                                                "Preço": preco
                                            })
                        except:
                            continue # Pula categorias que falharem ou não tiverem o item

                    browser.close()
                    
                    # 4. EXIBIÇÃO DOS DADOS
                    if resultados_finais:
                        st.success(f"✅ Encontramos {len(resultados_finais)} correspondências para '{item_alvo}'!")
                        st.dataframe(resultados_finais, use_container_width=True)
                    else:
                        st.error(f"❌ O item '{item_alvo}' não foi encontrado em nenhuma das categorias mapeadas.")

            except Exception as e:
                st.error(f"Falha técnica no motor: {e}")
