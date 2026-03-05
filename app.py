import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do motor de navegação
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras Pro", layout="wide")
st.title("🛒 Engine V14 - O Caçador (Beltrame)")

lista_txt = st.text_area("Sua Lista de Compras:", placeholder="Cebola\nArroz")

if st.button("Executar Busca Profissional 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Navegando e forçando carregamento de preços..."):
            try:
                with sync_playwright() as p:
                    # Lançamento com disfarce humano e viewport maior
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0",
                        viewport={'width': 1920, 'height': 1080}
                    )
                    page = context.new_page()

                    # Sessão inicial para validar cookies
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)

                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            query = urllib.parse.quote(item)
                            url = f"https://beltramesupermercados.com.br/busca?q={query}"

                            # Vai para a busca e aguarda a rede estabilizar
                            page.goto(url, wait_until="load", timeout=60000)
                            
                            # AÇÃO CRÍTICA: Rola a página para forçar o Lazy Loading do mercado
                            page.mouse.wheel(0, 600)
                            page.wait_for_timeout(4000) 

                            # Script de extração aprimorado: Busca o container do produto
                            item_data = page.evaluate("""
                                () => {
                                    // Procura por blocos que contenham R$
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length > 50 && el.innerText.length < 600);
                                    
                                    if (cards.length === 0) return null;
                                    
                                    // Retorna o texto do primeiro bloco que parece um produto
                                    return cards[0].innerText;
                                }
                            """)

                            if item_data:
                                linhas = [l.strip() for l in item_data.split('\n') if l.strip()]
                                nome_enc, preco_enc = "Não identificado", None

                                for i, linha in enumerate(linhas):
                                    if 'R$' in linha and any(c.isdigit() for c in linha):
                                        preco_enc = linha
                                        # Busca o nome ao redor do preço
                                        for idx in [i+1, i+2, i-1, i-2, i-3]:
                                            if 0 <= idx < len(linhas):
                                                cand = linhas[idx]
                                                lixo = ['oferta', 'off', '%', 'unidade', 'peso', 'adicionar', 'comprar', 'kg', 'ver mais']
                                                if len(cand) > 4 and 'R$' not in cand and not any(w in cand.lower() for w in lixo):
                                                    nome_enc = cand.title()
                                                    break
                                        break

                                if preco_enc:
                                    val_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_enc))
                                    total_geral += float(val_limpo.replace('.', '').replace(',', '.'))
                                    res.append({"Status": "✅", "Busca": item, "Produto": nome_enc, "Preço": preco_enc})
                                else:
                                    res.append({"Status": "❌", "Busca": item, "Produto": "Preço não capturado", "Preço": "-"})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado na prateleira", "Preço": "-"})

                        except Exception:
                            res.append({"Status": "❌", "Busca": item, "Produto": "Erro de conexão", "Preço": "-"})

                    browser.close()
                    
                    st.success(f"✅ Processamento Concluído! Total: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Falha técnica: {e}")
