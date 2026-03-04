import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

os.system("playwright install chromium")

st.set_page_config(page_title="Minhas Compras", page_icon="🛒", layout="wide")
st.title("🛒 Lista de Compras - Versão Diagnóstico")

lista_texto = st.text_area("Sua Lista de Compras:", placeholder="Ex: Cebola\nArroz")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista_texto.split('\n') if i.strip()]
    if itens:
        with st.spinner("O robô está em campo..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    # Disfarce completo de navegador humano
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0")
                    page = context.new_page()
                    
                    # PASSO 1: Entra na Home para setar cookies e ver se tem pop-up
                    page.goto("https://beltramesupermercados.com.br", wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(3000) # Espera pop-ups de carregamento
                    
                    resultados = []
                    total = 0.0
                    
                    for item in itens:
                        query = urllib.parse.quote(item)
                        url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                        page.goto(url_busca, wait_until="domcontentloaded", timeout=30000)
                        
                        # Espera os preços carregarem
                        try:
                            page.wait_for_selector("text=R$", timeout=10000)
                            page.mouse.wheel(0, 300) # Rolagem para ativar o site
                            
                            corpo = page.locator("body").inner_text()
                            linhas = [l.strip() for l in corpo.split('\n') if l.strip()]
                            
                            achou = False
                            for i, linha in enumerate(linhas):
                                if 'R$' in linha and any(c.isdigit() for c in linha):
                                    for j in range(i+1, min(i+8, len(linhas))):
                                        cand = linhas[j]
                                        if 'R$' in cand or len(cand) < 3 or any(x in cand.lower() for x in ['oferta', 'off', '%', 'unidade']):
                                            continue
                                        nome, preco = cand.title(), linha
                                        val = float("".join(filter(lambda x: x.isdigit() or x in ",.", preco)).replace('.', '').replace(',', '.'))
                                        total += val
                                        resultados.append({"Item": item, "Status": nome, "Preço": preco})
                                        achou = True
                                        break
                                if achou: break
                            if not achou: resultados.append({"Item": item, "Status": "Não identificado", "Preço": "-"})
                        except:
                            # Se falhar, tira um print para sabermos o motivo!
                            st.error(f"O robô não viu o preço de '{item}'. Veja abaixo o que ele está enxergando:")
                            page.screenshot(path="erro_visao.png")
                            st.image("erro_visao.png")
                            resultados.append({"Item": item, "Status": "Bloqueado/Esgotado", "Preço": "-"})
                            
                    browser.close()
                    st.success(f"✅ Total: **R$ {total:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(resultados)
            except Exception as e:
                st.error(f"Erro no motor: {e}")
