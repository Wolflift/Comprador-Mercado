import os
import streamlit as st
from playwright.sync_api import sync_playwright


os.system("playwright install chromium")


Layout mais largo para caber a tabela

st.set_page_config(page_title="Comparador de Mercado", page_icon="🛒", layout="wide")


st.title("🛒 Extrator de Preços - Beltrame")
st.write("Cole o link de uma categoria do mercado para extrairmos os produtos em formato de tabela.")


url = st.text_input("Link do Mercado:")


if st.button("Extrair Produtos"):
if url:
with st.spinner("Lendo as prateleiras e anotando os preços... isso leva cerca de 20 segundos."):
try:
with sync_playwright() as p:
browser = p.chromium.launch(headless=True)
page = browser.new_page()


                page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Agora o robô só prossegue quando enxergar um "R$" na tela
                page.wait_for_selector("text=R$", timeout=15000)

                # Pega todo o texto escrito na tela do mercado
                text_content = page.locator("body").inner_text()
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]

                produtos = []

                # Varre as linhas procurando preços e nomes
                for i, line in enumerate(lines):
                    if 'R$' in line and any(c.isdigit() for c in line):
                        preco = line
                        nome = "Desconhecido"

                        # Olha para cima para achar o nome, ignorando lixo
                        for j in range(i-1, -1, -1):
                            text_prev = lines[j].lower()
                            ignore_words = ['carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 'off', 'ver mais', 'comprar']
                            if not any(word in text_prev for word in ignore_words):
                                nome = lines[j]
                                break

                        # Filtro para evitar linhas curtas e produtos duplicados
                        if len(nome) > 3:
                            if not any(p['Produto'] == nome.title() for p in produtos):
                                produtos.append({"Produto": nome.title(), "Preço": preco})

                browser.close()

                if produtos:
                    st.success(f"✅ Sensacional! O robô anotou {len(produtos)} produtos nesta página.")
                    # Transforma a nossa lista em uma tabela interativa!
                    st.dataframe(produtos, use_container_width=True)
                else:
                    st.warning("Não conseguimos identificar os produtos. O layout pode ser muito diferente.")

        except Exception as e:
            st.error(f"❌ Ocorreu um erro na extração: {e}")
else:
    st.warning("Por favor, cole um link antes de buscar.")
