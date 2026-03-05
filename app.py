import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador [Histórico]
os.system("playwright install chromium")

st.set_page_config(page_title="Beltrame Pro v12", page_icon="🛒", layout="wide")

# Mapeamento sistematizado de categorias [2]
CATEGORIAS = {
    "Promoções": "https://beltramesupermercados.com.br/promocoes",
    "Mercearia": "https://beltramesupermercados.com.br/categorias/mercearia",
    "Carnes e Aves": "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "Hortifruti": "https://beltramesupermercados.com.br/categorias/hortifruti",
    "Bebidas": "https://beltramesupermercados.com.br/categorias/bebidas",
    "Limpeza": "https://beltramesupermercados.com.br/categorias/limpeza",
    "Higiene": "https://beltramesupermercados.com.br/categorias/higiene-e-beleza",
    "Laticínios": "https://beltramesupermercados.com.br/categorias/laticinios-e-frios",
    "Peixes": "https://beltramesupermercados.com.br/categorias/peixes-e-frutos-do-mar"
}

# Função para tratar variáveis numéricas (converte R$ para float) [7, 8]
def limpar_valor(texto):
    try:
        return float(texto.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except:
        return 0.0

st.title("🛒 Engine Beltrame - Validação de Preços e Promoções")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Controle")
    if st.button("🚀 Iniciar Coleta"):
        with st.spinner("O robô está aplicando as regras de magnitude nos preços..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    ctx = browser.new_context(user_agent="Mozilla/5.0")
                    page = ctx.new_page()

                    # Resolve popup de unidade (Sistematização) [5]
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        btn = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn.is_visible(timeout=5000): btn.click()
                    except: pass # EAFP [9]

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
                                # IDENTIFICAÇÃO DE PREÇO (Âncora)
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    # Ignora metadados de peso/unidade [Conversa]
                                    if "kg" in line.lower() or "un" in line.lower():
                                        i += 1
                                        continue
                                    
                                    # LÓGICA DE COLETA DE PREÇOS NO BLOCO
                                    precos_detectados = [line]
                                    
                                    # Verifica se a próxima linha é um preço promocional
                                    if i+1 < len(lines) and 'R$' in lines[i+1] and not any(x in lines[i+1].lower() for x in ["kg", "un"]):
                                        precos_detectados.append(lines[i+1])
                                        pula_proximo = True
                                    else:
                                        pula_proximo = False
                                    
                                    # CONVERSÃO E COMPARAÇÃO DE MAGNITUDE
                                    valores_num = [limpar_valor(p) for p in precos_detectados]
                                    
                                    if len(valores_num) >= 2:
                                        # Se há dois valores, o MAIOR é o cheio e o MENOR é o promo
                                        p_cheio = precos_detectados[valores_num.index(max(valores_num))]
                                        p_promo = precos_detectados[valores_num.index(min(valores_num))]
                                    else:
                                        # Se há apenas um valor, ele é o preço cheio
                                        p_cheio = precos_detectados
                                        p_promo = "-"

                                    # BUSCA PELO NOME (Sobe até 8 linhas ignorando ruído) [Conversa]
                                    nome_final = "Desconhecido"
                                    ruido = [
                                        'carrinho', 'adicionar', 'lista', 'indisponível', 'off', 'ver mais', 
                                        'comprar', 'oferta', '%', 'desconto', '360°', '360', 'unidade', 
                                        'kg', 'gramas', 'peso', 'mais', 'sucos', 'refrigerantes', 
                                        'bebidas', 'mercearia', 'carnes', 'aves', 'frutas', 'limpeza',
                                        'cafés, chás e achocolatados', 'açúcares e adoçantes', 'óleos', 
                                        'azeites', 'sopas instantâneas', 'cremes prontos', 'farináceos', 
                                        'massas', 'grãos, arrozes e feijões', 'snacks', 'bomboniere', 
                                        'salgadinhos', 'biscoitos', 'íntimos', 'banho', 'higiene'
                                    ]

                                    for j in range(i-1, i-9, -1):
                                        if j < 0: break
                                        txt = lines[j]
                                        txt_low = txt.lower()
                                        
                                        # Regra: Nome deve ter letras e não estar na lista de ruído exato
                                        if any(c.isalpha() for c in txt) and 'R$' not in txt and len(txt) > 3:
                                            if not any(word == txt_low for word in ruido):
                                                nome_final = txt
                                                break
                                    
                                    if nome_final != "Desconhecido":
                                        base_temp.append({
                                            "Categoria": nome_cat,
                                            "Produto": nome_final.title(),
                                            "Preço Cheio": p_cheio,
                                            "Menor Valor": p_promo
                                        })
                                    
                                    if pula_proximo: i += 1 # Avança para não ler o preço promo como novo item
                                i += 1
                        except:
                            i += 1
                            continue

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Sucesso! {len(base_temp)} itens organizados por magnitude.")
            except Exception as e:
                st.error(f"Erro na extração: {e}")

# Interface de busca sobre a base tratada [5]
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 O que deseja pesquisar?").strip().lower()
    if busca:
        res = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        st.table(res) if res else st.warning("Produto não encontrado.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
