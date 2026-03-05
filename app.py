import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras", layout="wide")
st.title("🛒 Engine V23 - Navegação e Sessão Real")

lista_txt = st.text_area("Sua Lista:", placeholder="Cebola\nCenoura\nBatata")

if st.button("Executar Busca Profissional 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Validando acesso e buscando produtos..."):
            try:
                with sync_playwright() as p:
                    # Lançamento com disfarce de navegador Chrome atualizado
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
                        viewport={'width': 1280, 'height': 800}
                    )
                    page = context.new_page()

                    # 1. PASSO CRÍTICO: ACESSO E BYPASS DO BLOQUEIO
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    
                    try:
                        # Clica no botão de confirmar loja visto no diagnóstico
                        btn = page.locator("button:has-text('Confirmar')")
                        if btn.is_visible(timeout=8000):
                            btn.click()
                            page.wait_for_timeout(2000)
                    except:
                        pass

                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # 2. USA A BARRA DE BUSCA (Mais estável que URL direta)
                            # Placeholder extraído da imagem: 'Leite, arroz, pão, vinho, frutas...'
                            campo = page.get_by_placeholder("Leite, arroz, pão, vinho, frutas...")
                            campo.fill(item)
                            page.keyboard.press("Enter")
                            
                            # 3. ESPERA O CONTEÚDO (Garante que o preço 'nasceu' na tela)
                            page.wait_for_selector("text=R$", timeout=15000)
                            page.wait_for_timeout(3000)

                            # 4. EXTRAÇÃO POR ESCOPO (Isolamento de Card)
                            dados = page.evaluate("""
                                () => {
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 400);
                                    return cards.length > 0 ? cards[0].innerText : null;
                                }
                            """)

                            if dados:
                                linhas = [l.strip() for l in dados.split('\n') if l.strip()]
                                p_enc, n_enc = None, "Item"
