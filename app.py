import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor do Streamlit [Histórico]
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema Beltrame Pro", page_icon="🛒", layout="wide")

# Mapeamento sistematizado das 10 URLs [Histórico]
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

st.title("🛒 Engine Beltrame - Extração com Filtro de Categorias")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Varredura Geral"):
        with st.spinner("Processando dados e aplicando filtros de limpeza..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # Resolve o popup de loja (Sistematização de tarefa repetitiva) [Histórico]
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
                            
                            # Rolagem para carregar itens dinâmicos (Lazy Loading) [Histórico]
                            for _ in range(5):
                                page.mouse.wheel(0, 2000)
                                page.wait_for_timeout(800)
                            
                            page.wait_for_selector("text=R$", timeout=10000)
                            text_content = page.locator("body").inner_text()
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    
                                    # Filtra metadados de preço (kg/un) [Histórico]
                                    if "kg" in line.lower() or "un" in line.lower():
                                        continue
                                    
                                    # Lógica de detecção de preço final (ignora preço 'De' em promoções) [Histórico]
                                    tem_preco_venda_depois = False
                                    for k in range(i + 1, min(i + 3, len(lines))):
                                        if 'R$' in lines[k] and not ("kg" in lines[k].lower()):
                                            tem_preco_venda_depois = True
                                            break
                                    if tem_preco_venda_depois: continue

                                    preco_final = line
                                    nome_real = "Desconhecido"
                                    
                                    # Busca o nome real subindo as linhas [Histórico]
                                    for j in range(i-1, i-6, -1):
                                        if j < 0: break
                                        txt = lines[j]
                                        txt_low = txt.lower()
                                        
                                        # LISTA DE RUÍDO ATUALIZADA (Frases para ignorar exatamente como escritas)
                                        ruido = [
                                            'carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 
                                            'off', 'ver mais', 'comprar', 'oferta', '%', 'desconto', 
                                            '360°', '360', 'presunto e peito de peru', 'íntimos', 
                                            'banho e higiene', 'peixes', 'frutos do mar', 'aves', 
                                            'frutas', 'peso', 'gramas', 'carnes bovinas', 'açúcares',
                                            'cafés, chás e achocolatados', 'açúcares e adoçantes',
                                            'óleos', 'azeites', 'sopas instantâneas', 'cremes prontos',
                                            'farináceos', 'massas', 'grãos, arrozes e feijões', 'snacks',
                                            'salgadinhos de milho', 'salgadinhos de batata', 
                                            'biscoitos salgados', 'biscoitos doces', 
                                            'geleias, doces, mel e cia', 'conservas de ovos',
                                            'conservas de legumes e vegetais', 'conservas de carnes',
                                            'conservas de peixes', 'molhos', 'molhos para massas',
                                            'molhos para saladas', 'temperos secos', 'temperos em pó',
                                            'condimentos', 'vinagres', 'bomboniere', 'leites em pó',
                                            'erva mate', 'frutas em calda', 'panetones e chocotones',
                                            'cereais, sucrilhos, granolas e cia', 'suplementos', 'pratos prontos'
                                        ]
                                        
                                        # Validação do nome: não pode estar na lista de ruído nem ser apenas números [6, 11]
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
                    st.success(f"✅ Base carregada com {len(base_temp)} produtos reais!")
            except Exception as e:
                st.error(f"Erro técnico na coleta: {e}")

# INTERFACE DE BUSCA LOCAL (Processamento em memória Python) [12, 13]
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 Pesquisar na base limpa:").strip().lower()
    
    if busca:
        resultados = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        if resultados:
            st.table(resultados)
        else:
            st.warning("Produto não encontrado na base extraída.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
else:
    st.info("A base está vazia. Inicie a extração no menu lateral para carregar os dados.")
