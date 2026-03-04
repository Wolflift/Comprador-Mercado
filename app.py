import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instala o navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Rancho da Mãe", layout="wide")
st.title("🛒 Lista de Compras Inteligente - Beltrame")

lista = st.text_area("Sua Lista:", placeholder="Ex: Cebola\nArroz")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista.split('\n') if i.strip()]
    if itens:
        with st.spinner("O robô está procurando item por item..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    res, total = [], 0.0
                    
                    for item in itens:
                        try:
                            # 1. Vai direto para o link de busca
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url, wait_until="domcontentloaded", timeout=60000)
                            
                            # 2. ESPERA CRÍTICA: Aguarda o símbolo de real (R$) aparecer de verdade
                            # Se em 15 segundos não aparecer, ele considera que não tem o item
                            page.wait_for_selector("text=R$", timeout=15000)
                            page.wait_for_timeout(2000) # Pausa extra para carregar nomes
                            
                            corpo = page.locator("body").inner_text()
                            linhas = [l.strip() for l in corpo.split('\n') if l.strip()]
                            
                            achou = False
                            for i, linha in enumerate(linhas):
                                if 'R$' in linha and any(c.isdigit() for c in linha):
                                    # Procura o nome nas 10 linhas abaixo do preço
                                    for j in range(i+1, min(i+11, len(linhas))):
                                        n = linhas[j]
                                        # Filtros para ignorar lixo visual (botões, descontos)
                                        if 'R$' in n or len(n) < 3 or any(x in n.lower() for x in ['oferta', 'off', '%', 'unidade', 'peso', 'adicionar']):
                                            continue
                                        
                                        # Processa o preço e soma
                                        try:
                                            p_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", linha))
                                            total += float(p_limpo.replace('.', '').replace(',', '.'))
                                        except: pass
                                        
                                        res.append({"Item": item, "Mercado": n.title(), "Preço": linha})
                                        achou = True
                                        break
                                if achou: break
                            if not achou: res.append({"Item": item, "Mercado": "Não encontrado", "Preço": "-"})
                        except: 
                            res.append({"Item": item, "Mercado": "Esgotado ou Erro", "Preço": "-"})
                    
                    browser.close()
                    # Mostra o total com formatação de moeda
                    st.success(f"✅ Total Estimado: **R$ {total:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)
            except Exception as e:
                st.error(f"Erro no motor: {e}")
