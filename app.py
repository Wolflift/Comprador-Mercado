import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Beltrame Pro v11", page_icon="🛒", layout="wide")

# Mapeamento sistematizado das URLs [5]
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

# Função para converter R$ em número real para comparação [11]
def p_to_f(t):
    try: return float(t.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except: return 0.0

st.title("🛒 Engine Beltrame - Extração com Limpeza Refinada (v11)")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Controle")
    if st.button("🚀 Iniciar Varredura"):
        with st.spinner("Limpando ruídos e coletando dados reais..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    ctx = browser.new_context(user_agent="Mozilla/5.0")
                    page = ctx.new_page()

                    # Resolve popup inicial [Conversa]
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        btn = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn.is_visible(timeout=5000): btn.click()
                    except: pass

                    base_temp = []
                    for nome_cat, url in CATEGORIAS.items():
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=40000)
                            
                            # Rolagem para carregar mais itens [Conversa]
                            for _ in range(5):
                                page.mouse.wheel(0, 2000)
                                page.wait_for_timeout(1000)

                            page.wait_for_selector("text=R$", timeout=15000)
                            text_content = page.locator("body").inner_text()
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            i = 0
                            while i < len(lines):
                                line = lines[i]
                                # IDENTIFICAÇÃO DE PREÇO (Âncora de busca)
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    if "kg" in line.lower() or "un" in line.lower():
                                        i += 1
                                        continue
                                    
                                    # Lógica de agrupamento por vizinhança
                                    precos_bloco = [line]
                                    if i+1 < len(lines) and 'R$' in lines[i+1] and not any(x in lines[i+1].lower() for x in ["kg", "un"]):
                                        precos_bloco.append(lines[i+1])
                                        i += 1 
                                    
                                    # Define Preço Cheio (maior) e Menor Valor (menor)
                                    numeros = [p_to_f(p) for p in precos_bloco]
                                    p_cheio = precos_bloco[numeros.index(max(numeros))]
                                    p_promo = precos_bloco[numeros.index(min(numeros))] if len(numeros) > 1 else "-"
                                    
                                    # BUSCA PELO NOME COM FILTRO DE PALAVRAS GENÉRICAS ATUALIZADO
                                    nome_item = "Desconhecido"
                                    
                                    # LISTA DE RUÍDO EXPANDIDA (Categorias, marketing e genéricos) [2]
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

                                    for j in range(i-1, i-9, -1): # Sobe até 8 linhas buscando o nome
                                        if j < 0: break
                                        txt = lines[j]
                                        txt_low = txt.lower()
                                        
                                        # Validação: Letras, sem R$, sem ser ruído e tamanho mínimo
                                        if any(c.isalpha() for c in txt) and 'R$' not in txt and len(txt) > 3:
                                            # Verifica se o texto NÃO é uma palavra genérica da lista
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
                                i += 1
                        except:
                            i += 1
                            continue

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Sucesso! {len(base_temp)} itens capturados com filtros aplicados.")
            except Exception as e:
                st.error(f"Erro na extração: {e}")

# Interface de Busca Local sobre a massa de dados tratada [12]
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 O que deseja encontrar hoje?").strip().lower()
    if busca:
        res = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        st.table(res) if res else st.warning("Item não encontrado na base.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
