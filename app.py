import os
import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador conforme as necessidades de automação [6]
os.system("playwright install chromium")

st.set_page_config(page_title="Beltrame Pro v14", page_icon="🛒", layout="wide")

# 1. MAPEAMENTO DE FONTES VARIADAS (Excluindo a URL de Promoções conforme solicitado) [1]
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

# Função auxiliar para tratar variáveis numéricas (conversão para float) [7, 8]
def p_to_f(t):
    try:
        return float(t.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except:
        return 0.0

st.title("🛒 Engine Beltrame - Inteligência de Magnitude e Filtros")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Varredura"):
        with st.spinner("O robô está cruzando preços e aplicando regras de ouro..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    ctx = browser.new_context(user_agent="Mozilla/5.0")
                    page = ctx.new_page()

                    # Resolve popup de unidade (Sistematização de tarefa repetitiva) [2]
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        btn = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn.is_visible(timeout=5000): btn.click()
                    except: pass

                    base_temp = []
                    for nome_cat, url in CATEGORIAS.items():
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=40000)
                            for _ in range(5): 
                                page.mouse.wheel(0, 2000)
                                page.wait_for_timeout(1000)

                            page.wait_for_selector("text=R$", timeout=15000)
                            text_content = page.locator("body").inner_text()
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            i = 0
                            while i < len(lines):
                                line = lines[i]
                                # IDENTIFICAÇÃO DE PREÇO (Ponto de ancoragem) [9]
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    if "kg" in line.lower() or "un" in line.lower():
                                        i += 1
                                        continue
                                    
                                    # LÓGICA DE COLETA DE PREÇOS (Inteligência de Vizinhança)
                                    precos_vizinhança = [line]
                                    pula_proximo = False
                                    
                                    # Verifica se a próxima linha física também é um preço (Indicador de promoção)
                                    if i+1 < len(lines) and 'R$' in lines[i+1] and not any(x in lines[i+1].lower() for x in ["kg", "un"]):
                                        precos_vizinhança.append(lines[i+1])
                                        pula_proximo = True
                                    
                                    # CONVERSÃO E COMPARAÇÃO MATEMÁTICA (Magnitude) [3, 5]
                                    numeros = [p_to_f(p) for p in precos_vizinhança]
                                    
                                    if len(numeros) >= 2:
                                        # Maior valor é o preço cheio, menor valor é a promoção
                                        p_cheio = precos_vizinhança[numeros.index(max(numeros))]
                                        p_promo = precos_vizinhança[numeros.index(min(numeros))]
                                    else:
                                        p_cheio = precos_vizinhança
                                        p_promo = "-"

                                    # BUSCA PELO NOME DO PRODUTO (Refinamento de limpeza) [10, 11]
                                    nome_item = "Desconhecido"
                                    
                                    # LISTA DE RUÍDO ATUALIZADA (Incluindo Pratos Prontos)
                                    ruido = [
                                        'carrinho', 'adicionar', 'lista', 'indisponível', 'off', 'ver mais', 
                                        'comprar', 'oferta', '%', 'desconto', '360°', '360', 'unidade', 
                                        'kg', 'gramas', 'peso', 'mais', 'sucos', 'refrigerantes', 
                                        'bebidas', 'mercearia', 'carnes', 'aves', 'frutas', 'limpeza',
                                        'cafés, chás e achocolatados', 'açúcares e adoçantes', 'óleos', 
                                        'azeites', 'sopas instantâneas', 'cremes prontos', 'farináceos', 
                                        'massas', 'grãos, arrozes e feijões', 'snacks', 'bomboniere', 
                                        'salgadinhos', 'biscoitos', 'íntimos', 'banho', 'higiene',
                                        'pratos prontos' # Adicionado conforme solicitado
                                    ]

                                    for j in range(i-1, i-9, -1):
                                        if j < 0: break
                                        txt = lines[j]
                                        txt_low = txt.lower()
                                        
                                        # Regra: Deve ter letras, não ter R$, não ser ruído e ter tamanho mínimo [12]
                                        if any(c.isalpha() for c in txt) and 'R$' not in txt and len(txt) > 3:
                                            if not any(word == txt_low for word in ruido):
                                                nome_item = txt
                                                break
                                    
                                    if nome_item != "Desconhecido":
                                        base_temp.append({
                                            "Categoria": nome_cat,
                                            "Produto": nome_item.title(),
                                            "Preço Cheio": p_cheio,
                                            "Menor Valor": p_promo
                                        })
                                    
                                    if pula_proximo: i += 1 # Avança índice para evitar duplicidade na promoção
                                i += 1
                        except:
                            i += 1
                            continue

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Coleta finalizada: {len(base_temp)} itens organizados.")
            except Exception as e:
                st.error(f"Erro técnico: {e}")

# 2. ESTABILIDADE DE TABELAS (Tratamento de Variáveis com Pandas) [1, 13]
if st.session_state.base_produtos:
    st.divider()
    
    # Converte para DataFrame e garante que tudo seja string para o Streamlit/Arrow
    df = pd.DataFrame(st.session_state.base_produtos).astype(str)
    
    busca = st.text_input("🔍 O que deseja pesquisar na base local?").strip().lower()
    if busca:
        res = df[df['Produto'].str.lower().str.contains(busca)]
        st.table(res) if not res.empty else st.warning("Item não encontrado.")
    else:
        st.dataframe(df, use_container_width=True)
