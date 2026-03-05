import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema ETL Beltrame Pro", page_icon="🛒", layout="wide")

# Mapeamento das 10 URLs fornecidas [Histórico]
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

st.title("🛒 Engine Beltrame - Inteligência em Promoções")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Extração Geral"):
        with st.spinner("Limpando prateleiras e processando promoções..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # Resolver o popup de loja inicial [Histórico]
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
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    
                                    # --- NOVA LÓGICA PARA PROMOÇÕES ---
                                    # Verifica se há outro preço nas próximas 3 linhas (indicando que este é o valor "DE")
                                    tem_outro_preco_depois = False
                                    for k in range(i + 1, min(i + 4, len(lines))):
                                        if 'R$' in lines[k] and any(c.isdigit() for c in lines[k]):
                                            tem_outro_preco_depois = True
                                            break
                                    
                                    if tem_outro_preco_depois:
                                        continue # Ignora este valor, pois ele é apenas o preço original (caro)

                                    # Se não houver outro preço à frente, este é o preço final (com desconto)
                                    preco = line
                                    nome_prod = "Desconhecido"
                                    
                                    # Busca o nome olhando para cima (subindo até 4 linhas)
                                    for j in range(i-1, i-5, -1):
                                        if j < 0: break
                                        text_prev = lines[j].lower()
                                        
                                        # Lista negra expandida (Cabeçalhos e Marketing) [Histórico]
                                        ignore = [
                                            'carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 
                                            'off', 'ver mais', 'comprar', 'oferta', '%', 'desconto', 
                                            'unidade', 'kg', '360°', '360', 'presunto e peito de peru', 
                                            'íntimos', 'banho e higiene', 'peixes', 'frutos do mar',
                                            'carnes bovinas', 'aves', 'frutas', 'peso', 'gramas'
                                        ]
                                        
                                        # Validação do nome
                                        if not any(word == text_prev for word in ignore) and len(text_prev) > 3:
                                            # Garante que não é um número/porcentagem solto
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
                    st.success(f"✅ Base carregada com {len(base_temp)} itens reais!")
            except Exception as e:
                st.error(f"Erro técnico: {e}")

# INTERFACE DE BUSCA LOCAL [Histórico]
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 Pesquise na base limpa (Ex: Presunto, Papel, Tilápia):").strip().lower()
    
    if busca:
        resultados = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        if resultados:
            st.table(resultados)
        else:
            st.warning("Produto não encontrado.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
else:
    st.info("A base está vazia. Inicie a extração no menu lateral.")
