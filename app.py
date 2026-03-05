import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do motor de navegação
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras Pro", layout="wide")
st.title("🛒 Engine V13 - Assertividade Máxima")

lista_txt = st.text_area("Sua Lista de Compras:", placeholder="Cebola\nArroz")

if st.button("Executar Busca Profissional 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Navegando e capturando dados..."):
            try:
                with sync_playwright() as p:
                    # Lançamento do navegador com disfarce humano completo
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0",
                        viewport={'width': 1280, 'height': 800}
                    )
                    page = context.new_page()

                    # Forçar a sessão inicial na home
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)

                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"

                            # O segredo do timeout: Esperar o carregamento total e dar tempo ao JS
                            page.goto(url, wait_until="load", timeout=60000)
                            
                            # ESPERA MANDATÓRIA: 5 segundos para os preços "brotarem" na tela
                            page.wait_for_timeout(5000) 

                            # Extração via JavaScript direto: Isolamento de containers
                            produto_info = page.evaluate("""
                                () => {
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 500);
                                    
                                    if (cards.length === 0) return null;
                                    
                                    // Retorna o texto bruto do primeiro card de produto encontrado
                                    return cards[0].innerText;
                                }
                            """)

                            if produto_info:
                                # Processamento do texto do card (suporta quebras de linha do JS)
                                linhas = [l.strip() for l in produto_info.split('\n') if l.strip()]
                                nome_enc, preco_enc = "Não identificado", None

                                for i, linha in enumerate(linhas):
                                    if 'R$' in linha and any(c.isdigit() for c in linha):
                                        preco_enc = linha
                                        # Busca o nome num raio de 4 linhas vizinhas
                                        vizinhos_indices = [i+1, i+2, i-1, i-2, i-3]
                                        for idx in vizinhos_indices:
                                            if 0 <= idx < len(linhas):
                                                cand = linhas[idx]
                                                lixo = ['oferta', 'off', '%', 'unidade', 'peso', 'adicionar', 'comprar', 'kg']
                                                if len(cand) > 3 and 'R$' not in cand and not any(w in cand.lower() for w in lixo):
                                                    nome_enc = cand.title()
                                                    break
                                        break

                                if preco_enc:
                                    # Limpeza de string e soma do total
                                    val_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_enc))
                                    total_geral += float(val_limpo.replace('.', '').replace(',', '.'))
                                    res.append({"Status": "✅", "Busca": item, "Produto": nome_enc, "Preço": preco_enc})
                                else:
                                    res.append({"Status": "❌", "Busca": item, "Produto": "Preço não visível", "Preço": "-"})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado", "Preço": "-"})

                        except Exception:
                            res.append({"Status": "❌", "Busca": item, "Produto": "Erro/Timeout de Carregamento", "Preço": "-"})

                    # Fechamento do navegador após o loop
                    browser.close()
                    
                    # Exibição dos resultados finais
                    st.success(f"✅ Rancho Calculado: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Falha técnica no motor: {e}")
