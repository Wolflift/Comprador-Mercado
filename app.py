import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação forçada do navegador
os.system("playwright install chromium")

st.set_page_config(page_title="Minhas Compras", page_icon="🛒", layout="wide")
st.title("🛒 Lista de Compras - Versão Direta")

lista_texto = st.text_area("Sua Lista de Compras:", placeholder="Ex: Cebola\nArroz")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista_texto.split('\n') if i.strip()]
    if itens:
        with st.spinner("O robô está indo direto ao ponto, sem esperar papo furado..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    # User-agent atualizado para parecer um Chrome de desktop real
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
                    page = context.new_page()
                    
                    resultados = []
                    total = 0.0
                    
                    for item in itens:
                        try:
                            query = urllib.parse.quote(item)
                            url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            # AQUI A MÁGICA: Não esperamos mais o 'networkidle'
                            page.goto(url_busca, wait_until="domcontentloaded", timeout=60000)
                            
                            # Espera curta de 5 segundos só para o JavaScript dos preços renderizar
                            page.wait_for_timeout(5000)
                            
                            # Se não achar o R$ em 10s, ele pula pro próximo sem travar tudo
                            try:
                                page.wait_for_selector("text=R$", timeout=10000)
                            except:
                                resultados.append({"Item": item, "Status": "Não carregou preços", "Preço": "-"})
                                continue

                            corpo = page.locator("body").inner_text()
                            linhas = [l.strip() for l in corpo.split('\n') if l.strip()]
                            
                            achou = False
                            for i, linha in enumerate(linhas):
                                if 'R$' in linha and any(c.isdigit() for c in line):
                                    for j in range(i+1, min(i+10, len(linhas))):
                                        cand = lines[j]
                                        if 'R$' in cand or len(cand) < 3 or any(x in cand.lower() for x in ['oferta', 'off', '%', 'unidade', 'peso']):
                                            continue
                                        nome, preco = cand.title(), linha
                                        # Limpa o preço e soma
                                        val_str = "".join(filter(lambda x: x.isdigit() or x in ",.", preco)).replace('.', '').replace(',', '.')
                                        total += float(val_str)
                                        resultados.append({"Item": item, "Status": nome, "Preço": preco})
                                        achou = True
                                        break
                                if achou: break
                            if not achou: resultados.append({"Item": item, "Status": "Item não identificado", "Preço": "-"})
                        except:
                            resultados.append({"Item": item, "Status": "Erro na busca individual", "Preço": "-"})
                            
                    browser.close()
