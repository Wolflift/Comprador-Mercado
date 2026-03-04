import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instala o navegador no servidor do Streamlit
os.system("playwright install chromium")

st.set_page_config(page_title="Rancho Automático", layout="wide")
st.title("🛒 Lista de Compras - Beltrame")

lista_txt = st.text_area("Sua Lista:", placeholder="Ex: Cebola\nArroz")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner(f"Pesquisando {len(itens)} itens..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    res, total = [], 0.0
                    
                    for item in itens:
                        try:
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            # Vai para a busca e aguarda o carregamento básico
                            page.goto(url, wait_until="domcontentloaded", timeout=45000)
                            
                            # ESPERA FORÇADA: 5 segundos para o JavaScript do site carregar os preços
                            page.wait_for_timeout(5000)
                            
                            linhas = [l.strip() for l in page.locator("body").inner_text().split('\n') if l.strip()]
                            
                            achou = False
                            for i, linha in enumerate(linhas):
                                if 'R$' in linha and any(c.isdigit() for c in linha):
                                    # Procura o nome nas 5 linhas vizinhas (cima ou baixo)
                                    vizinhos = linhas[max(0, i-5):min(len(linhas), i+6)]
                                    for v in vizinhos:
                                        v_low = v.lower()
                                        lixo = ['carrinho','adicionar','lista','r$','off','comprar','unidade','peso','oferta']
                                        if len(v) > 3 and not any(w in v_low for w in lixo):
                                            # Sucesso: Limpa preço e soma
                                            p_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", linha))
                                            total += float(p_limpo.replace('.', '').replace(',', '.'))
                                            res.append({"Busca": item, "Produto": v.title(), "Preço": linha})
                                            achou = True
                                            break
                                    if achou: break
                            if not achou:
                                res.append({"Busca": item, "Produto": "Não encontrado", "Preço": "-"})
                        except:
                            res.append({"Busca": item, "Produto": "Erro na conexão", "Preço": "-"})
                    
                    browser.close()
                    st.success(f"✅ Total Estimado: **R$ {total:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)
            except Exception as e:
                st.error(f"Falha no motor: {e}")
