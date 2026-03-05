import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação forçada do navegador no servidor do Streamlit
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras Pro", layout="wide")
st.title("🛒 Engine V15 - Estabilidade Máxima (Beltrame)")

# Entrada de dados em lista
lista_txt = st.text_area("Sua Lista de Compras:", placeholder="Cebola\nArroz\nFeijão")

if st.button("Executar Busca Profissional 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Navegando e capturando preços reais..."):
            try:
                with sync_playwright() as p:
                    # Lançamento com disfarce humano total e tela cheia
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0",
                        viewport={'width': 1920, 'height': 1080}
                    )
                    page = context.new_page()

                    # Valida sessão na home para carregar cookies de loja
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(3000)
                    
                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # Busca via URL direta (método mais veloz)
                            query = urllib.parse.quote(item)
                            url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url_busca, wait_until="domcontentloaded", timeout=60000)
                            
                            # AÇÃO CRÍTICA: Aguarda o símbolo R$ e rola a página para carregar preços dinâmicos
                            page.wait_for_selector("text=R$", timeout=20000)
                            page.mouse.wheel(0, 400)
                            page.wait_for_timeout(3000)

                            # EXTRAÇÃO VIA JAVASCRIPT: Isola apenas os cards de produtos reais
                            # Indentação conferida para evitar IndentationError
                            info_produto = page.evaluate("""
                                () => {
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length > 50 && el.innerText.length < 500);
                                    return cards.length > 0 ? cards[0].innerText : null;
                                }
                            """)

                            if info_produto:
                                # Processamento de linhas do card encontrado
                                linhas = [l.strip() for l in info_produto.split('\n') if l.strip()]
                                nome_capturado, preco_capturado = "Não identificado", None
                                
                                for i, linha in enumerate(linhas):
                                    if 'R$' in linha and any(c.isdigit() for c in linha):
                                        preco_capturado = linha
                                        # Procura o nome num raio de 4 linhas vizinhas
                                        indices_alvo = [i+1, i+2, i-1, i-2, i-3]
                                        for idx in indices_alvo:
                                            if 0 <= idx < len(linhas):
                                                cand = linhas[idx]
                                                lixo = ['oferta', 'off', '%', 'unidade', 'peso', 'adicionar', 'comprar', 'kg']
                                                if len(cand) > 4 and 'R$' not in cand and not any(w in cand.lower() for w in lixo):
                                                    nome_capturado = cand.title()
                                                    break
                                        break
                                
                                if preco_capturado:
                                    # Limpeza de string e soma real do valor total
                                    valor_str = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_capturado))
                                    total_geral += float(valor_str.replace('.', '').replace(',', '.'))
                                    res.append({"Status": "✅", "Busca": item, "Produto": nome_capturado, "Preço": preco_capturado})
                                else:
                                    res.append({"Status": "❌", "Busca": item, "Produto": "Preço não visível", "Preço": "-"})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado na tela", "Preço": "-"})
                        
                        except Exception:
                            # Trata timeouts individuais sem travar o loop de outros itens
                            res.append({"Status": "❌", "Busca": item, "Produto": "Erro/Timeout de Carregamento", "Preço": "-"})

                    browser.close()
                    
                    # Interface de resultados com formatação brasileira
                    st.success(f"✅ Processamento Finalizado! Total: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Falha técnica crítica: {e}")
    else:
        st.warning("A lista está vazia!")
