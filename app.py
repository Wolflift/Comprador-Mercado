import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação forçada do navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras Pro", layout="wide")
st.title("🛒 Engine V12 - Estabilidade e Sessão")

# Campo de texto para a lista
lista_txt = st.text_area("Sua Lista de Compras:", placeholder="Cebola\nArroz")

if st.button("Executar Busca Profissional 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Simulando navegação e validando preços..."):
            try:
                with sync_playwright() as p:
                    # Lançamento do navegador com camuflagem de usuário real
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0"
                    )
                    page = context.new_page()

                    # PASSO DE SESSÃO: Entra na home primeiro para carregar os cookies da loja
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(3000)
                    
                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # 1. Geração da URL de busca individual
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            # 2. Navegação resiliente
                            page.goto(url, wait_until="domcontentloaded", timeout=45000)
                            
                            # 3. ESPERA AMPLIADA: Aguarda o R$ aparecer (âncora do preço)
                            # Se em 20s não aparecer, o site provavelmente bloqueou o robô
                            page.wait_for_selector("text=R$", timeout=20000)
                            page.wait_for_timeout(2000)

                            # 4. EXTRAÇÃO POR ESCOPO (JS): Captura apenas os cards de produtos
                            # Indentação rigorosa aplicada aqui para evitar IndentationError
                            cards_data = page.evaluate("""
                                () => {
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 300);
                                    return cards.map(c => c.innerText);
                                }
                            """)

                            if cards_data:
                                # Analisamos o primeiro resultado encontrado
                                bloco = cards_data[0]
                                linhas = [l.strip() for l in bloco.split('\n') if l.strip()]
                                
                                nome_encontrado, preco_encontrado = None, None
                                
                                for i, linha in enumerate(linhas):
                                    if 'R$' in linha and any(c.isdigit() for c in linha):
                                        preco_encontrado = linha
                                        # Procura o nome ao redor do preço no bloco isolado
                                        vizinhos = [i-1, i-2, i+1, i+2]
                                        for idx in vizinhos:
                                            if 0 <= idx < len(linhas):
                                                cand = linhas[idx]
                                                lixo = ['oferta', 'off', '%', 'unidade', 'peso', 'adicionar', 'comprar']
                                                if len(cand) > 3 and 'R$' not in cand and not any(w in cand.lower() for w in lixo):
                                                    nome_encontrado = cand.title()
                                                    break
                                        break

                                if nome_encontrado and preco_encontrado:
                                    # Processamento numérico para soma do total
                                    val_str = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_encontrado))
                                    total_geral += float(val_str.replace('.', '').replace(',', '.'))
                                    res.append({"Status": "✅", "Busca": item, "Produto": nome_encontrado, "Preço": preco_encontrado})
                                else:
                                    res.append({"Status": "⚠️", "Busca": item, "Produto": "Nome não identificado", "Preço": preco_encontrado})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado", "Preço": "-"})

                        except Exception:
                            # Registra o timeout ou erro de carregamento por item
                            res.append({"Status": "❌", "Busca": item, "Produto": "Erro/Timeout de Carregamento", "Preço": "-"})
                    
                    browser.close()
                    
                    # Interface final de resultados
                    st.success(f"✅ Rancho Calculado: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Falha crítica no sistema de navegação: {e}")
