import os
import streamlit as st
from playwright.sync_api import sync_playwright

os.system("playwright install chromium")

st.set_page_config(page_title="Minhas Compras", page_icon="🛒", layout="wide")

st.title("🛒 Lista de Compras Inteligente - Beltrame")
st.write("Digite os itens (um por linha). O robô pegará o primeiro resultado de cada busca.")

lista_texto = st.text_area("Sua Lista de Compras:", placeholder="Ex: Arroz 5kg\nFeijão\nCebola")

if st.button("Fazer Rancho 🛒"):
    itens_pesquisa = [item.strip() for item in lista_texto.split('\n') if item.strip()]
    
    if itens_pesquisa:
        with st.spinner(f"Pesquisando {len(itens_pesquisa)} itens..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    resultados_finais = []
                    valor_total_compra = 0.0
                    
                    for item in itens_pesquisa:
                        try:
                            # ATALHO: Vai direto para a URL de busca do Beltrame
                            search_url = f"https://beltramesupermercados.com.br/busca?q={item}"
                            page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                            
                            # Espera os produtos aparecerem
                            page.wait_for_selector("text=R$", timeout=10000)
                            
                            text_content = page.locator("body").inner_text()
                            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                            
                            produto_nome = None
                            produto_preco = None
                            
                            # Lógica aprimorada para capturar o primeiro par Preço + Nome
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    # Encontrou o preço
                                    for j in range(i + 1, min(i + 6, len(lines))):
                                        cand = lines[j].strip()
                                        if 'R$' in cand or len(cand) < 3 or any(x in cand.lower() for x in ['oferta', 'off', '%', 'unidade', 'peso']):
                                            continue
                                        produto_nome = cand
                                        produto_preco = line
                                        break
                                if produto_nome: break

                            if produto_nome:
                                resultados_finais.append({"Item da Lista": item, "Produto Encontrado": produto_nome.title(), "Preço": produto_preco})
                                # Soma no total
                                val = produto_preco.split(' ')[1].replace('.', '').replace(',', '.') # Pega '1,98' de 'R$ 1,98 kg'
                                valor_total_compra += float(val)
                            else:
                                resultados_finais.append({"Item da Lista": item, "Produto Encontrado": "Não encontrado", "Preço": "-"})
                        except:
                            resultados_finais.append({"Item da Lista": item, "Produto Encontrado": "Erro na busca", "Preço": "-"})

                    browser.close()
                    
                    st.success(f"✅ Compra Finalizada! Total: **R$ {valor_total_compra:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.dataframe(resultados_finais, use_container_width=True)
            except Exception as e:
                st.error(f"Erro geral: {e}")
