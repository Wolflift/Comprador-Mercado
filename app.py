import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instala o navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Rancho da Mãe", layout="wide")
st.title("🛒 Lista de Compras - Beltrame")

# Texto de exemplo sumindo ao digitar
lista = st.text_area("Sua Lista:", placeholder="Ex: Cebola\nArroz")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista.split('\n') if i.strip()]
    if itens:
        with st.spinner("Procurando itens..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    res, total = [], 0.0
                    
                    for item in itens:
                        try:
                            # Busca direta via URL
                            query = urllib.parse.quote(item)
                            page.goto(f"https://beltramesupermercados.com.br/busca?q={query}", timeout=45000)
                            page.wait_for_timeout(3000) # Espera carregar os preços
                            
                            corpo = page.locator("body").inner_text()
                            linhas = [l.strip() for l in corpo.split('\n') if l.strip()]
                            
                            achou = False
                            for i, linha in enumerate(linhas):
                                if 'R$' in linha and any(c.isdigit() for c in linha):
                                    # Pega o nome do produto que vem logo abaixo do preço
                                    for j in range(i+1, min(i+10, len(linhas))):
                                        n = linhas[j]
                                        if 'R$' in n or len(n) < 3 or any(x in n.lower() for x in ['oferta', 'off', '%', 'unidade']):
                                            continue
                                        
                                        # Soma o preço
                                        try:
                                            p_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", linha))
                                            total += float(p_limpo.replace('.', '').replace(',', '.'))
                                        except: pass
                                        
                                        res.append({"Item": item, "Mercado": n.title(), "Preço": linha})
                                        achou = True
                                        break
                                if achou: break
                            if not achou: res.append({"Item": item, "Mercado": "Não encontrado", "Preço": "-"})
                        except: res.append({"Item": item, "Mercado": "Erro na busca", "Preço": "-"})
                    
                    browser.close()
                    st.success(f"✅ Total: **R$ {total:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)
            except Exception as e:
                st.error(f"Erro no motor: {e}")
