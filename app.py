import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Força a instalação do navegador
os.system("playwright install chromium")

st.set_page_config(page_title="Minhas Compras", page_icon="🛒", layout="wide")

st.title("🛒 Lista de Compras Inteligente - Beltrame")
st.write("Versão de Alta Estabilidade: O robô agora espera o carregamento completo de cada item.")

lista_texto = st.text_area("Sua Lista de Compras:", placeholder="Digite um item por linha (ex: Arroz 5kg)")

if st.button("Fazer Rancho 🛒"):
    itens = [i.strip() for i in lista_texto.split('\n') if i.strip()]
    
    if itens:
        with st.spinner(f"Processando {len(itens)} itens... O robô está sendo cuidadoso para não falhar."):
            try:
                with sync_playwright() as p:
                    # Configurações de "Disfarce Humano"
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                        viewport={'width': 1280, 'height': 800}
                    )
                    page = context.new_page()
                    
                    resultados = []
                    total_compra = 0.0
                    
                    for item in itens:
                        try:
                            query = urllib.parse.quote(item)
                            url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            # Navegação com tempo de espera maior
                            page.goto(url_busca, wait_until="networkidle", timeout=45000)
                            
                            # Simula uma pequena rolagem para ativar o carregamento dos itens
                            page.mouse.wheel(0, 400)
                            
                            # ESPERA CRÍTICA: Aguarda um elemento de preço real aparecer na tela
                            try:
                                page.wait_for_selector("text=R$", timeout=15000)
                            except:
                                resultados.append({"Item": item, "Status": "Não encontrado/Esgotado", "Preço": "-"})
                                continue

                            # Captura todos os blocos de produtos da página
                            # Usamos uma busca por elementos que contenham R$
                            corpo = page.locator("body").inner_text()
                            linhas = [l.strip() for l in corpo.split('\n') if l.strip()]
                            
                            encontrou_neste_item = False
                            for i, linha in enumerate(linhas):
                                if 'R$' in linha and any(c.isdigit() for c in linha):
                                    # O nome geralmente está nas próximas linhas
                                    for j in range(i+1, min(i+8, len(linhas))):
                                        candidato = linhas[j]
                                        # Filtros para ignorar lixo visual
                                        if 'R$' in candidato or len(candidato) < 3 or any(x in candidato.lower() for x in ['oferta', 'off', '%', 'unidade', 'peso', 'comprar', 'adicionar']):
                                            continue
                                        
                                        nome_real = candidato.title()
                                        preco_real = linha
                                        
                                        # Limpeza do preço para soma
                                        try:
                                            # Pega apenas os números e a vírgula/ponto
                                            valor_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_real))
                                            valor_num = float(valor_limpo.replace('.', '').replace(',', '.'))
                                            
                                            total_compra += valor_num
                                            resultados.append({"Item": item, "Status": nome_real, "Preço": preco_real})
                                            encontrou_neste_item = True
                                            break
                                        except:
                                            continue
                                if encontrou_neste_item: break
                            
                            if not encontrou_neste_item:
                                resultados.append({"Item": item, "Status": "Não identificado", "Preço": "-"})
                                
                        except Exception as e:
                            resultados.append({"Item": item, "Status": f"Erro técnico na busca", "Preço": "-"})
                            
                    browser.close()
                    
                    # Exibição do Resultado
                    st.success(f"✅ Rancho Calculado! Total: **R$ {total_compra:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(resultados) # Tabela fixa é mais fácil de ler que o dataframe em alguns celulares
                    
            except Exception as e:
                st.error(f"Ocorreu um erro no motor de busca: {e}")
