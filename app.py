import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor do Streamlit
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema Pro Beltrame", page_icon="🛒", layout="wide")

# Mapeamento sistematizado das 10 URLs [Histórico]
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

st.title("🛒 Engine Beltrame - Extração de Produtos Real")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Extração Geral"):
        with st.spinner("Limpando prateleiras e organizando a base local..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # Resolve o popup de loja (Sistematização de tarefa repetitiva) [4]
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
                            page.goto(url, wait_until="domcontentloaded", timeout=40000)
                            page.wait_for_selector("text=R$", timeout=15000)
                            
                            text_content = page.locator("body").inner_text()
                            # Manipulação de strings: quebra o texto em linhas limpas [5-7]
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    preco = line
                                    nome_prod = "Desconhecido"
                                    
                                    # LÓGICA DE FILTRAGEM REFINADA (Sobe até 4 linhas) [Histórico]
                                    for j in range(i-1, i-5, -1):
                                        if j < 0: break
                                        text_prev = lines[j].lower()
                                        
                                        # LISTA DE PALAVRAS IGNORADAS ATUALIZADA (Categorias e Selos)
                                        ignore = [
                                            'carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 
                                            'off', 'ver mais', 'comprar', 'oferta', '%', 'desconto', 
                                            'unidade', 'kg', '360°', '360', 'presunto e peito de peru', 
                                            'íntimos', 'banho e higiene', 'peixes', 'frutos do mar'
                                        ]
                                        
                                        # Validação do nome: ignora se estiver na lista ou for apenas número
                                        if not any(word == text_prev for word in ignore) and len(text_prev) > 3:
                                            if not text_prev.replace('-','').replace('%','').isdigit():
                                                nome_prod = lines[j]
                                                break 
                                    
                                    if len(nome_prod) > 3 and nome_prod != "Desconhecido":
                                        base_temp.append({
                                            "Categoria": nome_cat, 
                                            "Produto": nome_prod.title(), 
                                            "Preço": preco
                                        })
                        except: continue 

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Base carregada com {len(base_temp)} itens!")
            except Exception as e:
                st.error(f"Erro técnico: {e}")

# INTERFACE DE BUSCA LOCAL (Processamento em memória Python) [8, 9]
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 O que deseja filtrar da base coletada? (Ex: Presunto, Arroz, Tilápia)").strip().lower()
    
    if busca:
        # Filtro de lista: busca o termo no nome do produto formatado [10, 11]
        resultados = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        if resultados:
            st.write(f"Encontrados **{len(resultados)}** resultados:")
            st.table(resultados)
        else:
            st.warning("Produto não encontrado na base extraída.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
else:
    st.info("A base está vazia. Inicie a extração no menu lateral.")
