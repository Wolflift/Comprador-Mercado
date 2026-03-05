import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador conforme fontes de automação
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema Pro Beltrame v5", page_icon="🛒", layout="wide")

# Mapeamento das 10 URLs [Histórico]
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

st.title("🛒 Engine Beltrame - Inteligência de Preços (ETL)")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Varredura Inteligente"):
        with st.spinner("O robô está separando preços cheios de preços promocionais..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # Resolver popup inicial [Histórico]
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
                            for _ in range(5):
                                page.mouse.wheel(0, 2000)
                                page.wait_for_timeout(800)
                            
                            page.wait_for_selector("text=R$", timeout=10000)
                            text_content = page.locator("body").inner_text()
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            i = 0
                            while i < len(lines):
                                line = lines[i]
                                # Se encontrou um preço
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    if "kg" in line.lower() or "un" in line.lower():
                                        i += 1
                                        continue
                                    
                                    # LÓGICA DE DUPLA COLUNA: Verifica se o próximo também é preço
                                    preco_cheio = line
                                    preco_promo = "-"
                                    
                                    # Se a próxima linha também for preço, houve promoção detectada
                                    if i+1 < len(lines) and 'R$' in lines[i+1] and not ("kg" in lines[i+1].lower()):
                                        preco_promo = lines[i+1]
                                        i += 1 # Pula o preço promo para não reprocessá-lo
                                    
                                    nome_real = "Desconhecido"
                                    # Busca o nome subindo a partir do PRIMEIRO preço encontrado
                                    # Reduzimos a subida para não pegar títulos de seções distantes
                                    for j in range(i-1, i-6, -1):
                                        if j < 0: break
                                        txt_orig = lines[j]
                                        txt_low = txt_orig.lower()
                                        
                                        # LISTA DE RUÍDO [Conversa Anterior]
                                        ruido = [
                                            'carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 'off', 'ver mais', 'comprar', 'oferta', '%', 'desconto', '360°', '360', 'unidade', 'kg', 'gramas', 'peso',
                                            'cafés, chás e achocolatados', 'açúcares e adoçantes', 'óleos', 'azeites', 'sopas instantâneas', 'cremes prontos', 'farináceos', 'massas', 'grãos, arrozes e feijões',
                                            'snacks', 'salgadinhos de milho', 'salgadinhos de batata', 'biscoitos salgados', 'biscoitos doces', 'geleias, doces, mel e cia', 'conservas de ovos',
                                            'conservas de legumes e vegetais', 'conservas de carnes', 'conservas de peixes', 'molhos', 'molhos para massas', 'molhos para saladas', 'temperos secos',
                                            'temperos em pó', 'condimentos', 'vinagres', 'bomboniere', 'leites em pó', 'erva mate', 'frutas em calda', 'cereais, sucrilhos, granolas e cia',
                                            'panetones e chocotones', 'suplementos', 'pratos prontos', 'presunto e peito de peru', 'íntimos', 'banho e higiene', 'peixes', 'frutos do mar', 'aves', 'frutas', 'carnes bovinas'
                                        ]
                                        
                                        if not any(word == txt_low for word in ruido) and len(txt_orig) > 3:
                                            if not txt_orig.replace('-','').replace('%','').replace(',','').replace('.','').isdigit():
                                                nome_real = txt_orig
                                                break
                                    
                                    if nome_real != "Desconhecido":
                                        base_temp.append({
                                            "Categoria": nome_cat,
                                            "Produto": nome_real.title(),
                                            "Preço Cheio": preco_cheio,
                                            "Preço Promo": preco_promo
                                        })
                                i += 1
                        except: 
                            i += 1
                            continue 

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Base carregada com sucesso!")
            except Exception as e:
                st.error(f"Erro técnico: {e}")

# INTERFACE DE BUSCA LOCAL
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 Pesquisar na base tratada:").strip().lower()
    
    if busca:
        resultados = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        if resultados:
            st.table(resultados)
        else:
            st.warning("Produto não encontrado.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
else:
    st.info("Inicie a extração no menu lateral para carregar os dados estruturados.")
