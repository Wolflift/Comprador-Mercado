import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador
os.system("playwright install chromium")

st.set_page_config(page_title="Comprador Pro", layout="wide")
st.title("🛒 Engine V24 - Estabilidade Total")

lista_txt = st.text_area("Lista de Compras:", placeholder="Cebola\nArroz")

if st.button("Executar Busca 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Desbloqueando loja e buscando..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"
                    )
                    page = context.new_page()

                    # 1. ACESSO E BYPASS DO POP-UP (image_abebbf.jpg)
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        # Clica no botão 'Confirmar' para liberar os preços
                        btn = page.locator("button:has-text('Confirmar')")
                        if btn.is_visible(timeout=7000):
                            btn.click()
                            page.wait_for_timeout(2000)
                    except:
                        pass

                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # 2. BUSCA INDIVIDUAL
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url, wait_until="load", timeout=45000)
                            
                            # 3. ESPERA PELO PREÇO (R$)
                            page.wait_for_selector("text=R$", timeout=15000)
                            page.wait_for_timeout(3000)

                            # 4. EXTRAÇÃO POR CONTAINER (A lógica de sucesso)
                            # Pega apenas o card isolado para não misturar dados
                            card_text = page.evaluate("""
                                () => {
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 400);
                                    return cards.length > 0 ? cards[0].innerText : null;
                                }
                            """)

                            if card_text:
                                lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                                p_val, n_val = None, "Item"
                                
                                for i, line in enumerate(lines):
                                    if 'R$' in line and any(c.isdigit() for c in line):
                                        p_val = line
                                        # Busca o nome num raio de 4 linhas vizinhas
                                        v_indices = [i-1, i-2, i+1, i+2]
                                        for v_idx in v_indices:
                                            if 0 <= v_idx < len(lines):
                                                cand = lines[v_idx]
                                                lixo = ['oferta', 'off', '%', 'kg', 'unidade', 'adicionar']
                                                if len(cand) > 3 and 'R$' not in cand and not any(w in cand.lower() for w in lixo):
                                                    n_val = cand
                                                    break
                                        break
                                
                                if p_val:
                                    clean_p = "".join(filter(lambda x: x.isdigit() or x in ",.", p_val))
                                    total_geral += float(clean_p.replace('.', '').replace(',', '.'))
                                    res.append({"Status": "✅", "Busca": item, "Produto": n_val.title(), "Preço": p_val})
                                else:
                                    res.append({"Status": "❌", "Busca": item, "Produto": "Preço invisível", "Preço": "-"})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado", "Preço": "-"})
                        except:
                            res.append({"Status": "❌", "Busca": item, "Produto": "Timeout", "Preço": "-"})

                    browser.close()
                    st.success(f"✅ Total: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)
            except Exception as e:
                st.error(f"Erro no motor: {e}")
