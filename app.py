import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação do motor
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras", layout="wide")
st.title("🛒 Engine V20 - Busca Real")

lista_txt = st.text_area("Sua Lista:", placeholder="Cebola\nArroz")

if st.button("Executar Busca 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Limpando bloqueios e buscando..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
                        viewport={'width': 1280, 'height': 800}
                    )
                    page = context.new_page()

                    # 1. ACESSO E DESBLOQUEIO (Pop-up de Loja)
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    
                    try:
                        # Clica no botão 'Confirmar' do pop-up de loja
                        btn = page.locator("button:has-text('Confirmar')")
                        if btn.is_visible(timeout=8000):
                            btn.click()
                            page.wait_for_timeout(2000)
                    except:
                        pass

                    res, total = [], 0.0

                    for item in itens:
                        try:
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            page.goto(url, wait_until="load", timeout=60000)
                            page.wait_for_timeout(5000) # Tempo para os preços carregarem

                            # 2. EXTRAÇÃO POR CONTAINER
                            item_info = page.evaluate("""
                                () => {
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 400);
                                    return cards.length > 0 ? cards[0].innerText : null;
                                }
                            """)
                            
                            if item_info:
                                linhas = [l.strip() for l in item_info.split('\n') if l.strip()]
                                p_enc, n_enc = None, "Item"
                                
                                for i, l in enumerate(linhas):
                                    if 'R$' in l and any(c.isdigit() for c in l):
                                        p_enc = l
                                        # Procura o nome nas 4 linhas ao redor
                                        for n in [i+1, i+2, i-1, i-2]:
                                            if 0 <= n < len(linhas) and len(linhas[n]) > 3:
                                                n_enc = linhas[n]
                                                break
                                        break
                                
                                if p_enc:
                                    v = float("".join(filter(lambda x: x.isdigit() or x in ",.", p_enc)).replace('.', '').replace(',', '.'))
                                    total += v
                                    res.append({"Status": "✅", "Busca": item, "Produto": n_enc, "Preço": p_enc})
                                else:
                                    res.append({"Status": "❌", "Busca": item, "Produto": "Preço não lido", "Preço": "-"})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado", "Preço": "-"})
                        
                        except Exception:
                            res.append({"Status": "❌", "Busca": item, "Produto": "Timeout", "Preço": "-"})

                    browser.close()
                    st.success(f"✅ Total: **R$ {total:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Erro central: {e}")
