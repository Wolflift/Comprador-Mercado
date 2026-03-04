import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Garante que o navegador esteja instalado no servidor do Streamlit
os.system("playwright install chromium")

st.set_page_config(page_title="Minhas Compras", page_icon="🛒", layout="wide")
st.title("🛒 Lista de Compras - Versão Estável")

lista_texto = st.text_area("Sua Lista de Compras:", placeholder="Digite os itens (um por linha).\nEx: Cebola\nArroz 5kg")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista_texto.split('\n') if i.strip()]
    
    if itens:
        with st.spinner(f"O robô está processando {len(itens)} itens..."):
            try:
                with sync_playwright() as p:
                    # Lança o navegador com disfarce de humano atualizado
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
                    page = context.new_page()
                    
                    resultados = []
                    total_geral = 0.0
                    
                    for item in itens:
                        try:
                            # Vai direto para a busca (economiza tempo e cliques)
                            query = urllib.parse.quote(item)
                            url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            # Carrega apenas o essencial (domcontentloaded)
                            page.goto(url_busca, wait_until="domcontentloaded", timeout=45000)
                            
                            # Espera curta para o JavaScript desenhar os preços
                            page.wait_for_timeout(3000)
                            
                            # Tenta localizar o texto de preço 'R$'
                            try:
                                page.wait_for_selector("text=R$", timeout=10000)
                                corpo = page.locator("body").inner_text()
                                linhas = [l.strip() for l in corpo.split('\n') if l.strip()]
                                
                                achou_neste_item = False
                                for i, linha in enumerate(linhas):
                                    if 'R$' in linha and any(c.isdigit() for c in linha):
                                        # O nome do produto costuma estar nas linhas seguintes
                                        for j in range(i+1, min(i+10, len(linhas))):
                                            cand = linhas[j]
                                            # Filtra termos irrelevantes do site
                                            if 'R$' in cand or len(cand) < 3 or any(x in cand.lower() for x in ['oferta', 'off', '%', 'unidade', 'peso']):
                                                continue
                                            
                                            nome_prod = cand.title()
                                            preco_prod = linha
                                            
                                            # Limpeza numérica para soma matemática
                                            valor_str = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_prod)).replace('.', '').replace(',', '.')
                                            total_geral += float(valor_str)
                                            
                                            resultados.append({"Item": item, "Encontrado": nome_prod, "Preço": preco_prod})
                                            achou_neste_item = True
                                            break
                                    if achou_neste_item: break
                                
                                if not achou_neste_item:
                                    resultados.append({"Item": item, "Encontrado": "Não identificado", "Preço": "-"})
                                    
                            except:
                                resultados.append({"Item": item, "Encontrado": "Esgotado ou não encontrado", "Preço": "-"})
                        
                        except Exception:
                            resultados.append({"Item": item, "Encontrado": "Erro na conexão", "Preço": "-"})
                            continue
                    
                    # Fecha o navegador após o loop para poupar memória
                    browser.close()
                    
                    # Exibe o valor total com formatação brasileira
                    st.success(f"✅ Rancho Calculado! Total Estimado: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(resultados)
                    
            except Exception as e:
                st.error(f"Erro no motor central: {e}")
    else:
        st.warning("A lista
