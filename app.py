import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema ETL Beltrame Pro", page_icon="🛒", layout="wide")

# 1. MAPEAMENTO COMPLETO DAS 10 URLs (Sistematização conforme fontes [1])
CATEGORIAS = {
    "Promoções": "https://beltramesupermercados.com.br/promocoes",
    "Mercearia": "https://beltramesupermercados.com.br/categorias/mercearia",
    "Carnes e Aves": "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "Hortifruti": "https://beltramesupermercados.com.br/categorias/hortifruti",
    "Bebidas Alcoólicas": "https://beltramesupermercados.com.br/categorias/bebidas-alcoolicas",
    "Bebidas": "https://beltramesupermercados.com.br/categorias/bebidas",
    "Laticínios e Frios": "https://beltramesupermercados.com.br/categorias/laticinios-e-frios",
    "Higiene e Beleza": "https://beltramesupermercados.com.br/categorias/higiene-e-beleza",
    "Limpeza": "https://beltramesupermercados.com.br/categorias/limpeza",
    "Peixes e Frutos do Mar": "https://beltramesupermercados.com.br/categorias/peixes-e-frutos-do-mar"
}

st.title("🛒 Engine Beltrame - Base Geral (10 Seções)")

# Gerenciamento de memória local via Session State
if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Extração Geral (Todas URLs)"):
        with st.spinner("Percorrendo as 10 seções do mercado... isso pode levar 1 minuto."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # Resolver o popup de loja inicial (Camobi selecionado por padrão)
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        btn = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn.is_visible(timeout=5000):
                            btn.click()
                            page.wait_for_timeout(2000)
                    except: pass

                    base_temp = []
                    for nome_cat, url in CATEGORIAS.items():
                        try:
                            # Navega para cada uma das 10 URLs [2]
                            page.goto(url, wait_until="domcontentloaded", timeout=40000)
                            page.wait_for_selector("text=R$", timeout=15000)
                            
                            text_content = page.locator("body").inner_text()
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    preco = line
                                    nome_prod = "Desconhecido"
                                    
                                    # Busca o nome limpando o "lixo" de marketing [5]
                                    for j in range(i-1, -1, -1):
                                        text_prev = lines[j].lower()
                                        ignore = [
                                            'carrinho', 'adicionar', 'lista', 'indisponível', 
                                            'r$', 'off', 'ver mais', 'comprar', 'oferta', 
                                            '%', 'desconto', 'unidade', 'kg'
                                        ]
                                        
                                        # Validação robusta: ignora linhas de desconto/números [6]
                                        if not any(word in text_prev for word in ignore) and len(text_prev) > 3:
                                            if not text_prev.isdigit() and text_prev != '-':
                                                nome_prod = lines[j]
                                                break
                                    
                                    if len(nome_prod) > 3 and nome_prod != "Desconhecido":
                                        base_temp.append({
                                            "Categoria": nome_cat, 
                                            "Produto": nome_prod.title(), 
                                            "Preço": preco
                                        })
                        except: 
                            continue # Segue para o próximo link se um falhar (EAFP [7])

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Sucesso! {len(base_temp)} itens coletados nas 10 categorias.")
            except Exception as e:
                st.error(f"Erro técnico na extração: {e}")

# INTERFACE DE BUSCA (PROCESSAMENTO LOCAL SOBRE OS DADOS CARREGADOS)
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 O que você deseja filtrar da base carregada?").strip().lower()
    
    if busca:
        resultados = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        if resultados:
            st.write(f"Encontrados **{len(resultados)}** resultados:")
            st.table(resultados)
        else:
            st.warning("Nenhum item com esse nome nas seções extraídas.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
else:
    st.info("A base está vazia. Use o menu lateral para extrair os dados das 10 URLs.")
