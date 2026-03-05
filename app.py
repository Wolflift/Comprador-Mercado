import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor do Streamlit
os.system("playwright install chromium")

# Configuração da página conforme o seu padrão
st.set_page_config(page_title="Comparador de Mercado", page_icon="🛒", layout="wide")

st.title("🛒 Engine de Busca Beltrame - Versão Pro")
st.write("Digite o nome do item para que o robô procure e extraia os preços automaticamente.")

# Entrada do produto (substituindo a URL manual)
item_busca = st.text_input("O que você deseja buscar?", placeholder="Ex: Arroz, Cenoura, Leite...")

if st.button("Executar Busca Inteligente 🚀"):
    if item_busca:
        with st.spinner(f"O robô está procurando '{item_busca}' nas prateleiras..."):
            try:
                with sync_playwright() as p:
                    # Lançamento do navegador [7]
                    browser = p.chromium.launch(headless=True)
                    # Disfarce de usuário real para evitar bloqueios [8]
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0"
                    )
                    page = context.new_page()

                    # 1. RESOLVER O POPUP DE ENDEREÇO (Crucial para carregar os preços)
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded", timeout=60000)
                    try:
                        # Tenta localizar o botão de confirmação de endereço
                        btn_confirmar = page.locator("button:has-text('Confirmar')")
                        if btn_confirmar.is_visible(timeout=8000):
                            btn_confirmar.click()
                            page.wait_for_timeout(2000)
                    except:
                        pass # Segue se o popup não aparecer

                    # 2. CONSTRUÇÃO DA URL DE BUSCA AUTOMÁTICA [2]
                    # O urllib.parse garante que nomes com espaços (ex: "arroz integral") funcionem na URL
                    query = urllib.parse.quote(item_busca)
                    url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                    page.goto(url_busca, wait_until="load", timeout=30000)
                    
                    # 3. EXTRAÇÃO (Sua lógica de varredura de linhas)
                    page.wait_for_selector("text=R$", timeout=15000)
                    
                    # Captura o texto bruto do corpo da página [3]
                    text_content = page.locator("body").inner_text()
                    # Transforma em lista de strings limpas [9, 10]
                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                    
                    produtos = []
                    
                    # Varre as linhas procurando preços e nomes usando sua heurística
                    for i, line in enumerate(lines):
                        if 'R$' in line and any(c.isdigit() for c in line):
                            preco = line
                            nome = "Desconhecido"
                            
                            # Busca o nome olhando para as linhas anteriores (i-1)
                            for j in range(i-1, -1, -1):
                                text_prev = lines[j].lower()
                                ignore_words = ['carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 'off', 'ver mais', 'comprar']
                                if not any(word in text_prev for word in ignore_words):
                                    nome = lines[j]
                                    break
                            
                            # Validação final do item [11]
                            if len(nome) > 3:
                                if not any(p['Produto'] == nome.title() for p in produtos):
                                    produtos.append({"Produto": nome.title(), "Preço": preco})
                    
                    browser.close()
                    
                    # 4. EXIBIÇÃO DOS RESULTADOS
                    if produtos:
                        st.success(f"✅ Sucesso! Encontramos {len(produtos)} resultados para sua busca.")
                        # Exibe em formato de tabela interativa (dataframe) [12]
                        st.dataframe(produtos, use_container_width=True)
                    else:
                        st.warning(f"Não encontramos o termo '{item_busca}' no site. Tente outro nome.")
                        
            except Exception as e:
                # Tratamento de erros para não travar a aplicação [11, 13]
                st.error(f"❌ Ocorreu um erro na extração: {e}")
    else:
        st.warning("Por favor, digite o nome de um produto antes de buscar.")
