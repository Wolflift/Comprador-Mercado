import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor do Streamlit
os.system("playwright install chromium")

st.set_page_config(page_title="Comparador Beltrame Pro", page_icon="🛒", layout="wide")

st.title("🛒 Engine de Busca por Categorias - Beltrame")
st.write("O robô irá percorrer as categorias mapeadas. O popup de unidade será confirmado automaticamente.")

# MAPEAMENTO DAS URLs (Sistematização conforme discutido anteriormente)
CATEGORIAS = [
    "https://beltramesupermercados.com.br/promocoes",
    "https://beltramesupermercados.com.br/categorias/mercearia",
    "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "https://beltramesupermercados.com.br/categorias/hortifruti",
    "https://beltramesupermercados.com.br/categorias/bebidas-alcoolicas",
    "https://beltramesupermercados.com.br/categorias/bebidas",
    "https://beltramesupermercados.com.br/categorias/laticinios-e-frios",
    "https://beltramesupermercados.com.br/categorias/higiene-e-beleza",
    "https://beltramesupermercados.com.br/categorias/limpeza",
    "https://beltramesupermercados.com.br/categorias/peixes-e-frutos-do-mar"
]

item_alvo = st.text_input("Qual item você deseja encontrar?", placeholder="Ex: cebola, arroz...")

if st.button("Executar Varredura Geral 🚀"):
    if not item_alvo:
        st.warning("Por favor, digite o nome de um item.")
    else:
        with st.spinner(f"O robô está procurando '{item_alvo}'..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    # O User-Agent ajuda a evitar bloqueios simulando um navegador real
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # 1. RESOLVER O POPUP DE UNIDADE (Passo essencial de sessão)
                    # Entra na home primeiro para confirmar a loja padrão
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    
                    try:
                        # Como Camobi já vem selecionado, apenas clicamos em Confirmar
                        # O seletor busca o botão pelo texto exato
                        btn_confirmar = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn_confirmar.is_visible(timeout=10000):
                            btn_confirmar.click()
                            st.toast("📍 Unidade confirmada automaticamente.")
                            page.wait_for_timeout(2000) # Pausa para o site salvar a escolha
                    except:
                        # "Erros nunca devem passar silenciosamente" [4], 
                        # mas aqui tratamos a ausência do popup como sucesso prévio.
                        pass

                    resultados_finais = []

                    # 2. LOOP DE AUTOMAÇÃO PELAS CATEGORIAS
                    for url in CATEGORIAS:
                        try:
                            page.goto(url, wait_until="load", timeout=30000)
                            
                            # Espera o texto R$ aparecer (indica que os preços carregaram)
                            page.wait_for_selector("text=R$", timeout=10000)
                            
                            text_content = page.locator("body").inner_text()
                            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                            
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    preco = line
                                    nome = "Desconhecido"
                                    
                                    for j in range(i-1, -1, -1):
                                        text_prev = lines[j].lower()
                                        ignore = ['carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 'off', 'ver mais', 'comprar']
                                        if not any(word in text_prev for word in ignore):
                                            nome = lines[j]
                                            break
                                    
                                    if item_alvo.lower() in nome.lower():
                                        if not any(r['Produto'] == nome.title() for r in resultados_finais):
                                            resultados_finais.append({
                                                "Seção": url.split('/')[-1].title(),
                                                "Produto": nome.title(), 
                                                "Preço": preco
                                            })
                        except:
                            continue # Pula para a próxima URL se esta falhar

                    browser.close()
                    
                    # 3. EXIBIÇÃO EM TABELA
                    if resultados_finais:
                        st.success(f"✅ Sucesso! Encontramos os seguintes resultados:")
                        st.dataframe(resultados_finais, use_container_width=True)
                    else:
                        st.error(f"❌ O item '{item_alvo}' não foi encontrado.")

            except Exception as e:
                st.error(f"Falha técnica: {e}")
