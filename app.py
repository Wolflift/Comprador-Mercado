import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor (Informação externa necessária para o deploy)
os.system("playwright install chromium")

# Configuração da página conforme preferência de layout largo [Histórico]
st.set_page_config(page_title="Comparador de Mercado Pro", page_icon="🛒", layout="wide")

st.title("🛒 Engine de Busca Automática - Beltrame")
st.write("Digite o nome do produto e o robô fará a busca e extração dos preços automaticamente.")

# Entrada do item de busca via texto (substituindo a URL) [5]
item_busca = st.text_input("O que você deseja buscar?", placeholder="Ex: Cebola, Arroz 5kg, Feijão...")

if st.button("Executar Busca Profissional 🚀"):
    if item_busca:
        with st.spinner(f"O robô está procurando '{item_busca}' nas prateleiras..."):
            try:
                with sync_playwright() as p:
                    # Lançamento do navegador em modo invisível (headless) [6]
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0"
                    )
                    page = context.new_page()

                    # 1. PASSO DE SESSÃO: Resolve o pop-up de endereço na página inicial [Histórico]
                    # Automatiza a tarefa que humanos fariam manualmente [3, 7]
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded", timeout=60000)
                    
                    try:
                        # Busca o botão de confirmação de endereço usando texto flexível
                        btn_confirmar = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn_confirmar.is_visible(timeout=8000):
                            btn_confirmar.click()
                            page.wait_for_timeout(2000) # Pausa para processamento do clique
                    except:
                        # Segue se o pop-up não aparecer (estilo EAFP: pedir perdão se falhar) [1, 8]
                        pass

                    # 2. BUSCA DINÂMICA: Constrói a URL de busca automaticamente [3, 9]
                    query = urllib.parse.quote(item_busca.strip().lower())
                    url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                    page.goto(url_busca, wait_until="load", timeout=30000)
                    
                    # 3. TRATAMENTO DE TIMEOUT: Captura a falha sem interromper o sistema [1, 2]
                    try:
                        # Espera o seletor de preço (R$) carregar na tela
                        page.wait_for_selector("text=R$", timeout=10000)
                        page.wait_for_timeout(2000) # Tempo extra para renderização de todos os cards
                        
                        # Captura todo o conteúdo de texto da página [Histórico]
                        text_content = page.locator("body").inner_text()
                        # Manipulação de strings: remove espaços e divide em linhas [9-11]
                        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                        
                        produtos = []
                        
                        # 4. LÓGICA DE EXTRAÇÃO: Varre as linhas procurando preços e nomes [12, 13]
                        for i, line in enumerate(lines):
                            # Identifica se a linha contém o padrão de preço [14]
                            if 'R$' in line and any(c.isdigit() for c in line):
                                preco = line
                                nome = "Desconhecido"
                                
                                # Heurística: olha para as linhas anteriores (i-1) para achar o nome [12]
                                for j in range(i-1, -1, -1):
                                    text_prev = lines[j].lower()
                                    # Lista de palavras para ignorar na busca pelo nome [9]
                                    ignore_words = ['carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 'off', 'ver mais', 'comprar']
                                    if not any(word in text_prev for word in ignore_words):
                                        nome = lines[j]
                                        break
                                
                                # Validação para evitar nomes curtos demais ou duplicados [15, 16]
                                if len(nome) > 3:
                                    if not any(p['Produto'] == nome.title() for p in produtos):
                                        produtos.append({"Produto": nome.title(), "Preço": preco})
                        
                        if produtos:
                            st.success(f"✅ Sucesso! Encontramos {len(produtos)} resultados para '{item_busca}'.")
                            # Exibição dos dados em tabela interativa [17, 18]
                            st.dataframe(produtos, use_container_width=True)
                        else:
                            st.warning(f"O termo '{item_busca}' não retornou produtos válidos. Tente ser mais específico.")

                    except Exception:
                        # Trata o erro de Timeout caso o item não exista no mercado [1, 2]
                        st.error(f"❌ O item '{item_busca}' não foi encontrado ou a página demorou muito para carregar.")
                    
                    browser.close()
                        
            except Exception as e:
                # Erro crítico no motor de automação [2]
                st.error(f"Falha técnica no motor de busca: {e}")
    else:
        st.warning("Por favor, digite o nome de um produto antes de buscar.")
