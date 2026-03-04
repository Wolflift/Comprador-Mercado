import os
import streamlit as st
from playwright.sync_api import sync_playwright

os.system("playwright install chromium")

st.set_page_config(page_title="Minhas Compras", page_icon="🛒", layout="wide")

st.title("🛒 Lista de Compras Inteligente")
st.write("Digite sua lista abaixo (um item por linha). O robô vai pesquisar tudo no Beltrame e montar seu carrinho.")

# Trocamos o campo de link por uma caixa de texto grande!
lista_texto = st.text_area("Sua Lista de Compras:", "Cebola\nBatata\nLeite Integral\nCafé")

if st.button("Fazer Rancho 🛒"):
    # Limpa as linhas vazias e cria uma lista real de itens
    itens_pesquisa = [item.strip() for item in lista_texto.split('\n') if item.strip()]
    
    if itens_pesquisa:
        with st.spinner(f"O robô pegou o carrinho e está procurando {len(itens_pesquisa)} itens... (isso pode levar 1 ou 2 minutinhos)"):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    resultados_finais = []
                    valor_total_compra = 0.0
                    
                    # O robô vai repetir esse processo para CADA item da sua lista
                    for item in itens_pesquisa:
                        try:
                            # 1. Vai para a página inicial
                            page.goto("https://beltramesupermercados.com.br/", wait_until="domcontentloaded", timeout=30000)
                            
                            # 2. Acha a barra de pesquisa (pelo texto "Leite, arroz..." que fica de fundo) e digita o item
                            busca_input = page.get_by_placeholder("Leite, arroz", exact=False)
                            busca_input.fill(item)
                            page.keyboard.press("Enter")
                            
                            # 3. Espera carregar os resultados
                            page.wait_for_selector("text=R$", timeout=15000)
                            
                            # 4. Lê a prateleira igual fizemos antes
                            text_content = page.locator("body").inner_text()
                            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                            
                            produto_encontrado = None
                            preco_encontrado = None
                            
                            # Procura o primeiro preço e nome válidos
                            for i, line in enumerate(lines):
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    preco_temp = line
                                    nome_temp = None
                                    
                                    for j in range(i + 1, min(i + 6, len(lines))):
                                        next_line = lines[j].strip()
                                        if 'R$' in next_line:
                                            break
                                            
                                        ignore_list = ['peso', 'unidade', 'adicionar', 'comprar', 'oferta', 'off', 'esgotado']
                                        if next_line.lower() in ignore_list or next_line.startswith('-') or next_line.endswith('%'):
                                            continue
                                            
                                        if len(next_line) > 3:
                                            nome_temp = next_line
                                            break
                                    
                                    if nome_temp:
                                        produto_encontrado = nome_temp.title()
                                        preco_encontrado = preco_temp
                                        break # IMPORTANTE: Como queremos só 1 pro carrinho, achou o primeiro, ele para de procurar!
                            
                            # 5. Salva o resultado no carrinho
                            if produto_encontrado:
                                resultados_finais.append({
                                    "Item da Lista": item, 
                                    "Produto no Mercado": produto_encontrado, 
                                    "Preço": preco_encontrado
                                })
                                
                                # Transforma o "R$ 5,99" em matemática para somar o total
                                try:
                                    valor_limpo = preco_encontrado.replace('R$', '').replace('.', '').replace(',', '.').strip()
                                    valor_total_compra += float(valor_limpo)
                                except:
                                    pass
                            else:
                                resultados_finais.append({"Item da Lista": item, "Produto no Mercado": "Não encontrado / Esgotado", "Preço": "-"})
                                
                        except Exception as e:
                            # Se der erro num item específico (ex: não achou nada), avisa mas continua a compra
                            resultados_finais.append({"Item da Lista": item, "Produto no Mercado": "Erro na busca", "Preço": "-"})
                            continue

                    browser.close()
                    
                    # Mostra a tela final da vitória
                    st.success(f"✅ Compra Finalizada! O valor total estimado no Beltrame é de **R$ {valor_total_compra:.2f}**".replace('.', ','))
                    st.dataframe(resultados_finais, use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ O robô tropeçou: {e}")
    else:
        st.warning("A lista está vazia! Digite alguma coisa.")
