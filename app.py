import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor [9]
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema ETL Beltrame", page_icon="🚀", layout="wide")

# 1. MAPEAMENTO DAS CATEGORIAS (Sistematização de dados) [7]
CATEGORIAS = {
    "Promocões": "https://beltramesupermercados.com.br/promocoes",
    "Mercearia": "https://beltramesupermercados.com.br/categorias/mercearia",
    "Carnes": "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "Hortifruti": "https://beltramesupermercados.com.br/categorias/hortifruti",
    "Bebidas": "https://beltramesupermercados.com.br/categorias/bebidas",
    "Limpeza": "https://beltramesupermercados.com.br/categorias/limpeza"
}

st.title("🛒 Engine Beltrame - Extração e Busca Local")
st.info("Passo 1: Extraia os dados das prateleiras. Passo 2: Busque o que desejar instantaneamente.")

# Inicializa a base de dados na sessão do Streamlit se não existir [5]
if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

# --- INTERFACE DE EXTRAÇÃO ---
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Extração Geral (ETL)"):
        with st.spinner("Conectando ao mercado e criando base local..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # Resolvendo o Popup de Loja Inicial (Apenas uma vez) [8]
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        btn_confirmar = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn_confirmar.is_visible(timeout=8000):
                            btn_confirmar.click()
                            page.wait_for_timeout(2000)
                    except:
                        pass

                    base_temporaria = []
                    
                    # Loop de automação pelas categorias mapeadas [10]
                    for nome_cat, url in CATEGORIAS.items():
                        try:
                            page.goto(url, wait_until="load", timeout=30000)
                            page.wait_for_selector("text=R$", timeout=10000)
                            
                            text_content = page.locator("body").inner_text()
                            lines = [line.strip() for line in text_content.split('\n') if line.strip()] [11]
                            
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    preco = line
                                    nome_prod = "Desconhecido"
                                    
                                    # Busca o nome olhando para as linhas vizinhas [12]
                                    for j in range(i-1, -1, -1):
                                        text_prev = lines[j].lower()
                                        ignore = ['carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 'off', 'ver mais', 'comprar']
                                        if not any(word in text_prev for word in ignore):
                                            nome_prod = lines[j]
                                            break
                                    
                                    if len(nome_prod) > 3:
                                        base_temporaria.append({
                                            "Categoria": nome_cat,
                                            "Produto": nome_prod.title(),
                                            "Preço": preco
                                        })
                        except:
                            continue 

                    st.session_state.base_produtos = base_temporaria
                    browser.close()
                    st.success(f"Base carregada com {len(base_temporaria)} itens!")
            except Exception as e:
                st.error(f"Erro no motor: {e}")

# --- INTERFACE DE BUSCA (PROCESSAMENTO LOCAL) ---
if st.session_state.base_produtos:
    st.subheader("🔎 Pesquisar na Base Local")
    termo_busca = st.text_input("Digite o item que deseja filtrar (ex: cebola, sabão):").strip().lower()

    if termo_busca:
        # Filtro inteligente usando manipulação de strings Python [13, 14]
        resultados = [item for item in st.session_state.base_produtos if termo_busca in item['Produto'].lower()]
        
        if resultados:
            st.write(f"Encontrados **{len(resultados)}** resultados para sua busca:")
            st.table(resultados)
        else:
            st.warning("Nenhum item com esse nome na base coletada.")
    else:
        st.write("Digite um termo para filtrar a base de dados acima.")
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
else:
    st.warning("A base de dados está vazia. Clique no botão 'Iniciar Extração Geral' no menu lateral para começar.")
