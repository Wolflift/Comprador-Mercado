import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação do motor de navegação no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Comprador de Mercado", layout="wide")
st.title("🛒 Engine Final - Estabilidade Total")

lista_txt = st.text_area("Lista de Compras:", placeholder="Cebola\nArroz")

if st.button("Executar Busca 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Processando..."):
            try:
                with sync_playwright() as p:
                    # Lançamento com disfarce de usuário real
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"
                    )
                    page = context.new_page()

                    # 1. ACESSO INICIAL E BYPASS DO MODAL DE LOJA (image_abebbf.jpg)
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        # Tenta clicar no botão 'Confirmar' do modal de localização
                        btn_confirmar = page.get_by_role("button", name="Confirmar")
                        if btn_confirmar.is_visible(timeout=5000):
                            btn_confirmar.click()
                            page.wait_for_timeout(2000)
                    except:
                        # Se o modal não aparecer (já salvo em cookie), ele segue
                        pass

                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # 2. BUSCA INDIVIDUAL POR URL
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url, wait_until="load", timeout=30000)
                            
                            # 3. ESPERA PELO CONTEÚDO (R$ é o sinalizador visual da prateleira)
                            page.wait_for_selector("text=R$", timeout=10000)
                            page.wait_for_timeout(2000)

                            # 4. EXTRAÇÃO ROBUSTA VIA JAVASCRIPT (Isolamento de Card)
                            # Pega o texto de cada card para não misturar nomes e preços
                            card_text = page.evaluate("""
                                () => {
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 500);
                                    return cards.length > 0 ? cards[0].innerText : null;
                                }
                            """)

                            if card_text:
                                lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                                p_val, n_val = None, "Item não identificado"
                                
                                for i, line in enumerate(lines):
                                    if 'R$' in line and any(c.isdigit() for c in line):
                                        p_val = line
                                        # Procura o nome nas linhas vizinhas
                                        vizinhos = [i-1, i-2, i+1, i+2]
                                        for v_idx in vizinhos:
                                            if 0 <= v_idx < len(lines):
                                                cand = lines[v_idx]
                                                lixo = ['oferta', 'off', '%', 'unidade', 'kg', 'adicionar']
                                                if len(cand) > 3 and 'R$' not in cand and not any(w in cand.lower() for w in lixo):
                                                    n_val = cand
                                                    break
