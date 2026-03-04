import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do motor de navegação
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras Pro", layout="wide")
st.title("🛒 Engine V11 - Estabilidade Total")

# Interface de entrada
lista_txt = st.text_area("Digite sua lista (um por linha):", placeholder="Cebola\nArroz\nFeijão")

if st.button("Executar Busca Profissional 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Mapeando componentes e isolando produtos..."):
            try:
                with sync_playwright() as p:
                    # Lançamento do navegador com disfarce atualizado
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0"
                    )
                    page = context.new_page()
                    
                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # 1. Geração da URL de busca
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            # 2. Navegação com timeout estendido para evitar o erro de Timeout
                            page.goto(url, wait_until="domcontentloaded", timeout=45000)
                            
                            # 3. Sincronismo: aguarda o elemento de preço (R$) carregar
                            # Aumentei para 15s para garantir que sites lentos respondam
                            page.wait_for_selector("text=R$", timeout=15000)
                            page.wait_for_timeout(2000)

                            # 4. Mapeamento via DOM: Isola os cards de produtos
                            cards_data = page.evaluate("""
                                () => {
                                    return Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 300)
                                        .map(el => el.innerText);
                                }
                            """)

                            if cards_data:
                                # Analisamos o primeiro resultado (mais relevante)
                                # Indentação corrigida conforme feedback
                                bloco_texto = cards_data[0]
                                linhas = [l.strip() for l in bloco_texto.split('\n') if l.strip()]
                                
                                nome_encontrado, preco_encontrado = None, None
                                
                                for i, linha in enumerate(linhas):
                                    if 'R$' in linha and any(c.isdigit() for c in linha):
                                        preco_encontrado = linha
                                        # Busca o nome num raio de 4 linhas ao redor do preço
                                        vizinhos = [i-1, i-2, i+1, i+2]
                                        for idx in vizinhos:
                                            if 0 <= idx < len(linhas):
                                                cand = linhas[idx]
                                                lixo = ['oferta', 'off', '%', 'unidade', 'peso', 'adicionar', 'comprar']
                                                if len(cand) > 3 and 'R$' not in cand and not any(x in cand.lower() for x in lixo):
                                                    nome_encontrado = cand.title()
                                                    break
                                        break

                                if nome_encontrado and preco_encontrado:
                                    # Limpeza de string e soma matemática
                                    val_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_encontrado))
                                    total_geral += float(val_limpo.replace('.', '').replace(',', '.'))
                                    res.append({"Status": "✅", "Busca": item, "Produto": nome_encontrado, "Preço": preco_encontrado})
                                else:
                                    res.append({"Status": "⚠️", "Busca": item, "Produto": "Dados incompletos", "Preço": "-"})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado", "Preço": "-"})

                        except Exception:
                            # Captura de falhas individuais por item
                            res.append({"Status": "❌", "Busca": item, "Produto": "Erro/Timeout", "Preço": "-"})
                    
                    browser.close()
                    
                    # Exibição dos resultados finais
                    st.success(f"✅ Rancho Calculado: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Falha técnica no motor: {e}")
