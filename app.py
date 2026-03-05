import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação do navegador
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras", layout="wide")
st.title("🛒 Engine V17 - Diagnóstico por Imagem")

lista_txt = st.text_area("Itens:", placeholder="Cebola\nArroz")

if st.button("Buscar com Diagnóstico 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("O robô está em campo..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
                        viewport={'width': 1280, 'height': 800}
                    )
                    page = context.new_page()

                    # Validação de Cookies/Sessão
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                    
                    res, total = [], 0.0

                    for item in itens:
                        try:
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            # Carregamento da busca
                            page.goto(url, wait_until="load", timeout=60000)
                            page.wait_for_timeout(5000) # Tempo para o JS do mercado

                            # TENTA IDENTIFICAR O PREÇO
                            found = page.locator("text=R$").first
                            if found.is_visible():
                                # Extração Cirúrgica via JS
                                dados = page.evaluate("""
                                    () => {
                                        const card = Array.from(document.querySelectorAll('div'))
                                            .find(el => el.innerText.includes('R$') && el.innerText.length < 300);
                                        return card ? card.innerText : null;
                                    }
                                """)
                                
                                if dados:
                                    linhas = [l.strip() for l in dados.split('\n') if l.strip()]
                                    preco, nome = None, "Indefinido"
                                    for i, l in enumerate(linhas):
                                        if 'R$' in l:
                                            preco = l
                                            # Nome costuma estar perto do preço
                                            for n in [i+1, i+2, i-1, i-2]:
                                                if 0 <= n < len(linhas) and len(linhas[n]) > 3:
                                                    nome = linhas[n]
                                                    break
                                            break
                                    
                                    val = float("".join(filter(lambda x: x.isdigit() or x in ",.", preco)).replace('.', '').replace(',', '.'))
                                    total += val
                                    res.append({"Status": "✅", "Item": item, "Produto": nome, "Preço": preco})
                                else:
                                    res.append({"Status": "❌", "Item": item, "Produto": "Estrutura não lida", "Preço": "-"})
                            else:
                                # SE FALHAR, TIRA PRINT PARA NÓS VERMOS O QUE HOUVE
                                page.screenshot(path="erro_busca.png")
                                st.image("erro_busca.png", caption=f"O que o robô viu ao buscar: {item}")
                                res.append({"Status": "❌", "Item": item, "Produto": "Não visível na tela", "Preço": "-"})
                        
                        except Exception as e:
                            res.append({"Status": "❌", "Item": item, "Produto": f"Erro: {str(e)[:20]}", "Preço": "-"})

                    browser.close()
                    st.success(f"✅ Total: **R$ {total:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Falha no motor: {e}")
