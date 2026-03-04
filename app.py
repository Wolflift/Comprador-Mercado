import os
import streamlit as st
from playwright.sync_api import sync_playwright

os.system("playwright install chromium")

st.set_page_config(page_title="Comparador de Mercado", page_icon="🛒", layout="wide")

st.title("🛒 Extrator de Preços - Beltrame")
st.write("Cole o link de uma categoria do mercado para extrairmos os produtos em formato de tabela.")

url = st.text_input("Link do Mercado:")

if st.button("Extrair Produtos"):
    if url:
        with st.spinner("Lendo as prateleiras e anotando os preços com a nova lógica..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_selector("text=R$", timeout=15000)
                    
                    text_content = page.locator("body").inner_text()
                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                    
                    produtos_dict = {}
                    
                    for i, line in enumerate(lines):
                        if 'R$' in line and any(c.isdigit() for c in line):
                            preco = line
                            nome = None
                            
                            # O robô agora olha para as próximas 5 linhas ABAIXO do preço
                            for j in range(i + 1, min(i + 6, len(lines))):
                                next_line = lines[j].strip()
                                
                                # Se achar outro preço logo em seguida, o preço atual era o "riscado" (antigo). Ignoramos.
                                if 'R$' in next_line:
                                    break
                                    
                                # Ignora botões e etiquetas de desconto (como "Peso", "Unidade", "-26%")
                                ignore_list = ['peso', 'unidade', 'adicionar', 'comprar', 'oferta', 'off']
                                if next_line.lower() in ignore_list or next_line.startswith('-') or next_line.endswith('%'):
                                    continue
                                    
                                # Se passou nos filtros, é o nome verdadeiro do produto!
                                if len(next_line) > 3:
                                    nome = next_line
                                    break
                            
                            if nome:
                                # Salva no dicionário (isso também evita produtos duplicados)
                                produtos_dict[nome.title()] = preco
                    
                    browser.close()
                    
                    # Converte nosso dicionário para o formato da tabela
                    produtos = [{"Produto": k, "Preço": v} for k, v in produtos_dict.items()]
                    
                    if produtos:
                        st.success(f"✅ Sensacional! O robô anotou {len(produtos)} produtos corretamente desta vez.")
                        st.dataframe(produtos, use_container_width=True)
                    else:
                        st.warning("Não conseguimos identificar os produtos. O layout pode ser muito diferente.")
                        
            except Exception as e:
                st.error(f"❌ Ocorreu um erro na extração: {e}")
    else:
        st.warning("Por favor, cole um link antes de buscar.")
