import os
import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright

os.system("playwright install chromium")

st.set_page_config(page_title="Beltrame Pro v16", page_icon="🛒", layout="wide")

# 1. MAPEAMENTO DAS CATEGORIAS (Sem Promoções) [Conversa]
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

def limpar_valor(texto):
    try: return float(texto.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except: return 0.0

st.title("🛒 Engine Beltrame - Correção de Alinhamento (v16)")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Coleta Sem Erros"):
        with st.spinner("Sincronizando nomes e preços..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    ctx = browser.new_context(user_agent="Mozilla/5.0")
                    page = ctx.new_page()

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
                            ultimo_i_nome = -1 # Trava para evitar que um produto pegue o nome do anterior [Sistematização]
                            
                            while i < len(lines):
                                line = lines[i]
                                
                                # IDENTIFICAÇÃO DE PREÇO
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    if "kg" in line.lower() or "un" in line.lower():
                                        i += 1
                                        continue
                                    
                                    # Lógica de agrupamento (Magnitude) [Conversa]
                                    precos_bloco = [line]
                                    pula_proximo = False
                                    if i+1 < len(lines) and 'R$' in lines[i+1] and not any(x in lines[i+1].lower() for x in ["kg", "un"]):
                                        precos_bloco.append(lines[i+1])
                                        pula_proximo = True
                                    
                                    numeros = [limpar_valor(p) for p in precos_bloco]
                                    p_cheio = precos_bloco[numeros.index(max(numeros))]
                                    p_promo = precos_bloco[numeros.index(min(numeros))] if len(numeros) > 1 else "-"
                                    
                                    # BUSCA PELO NOME COM TRAVA DE SEGURANÇA
                                    nome_item = "Desconhecido"
                                    ruido = [
                                        'carrinho', 'adicionar', 'lista', 'indisponível', 'off', 'ver mais', 
                                        'comprar', 'oferta', '%', 'desconto', '360°', '360', 'unidade', 
                                        'kg', 'gramas', 'peso', 'mais', 'sucos', 'refrigerantes',
                                        'cafés, chás e achocolatados', 'açúcares e adoçantes', 'óleos', 
                                        'azeites', 'sopas instantâneas', 'cremes prontos', 'farináceos', 
                                        'massas', 'grãos, arrozes e feijões', 'snacks', 'bomboniere', 
                                        'salgadinhos', 'biscoitos', 'íntimos', 'banho', 'higiene', 'pratos prontos'
                                    ]

                                    # Só busca o nome se ele estiver ABAIXO do último nome processado
                                    for j in range(i-1, max(-1, ultimo_i_nome), -1):
                                        txt = lines[j]
                                        txt_low = txt.lower()
                                        if any(c.isalpha() for c in txt) and 'R$' not in txt and len(txt) > 3:
                                            if not any(word == txt_low for word in ruido):
                                                nome_item = txt
                                                ultimo_i_nome = j # Marca este índice como "usado" [Tratamento]
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
                        except: i += 1; continue

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Coleta finalizada com {len(base_temp)} itens alinhados!")
            except Exception as e:
                st.error(f"Erro: {e}")

# EXIBIÇÃO ESTÁVEL [Conversa]
if st.session_state.base_produtos:
    st.divider()
    df = pd.DataFrame(st.session_state.base_produtos).astype(str)
    busca = st.text_input("🔍 Pesquisar na base corrigida:").strip().lower()
    if busca:
        res = df[df['Produto'].str.lower().str.contains(busca)]
        st.table(res) if not res.empty else st.warning("Não encontrado.")
    else:
        st.dataframe(df, use_container_width=True)
