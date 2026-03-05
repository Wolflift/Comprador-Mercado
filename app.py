import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras Pro", layout="wide")
st.title("🛒 Engine V19 - Estabilidade de Sessão")

lista_txt = st.text_area("Sua Lista de Compras:", placeholder="Cebola\nArroz")

if st.button("Executar Busca Profissional 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Validando acesso e capturando preços..."):
            try:
                with sync_playwright() as p:
                    # Lançamento com disfarce de usuário real
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0",
                        viewport={'width': 1280, 'height': 800}
                    )
                    page = context.new_page()

                    # 1. PASSO DE ENTRADA: Resolve o pop-up de loja antes de qualquer busca
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    
                    try:
                        # Tenta localizar o botão azul visto na imagem image_abebbf.jpg
                        btn_confirmar = page.locator("button:has-text('Confirmar')")
                        if btn_confirmar.is_visible(timeout=8000):
                            btn_confirmar.click()
                            page.wait_for_timeout(2000)
                    except:
                        pass # Segue caso o pop-up não apareça ou já tenha sido resolvido por cookie

                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # 2. BUSCA INDIVIDUAL
                            query = urllib.parse.quote(item)
                            url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url_busca, wait_until="domcontentloaded", timeout=45000)
                            
                            # 3. VERIFICAÇÃO DE PREÇO: Aguarda o R$ aparecer para garantir que a prateleira carregou
                            page.wait_for_selector("text=R$", timeout=15000)
                            page.wait_for_timeout(3000) # Tempo para o Lazy Loading

                            # 4. EXTRAÇÃO POR ESCOPO (A lógica que você validou)
                            # Isolamos o primeiro 'card' de produto para evitar ruído de menus
                            dados_bloco = page.evaluate("""
                                () => {
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length > 50 && el.innerText.length < 400);
                                    return cards.length > 0 ? cards[0].innerText : null;
                                }
                            """)

                            if dados_bloco:
                                linhas = [l.strip() for l in dados_bloco.split('\n') if l.strip()]
                                nome_prod, preco_prod = "Item Encontrado", None

                                for i, linha in enumerate(linhas):
                                    if 'R$' in linha and any(c.isdigit() for c in linha):
                                        preco_prod = linha
                                        # Busca o nome num raio de 4 linhas vizinhas
                                        indices_vizinhos = [i-1, i-2, i+1, i+2]
                                        for idx in indices_vizinhos:
                                            if 0 <= idx < len(linhas):
                                                cand = linhas[idx]
                                                lixo
