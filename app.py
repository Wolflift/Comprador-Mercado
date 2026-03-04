import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação forçada do navegador
os.system("playwright install chromium")

st.set_page_config(page_title="Rancho da Mãe", layout="wide")
st.title("🛒 Lista de Compras - Beltrame (Engine V3)")

# Campo de texto limpo
lista_input = st.text_area("Sua Lista:", placeholder="Cebola\nBatata\nArroz")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista_input.split('\n') if i.strip()]
    if itens:
        with st.spinner(f"Pesquisando {len(itens)} itens..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    res, total_geral = [], 0.0
                    
                    for item in itens:
                        try:
                            # Busca direta por URL (mais rápido e seguro)
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url, wait_until="domcontentloaded", timeout=30000)
                            
                            # Espera o carregamento dos preços
                            page.wait_for_selector("text=R$", timeout=10000)
                            page.wait_for_timeout(2000) # Pausa para renderização
                            
                            linhas = [l.strip() for l in page.locator("body").inner_text().split('\n') if l.strip()]
                            
                            nome_achado, preco_achado = None, None
                            
                            for i, linha in enumerate(linhas):
                                if 'R$' in linha and any(c.isdigit() for c in linha):
                                    preco_achado = linha
                                    # BUSCA 360: Procura o nome 3 linhas pra cima e 3 pra baixo
                                    vizinhos = []
                                    # Pega índices válidos ao redor do preço
                                    indices = [i-1, i-2, i-3, i+1, i+2, i+3]
                                    for idx in indices:
                                        if 0 <= idx < len(linhas):
                                            vizinhos.append(linhas[idx])
                                    
                                    # Filtra o primeiro vizinho que parece um nome
                                    for v in vizinhos:
                                        v_low = v.lower()
                                        lixo = ['carrinho', 'adicionar', 'lista', 'indisponível', 'r$', 'off', 'ver mais', 'comprar', 'unidade', 'peso']
                                        if len(v) > 3 and not any(word in v_low for word in lixo):
                                            nome_achado = v.title()
                                            break
                                    if nome_achado: break
                            
                            if nome_achado:
                                res.append({"Busca": item, "Produto": nome_achado, "Preço": preco_achado})
                                # Soma matemática
                                p_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_achado))
                                total_geral += float(p_limpo.replace('.', '').replace(',', '.'))
                            else:
                                res.append({"Busca": item, "Produto": "Não identificado", "Preço": "-"})
                        except:
                            res.append({"Busca": item, "Produto": "Erro/Esgotado", "Preço": "-"})
                    
                    browser.close()
                    st.success(f"✅ Compra Finalizada! Total: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)
            except Exception as e:
                st.error(f"Falha no motor: {e}")
