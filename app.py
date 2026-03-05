import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema Pro Beltrame", page_icon="🛒", layout="wide")

# URLs mapeadas para a base de dados
CATEGORIAS = {
    "Promocões": "https://beltramesupermercados.com.br/promocoes",
    "Hortifruti": "https://beltramesupermercados.com.br/categorias/hortifruti",
    "Mercearia": "https://beltramesupermercados.com.br/categorias/mercearia",
    "Carnes": "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "Limpeza": "https://beltramesupermercados.com.br/categorias/limpeza"
}

st.title("🛒 Engine Beltrame - Base Local Ativa")

# Gerenciamento de memória local via Session State
if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Configurações")
    if st.button("🚀 Iniciar Extração Geral"):
        with st.spinner("Criando base local..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    # Mantém a sessão ativa entre as páginas
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # 1. PASSO CRÍTICO: Resolver o popup logo no início
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        # Tenta clicar no confirmar do popup de Camobi
                        btn = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn.is_visible(timeout=5000):
                            btn.click()
                            page.wait_for_timeout(2000)
                    except: pass

                    base_temp = []
                    for nome_cat, url in CATEGORIAS.items():
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=30000)
                            page.wait_for_selector("text=R$", timeout=15000)
                            
                            # SUA LÓGICA DE VARREDURA (Adaptada para loop)
                            text_content = page.locator("body").inner_text()
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    preco = line
                                    nome = "Desconhecido"
                                    # Olha para cima buscando o nome (sua heurística)
                                    for j in range(i-1, -1, -1):
                                        text_prev = lines[j].lower()
                                        ignore = ['carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 'off', 'ver mais', 'comprar']
                                        if not any(word in text_prev for word in ignore):
                                            nome = lines[j]
                                            break
                                    
                                    if len(nome) > 3:
                                        base_temp.append({"Categoria": nome_cat, "Produto": nome.title(), "Preço": preco})
                        except: continue 

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Base carregada: {len(base_temp)} itens encontrados!")
            except Exception as e:
                st.error(f"Erro na extração: {e}")

# INTERFACE DE BUSCA (PROCESSAMENTO LOCAL)
if st.session_state.base_produtos:
    st.subheader("🔎 Pesquisar na Base")
    busca = st.text_input("Digite o que procura:").strip().lower()
    
    if busca:
        # Filtro em memória usando strings Python
        resultados = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        if resultados:
            st.table(resultados)
        else:
            st.warning("Nenhum item com esse nome na base.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
else:
    st.info("A base está vazia. Clique em 'Iniciar Extração Geral' para carregar os dados.")
