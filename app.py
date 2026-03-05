import os
import streamlit as st
from playwright.sync_api import sync_playwright

os.system("playwright install chromium")

st.set_page_config(page_title="Beltrame v9 - Fluxo Assertivo", page_icon="🛒", layout="wide")

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

def p_to_f(t): # Converte R$ para número real
    try: return float(t.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except: return 0.0

st.title("🛒 Engine Beltrame - Fluxo de Extração Estruturado")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Coleta Completa"):
        with st.spinner("Processando prateleiras... Isso pode levar alguns minutos."):
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
                            
                            # FLUXO 1: Carregamento Máximo (Ver Mais) [5, 9]
                            for _ in range(15): # Limite de 15 cliques para segurança
                                try:
                                    ver_mais = page.get_by_role("button", name="Ver mais", exact=False)
                                    if ver_mais.is_visible(timeout=3000):
                                        ver_mais.click()
                                        page.wait_for_timeout(1500)
                                    else: break
                                except: break

                            # FLUXO 2: Extração por Blocos (Tratamento de Variáveis) [3]
                            cards = page.locator("div.product-card, .item-produto, [class*='product']").all()
                            
                            for c in cards:
                                txt_bloco = c.inner_text()
                                linhas = [l.strip() for l in txt_bloco.split('\n') if l.strip()]
                                
                                precos_num = []
                                precos_orig = []
                                nome_final = "Desconhecido"
                                
                                # Lista de ruído exaustiva [Conversa]
                                ruido = [
                                    'carrinho', 'adicionar', 'lista', 'indisponível', 'off', 'ver mais', 'comprar', 'oferta', '%', 'desconto', '360°', 'unidade', 'kg', 'gramas', 'peso',
                                    'cafés, chás e achocolatados', 'açúcares e adoçantes', 'óleos', 'azeites', 'sopas instantâneas', 'cremes prontos', 'farináceos', 'massas', 'grãos, arrozes e feijões',
                                    'snacks', 'salgadinhos de milho', 'salgadinhos de batata', 'biscoitos salgados', 'biscoitos doces', 'geleias, doces, mel e cia', 'conservas de ovos',
                                    'conservas de legumes e vegetais', 'conservas de carnes', 'conservas de peixes', 'molhos', 'molhos para massas', 'molhos para saladas', 'temperos secos',
                                    'temperos em pó', 'condimentos', 'vinagres', 'bomboniere', 'leites em pó', 'erva mate', 'frutas em calda', 'cereais, sucrilhos, granolas e cia',
                                    'panetones e chocotones', 'suplementos', 'pratos prontos', 'presunto e peito de peru', 'íntimos', 'banho e higiene', 'peixes', 'frutos do mar', 'aves', 'frutas', 'carnes bovinas'
                                ]

                                for lin in linhas:
                                    # Lógica de Preço: captura e converte
                                    if 'R$' in lin and any(char.isdigit() for char in lin):
                                        if "kg" not in lin.lower() and "un" not in lin.lower():
                                            precos_num.append(p_to_f(lin))
                                            precos_orig.append(lin)
                                    # Lógica de Nome: Letras, sem R$ e sem ruído [7]
                                    elif any(char.isalpha() for char in lin) and 'R$' not in lin and len(lin) > 3:
                                        if not any(word == lin.lower() for word in ruido):
                                            nome_final = lin

                                # FLUXO 3: Atribuição Matemática Assertiva
                                if precos_num and nome_final != "Desconhecido":
                                    if len(precos_num) >= 2:
                                        v_max = max(precos_num)
                                        v_min = min(precos_num)
                                        p_cheio = f"R$ {v_max:.2f}".replace('.', ',')
                                        p_promo = f"R$ {v_min:.2f}".replace('.', ',')
                                    else:
                                        p_cheio = precos_orig
                                        p_promo = "-"

                                    base_temp.append({
                                        "Categoria": nome_cat,
                                        "Produto": nome_final.title(),
                                        "Preço Cheio": p_cheio,
                                        "Menor Valor": p_promo
                                    })
                        except: continue 

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Base carregada! {len(base_temp)} itens encontrados com sucesso.")
            except Exception as e:
                st.error(f"Erro técnico: {e}")

# Interface de busca local
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 Filtrar na base tratada:").strip().lower()
    if busca:
        res = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        st.table(res) if res else st.warning("Não encontrado.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
