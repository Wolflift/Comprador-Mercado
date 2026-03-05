import os
import streamlit as st
import pandas as pd # Essencial para tratar tabelas e evitar o erro Arrow [Conversa]
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor [3]
os.system("playwright install chromium")

st.set_page_config(page_title="Beltrame Pro v15", page_icon="🛒", layout="wide")

# 1. MAPEAMENTO DE CATEGORIAS (URL de Promoções excluída conforme solicitado) [Conversa]
CATEGORIAS = {
    "Mercearia": "https://beltramesupermercados.com.br/categorias/mercearia",
    "Carnes e Aves": "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "Hortifruti": "https://beltramesupermercados.com.br/categorias/hortifruti",
    "Bebidas": "https://beltramesupermercados.com.br/categorias/bebidas",
    "Laticínios e Frios": "https://beltramesupermercados.com.br/categorias/laticinios-e-frios",
    "Higiene e Beleza": "https://beltramesupermercados.com.br/categorias/higiene-e-beleza",
    "Limpeza": "https://beltramesupermercados.com.br/categorias/limpeza",
    "Peixes e Frutos do Mar": "https://beltramesupermercados.com.br/categorias/peixes-e-frutos-do-mar"
}

# Função para tratar variáveis numéricas (converte R$ para número real) [1]
def p_to_f(t):
    try: return float(t.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except: return 0.0

st.title("🛒 Engine Beltrame - Filtro de Títulos e Magnitude")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Varredura"):
        with st.spinner("Limpando ruídos e organizando prateleiras..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    ctx = browser.new_context(user_agent="Mozilla/5.0")
                    page = ctx.new_page()

                    # Resolve popup inicial de unidade [Conversa]
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        btn = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn.is_visible(timeout=5000): btn.click()
                    except: pass

                    base_temp = []
                    for nome_cat, url in CATEGORIAS.items():
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=40000)
                            for _ in range(5): # Rolagem para carregamento dinâmico
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
                                    
                                    # Lógica de agrupamento por vizinhança (Promoção)
                                    precos_bloco = [line]
                                    pula_proximo = False
                                    if i+1 < len(lines) and 'R$' in lines[i+1] and not any(x in lines[i+1].lower() for x in ["kg", "un"]):
                                        precos_bloco.append(lines[i+1])
                                        pula_proximo = True
                                    
                                    # MAGNITUDE: Define Preço Cheio (maior) e Menor Valor (menor) [Conversa]
                                    numeros = [p_to_f(p) for p in precos_bloco]
                                    p_cheio = precos_bloco[numeros.index(max(numeros))]
                                    p_promo = precos_bloco[numeros.index(min(numeros))] if len(numeros) > 1 else "-"
                                    
                                    # BUSCA PELO NOME COM FILTRO EXATO DE FRASES NEGATIVADAS
                                    nome_item = "Desconhecido"
                                    
                                    # LISTA DE RUÍDO ATUALIZADA (Exatamente conforme solicitado) [Conversa]
                                    ruido = [
                                        'carrinho', 'adicionar', 'lista', 'indisponível', 'off', 'ver mais', 'comprar', 'oferta', '%', 'desconto', '360°', 'unidade', 'kg', 'gramas', 'peso',
                                        'cafés, chás e achocolatados', 'açúcares e adoçantes', 'óleos', 'azeites', 'sopas instantâneas', 'cremes prontos', 'farináceos', 'massas', 'grãos, arrozes e feijões',
                                        'snacks', 'salgadinhos de milho', 'salgadinhos de batata', 'biscoitos salgados', 'biscoitos doces', 'geleias, doces, mel e cia', 'conservas de ovos',
                                        'conservas de legumes e vegetais', 'conservas de carnes', 'conservas de peixes', 'molhos', 'molhos para massas', 'molhos para saladas', 'temperos secos',
                                        'temperos em pó', 'condimentos', 'vinagres', 'bomboniere', 'leites em pó', 'erva mate', 'frutas em calda', 'cereais, sucrilhos, granolas e cia',
                                        'panetones e chocotones', 'suplementos', 'pratos prontos', 'mais', 'sucos', 'refrigerantes'
                                    ]

                                    for j in range(i-1, i-9, -1): # Sobe 8 linhas buscando o nome alfabético [Conversa]
                                        txt = lines[j]
                                        txt_low = txt.lower()
                                        
                                        # Validação do Nome: Letras, sem R$, sem ser ruído e tamanho mínimo [4]
                                        if any(c.isalpha() for c in txt) and 'R$' not in txt and len(txt) > 3:
                                            # Verifica se o texto NÃO corresponde a nenhum ruído exato
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
                                    if pula_proximo: i += 1 
                                i += 1
                        except:
                            i += 1
                            continue

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Base carregada! {len(base_temp)} itens encontrados.")
            except Exception as e:
                st.error(f"Erro na extração: {e}")

# Interface de Busca Local com Estabilidade Arrow [Conversa]
if st.session_state.base_produtos:
    st.divider()
    # Converte para DataFrame e força string para evitar erros de tipagem [Conversa]
    df = pd.DataFrame(st.session_state.base_produtos).astype(str)
    
    busca = st.text_input("🔍 Pesquisar na base tratada:").strip().lower()
    if busca:
        res = df[df['Produto'].str.lower().str.contains(busca)]
        st.table(res) if not res.empty else st.warning("Não encontrado.")
    else:
        st.dataframe(df, use_container_width=True)
