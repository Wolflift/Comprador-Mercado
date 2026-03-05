import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema Beltrame v3", page_icon="🛒", layout="wide")

CATEGORIAS = {
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

st.title("🛒 Engine Beltrame - Inteligência Anti-Ruído")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Controle de Coleta")
    if st.button("🚀 Iniciar Varredura Completa"):
        with st.spinner("O robô está descendo as prateleiras e limpando os dados..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # 1. RESOLVER POPUP (Sistematização de tarefa [5])
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        btn = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn.is_visible(timeout=5000):
                            btn.click()
                            page.wait_for_timeout(1500)
                    except: pass

                    base_temp = []
                    for nome_cat, url in CATEGORIAS.items():
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=40000)
                            
                            # 2. ROLAGEM AUTOMÁTICA: Para carregar todos os itens (Lazy Loading)
                            for _ in range(5):
                                page.mouse.wheel(0, 2000)
                                page.wait_for_timeout(800)
                            
                            page.wait_for_selector("text=R$", timeout=10000)
                            text_content = page.locator("body").inner_text()
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            # 3. LÓGICA DE EXTRAÇÃO POR BLOCOS (Tratamento de Variáveis [1])
                            for i, line in enumerate(lines):
                                # Identifica uma linha de preço
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    
                                    # Se a linha contém "kg" ou "unidade" no texto do preço, é metadado
                                    if "kg" in line.lower() or "un" in line.lower():
                                        continue
                                    
                                    # Verifica se o preço seguinte está muito próximo (Promoção "De/Por")
                                    # Se houver outro preço logo abaixo, este atual é o preço 'caro' (antigo)
                                    tem_preco_venda_depois = False
                                    for k in range(i + 1, min(i + 3, len(lines))):
                                        if 'R$' in lines[k] and not ("kg" in lines[k].lower()):
                                            tem_preco_venda_depois = True
                                            break
                                    
                                    if tem_preco_venda_depois:
                                        continue

                                    # Se chegou aqui, este é o PREÇO FINAL de compra
                                    preco_final = line
                                    nome_real = "Desconhecido"
                                    
                                    # Busca o nome subindo, mas IGNORA selos de marketing e categorias
                                    for j in range(i-1, i-6, -1):
                                        if j < 0: break
                                        txt = lines[j]
                                        txt_low = txt.lower()
                                        
                                        # Lista de Ruído (Sistematização de filtros [5])
                                        ruido = [
                                            'carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 
                                            'off', 'ver mais', 'comprar', 'oferta', '%', 'desconto', 
                                            '360°', '360', 'presunto e peito de peru', 'íntimos', 
                                            'banho e higiene', 'peixes', 'frutos do mar', 'aves', 
                                            'frutas', 'peso', 'gramas', 'carnes bovinas', 'açúcares'
                                        ]
                                        
                                        # Se não for ruído e tiver tamanho de nome, capturamos
                                        if not any(word == txt_low for word in ruido) and len(txt) > 3:
                                            if not txt.replace('-','').replace('%','').isdigit():
                                                nome_real = txt
                                                break 
                                    
                                    if nome_real != "Desconhecido":
                                        base_temp.append({
                                            "Categoria": nome_cat, 
                                            "Produto": nome_real.title(), 
                                            "Preço": preco_final
                                        })
                        except: continue 

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Base consolidada com {len(base_temp)} itens!")
            except Exception as e:
                st.error(f"Erro técnico na coleta: {e}")

# INTERFACE DE BUSCA (Processamento Local Instantâneo [5])
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 O que você quer comprar hoje?").strip().lower()
    
    if busca:
        resultados = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        if resultados:
            st.table(resultados)
        else:
            st.warning("Item não encontrado na base extraída.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
