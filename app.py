import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras", layout="wide")
st.title("🛒 Engine V18 - Bypass de Loja (Beltrame)")

lista_txt = st.text_area("Sua Lista:", placeholder="Cebola\nCenoura")

if st.button("Executar Busca com Bypass 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Desbloqueando acesso à loja..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
                        viewport={'width': 1280, 'height': 800}
                    )
                    page = context.new_page()

                    # 1. ACESSO INICIAL E BYPASS DO POP-UP
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    
                    try:
                        # Procura o botão azul de 'Confirmar' do pop-up visto no diagnóstico
                        # Se o pop-up aparecer, o robô clica nele em até 10 segundos
                        btn_confirmar = page.locator("button:has-text('Confirmar')")
                        if btn_confirmar.is_visible(timeout=10000):
                            btn_confirmar.click()
                            page.wait_for_timeout(2000)
                    except:
                        pass # Segue se o pop-up não aparecer

                    res, total = [], 0.0

                    for item in itens:
                        try:
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            page.goto(url, wait_until="load", timeout=60000)
                            page.wait_for_timeout(4000) 

                            # 2. CAPTURA DOS DADOS (Agora com a tela desbloqueada)
                            dados = page.evaluate("""
                                () => {
                                    const card = Array.from(document.querySelectorAll('div, section, article'))
                                        .find(el => el.innerText.includes('R$') && el.innerText.length < 400);
                                    return card ? card.innerText : null;
                                }
                            """)
                            
                            if dados:
                                linhas = [l.strip() for l in dados.split('\n') if l.strip()]
                                preco_enc, nome_enc = None, "Item"
                                
                                for i, l in enumerate(linhas):
                                    if 'R$' in l and any(c.isdigit() for c in l):
                                        preco_enc = l
                                        # Pega o nome nas vizinhas (cima ou baixo)
                                        for n in [i+1, i+2, i-1, i-2]:
                                            if 0 <= n < len(linhas) and len(linhas[n]) > 3 and 'R$' not in linhas[n]:
                                                nome_enc = linhas[n]
                                                break
                                        break
                                
                                if preco_enc:
                                    val = float("".join(filter(lambda x: x.isdigit() or x in ",.", preco_enc)).replace('.', '').replace(',', '.'))
                                    total += val
                                    res.append({"Status": "✅", "Busca": item, "Produto": nome_enc, "Preço": preco_enc})
                                else:
                                    res.append({"Status": "❌", "Busca": item, "Produto": "Preço não visível", "Preço": "-"})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado", "Preço": "-"})
                        
                        except Exception:
                            res.append({"Status": "❌", "Busca": item, "Produto": "Erro no item", "Preço": "-"})

                    browser.close()
                    st.success(f"✅ Total do Rancho: **R$ {total:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Falha no motor principal: {e}")
