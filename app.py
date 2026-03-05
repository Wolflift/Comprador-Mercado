import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação obrigatória do navegador para automação [2]
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema Beltrame Pro v8", page_icon="🛒", layout="wide")

# Mapeamento das 10 categorias para coleta de fontes variadas [2, Histórico]
CATEGORIAS = {
    "Promoções": "https://beltramesupermercados.com.br/promocoes",
    "Mercearia": "https://beltramesupermercados.com.br/categorias/mercearia",
    "Carnes e Aves": "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "Hortifruti": "https://beltramesupermercados.com.br/categorias/hortifruti",
    "Bebidas": "https://beltramesupermercados.com.br/categorias/bebidas",
    "Limpeza": "https://beltramesupermercados.com.br/categorias/limpeza",
    "Higiene e Beleza": "https://beltramesupermercados.com.br/categorias/higiene-e-beleza",
    "Laticínios e Frios": "https://beltramesupermercados.com.br/categorias/laticinios-e-frios",
    "Peixes e Frutos do Mar": "https://beltramesupermercados.com.br/categorias/peixes-e-frutos-do-mar"
}

# Função para converter strings monetárias em números reais para comparação [5, 6]
def converter_para_numero(texto):
    try:
        return float(texto.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except:
        return 0.0

st.title("🛒 Engine Beltrame - Extração por Blocos de Produto")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Extração Assertiva"):
        with st.spinner("Analisando cada 'quadrado' de produto..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # Resolve popup de loja inicial para evitar bloqueio de preços [Histórico]
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
                            # Rolagem para carregar itens ocultos (Lazy Loading) [Histórico]
                            for _ in range(5):
                                page.mouse.wheel(0, 2000)
                                page.wait_for_timeout(800)
                            
                            # 1. IDENTIFICAÇÃO DOS BLOCOS (QUADRADOS)
                            # Usamos um seletor genérico que engloba o card do produto no site
                            product_cards = page.locator("div.product-card, .item-produto, [class*='product']").all()
                            
                            for card in product_cards:
                                # Captura o texto apenas de DENTRO deste quadrado específico
                                card_text = card.inner_text()
                                lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                                
                                precos_encontrados = []
                                nome_candidato = "Desconhecido"
                                
                                # LISTA DE FRASES NEGATIVADAS (Títulos e Lixo de Marketing) [Histórico]
                                ruido = [
                                    'carrinho', 'adicionar', 'lista', 'indisponível', 'off', 'ver mais', 'comprar', 'oferta', '%', 'desconto', '360°', '360', 'unidade', 'kg', 'gramas', 'peso',
                                    'cafés, chás e achocolatados', 'açúcares e adoçantes', 'óleos', 'azeites', 'sopas instantâneas', 'cremes prontos', 'farináceos', 'massas', 'grãos, arrozes e feijões',
                                    'snacks', 'salgadinhos de milho', 'salgadinhos de batata', 'biscoitos salgados', 'biscoitos doces', 'geleias, doces, mel e cia', 'conservas de ovos',
                                    'conservas de legumes e vegetais', 'conservas de carnes', 'conservas de peixes', 'molhos', 'molhos para massas', 'molhos para saladas', 'temperos secos',
                                    'temperos em pó', 'condimentos', 'vinagres', 'bomboniere', 'leites em pó', 'erva mate', 'frutas em calda', 'cereais, sucrilhos, granolas e cia',
                                    'panetones e chocotones', 'suplementos', 'pratos prontos', 'presunto e peito de peru', 'íntimos', 'banho e higiene', 'peixes', 'frutos do mar', 'aves', 'frutas', 'carnes bovinas'
                                ]

                                for line in lines:
                                    # Se a linha for um preço (R$), guarda para comparação numérica [5, 7]
                                    if 'R$' in line and any(c.isdigit() for c in line):
                                        if "kg" not in line.lower() and "un" not in line.lower():
                                            precos_encontrados.append(line)
                                    # Se a linha tiver letras e não for ruído/preço, é o NOME [8, 9]
                                    elif any(c.isalpha() for c in line) and len(line) > 3:
                                        if not any(word == line.lower() for word in ruido):
                                            nome_candidato = line

                                # 2. LÓGICA ASSERTIVA DE SEPARAÇÃO (Informação Tratada) [4, 10]
                                if precos_encontrados:
                                    numeros = [converter_para_numero(p) for p in precos_encontrados]
                                    
                                    if len(numeros) >= 2:
                                        # Se há dois preços no quadrado, o maior é o cheio e o menor a promo
                                        val_max = max(numeros)
                                        val_min = min(numeros)
                                        p_cheio = f"R$ {val_max:.2f}".replace('.', ',')
                                        p_promo = f"R$ {val_min:.2f}".replace('.', ',')
                                    else:
                                        # Se há só um preço, ele é o valor atual/cheio
                                        p_cheio = precos_encontrados
                                        p_promo = "-"

                                    if nome_candidato != "Desconhecido":
                                        base_temp.append({
                                            "Categoria": nome_cat,
                                            "Produto": nome_candidato.title(),
                                            "Preço Cheio": p_cheio,
                                            "Menor Valor": p_promo
                                        })
                        except: continue 

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success("✅ Base carregada com separação assertiva por blocos!")
            except Exception as e:
                st.error(f"Erro técnico: {e}")

# INTERFACE DE BUSCA SOBRE A BASE LOCAL (ETL Completo) [1, 11]
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 Buscar na lista tratada:").strip().lower()
    if busca:
        resultados = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        st.table(resultados) if resultados else st.warning("Não encontrado.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
