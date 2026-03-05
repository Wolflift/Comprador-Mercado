import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor do Streamlit
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras Pro", layout="wide")
st.title("🛒 Engine V25 - Estabilidade de Sessão (Beltrame)")

lista_txt = st.text_area("Sua Lista de Compras:", placeholder="Cebola\nArroz")

if st.button("Executar Busca Profissional 🚀"):
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    if itens:
        with st.spinner("Validando acesso e capturando preços..."):
            try:
                with sync_playwright() as p:
                    # Lançamento com disfarce de usuário real
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0"
                    )
                    page = context.new_page()

                    # 1. PASSO DE SESSÃO: Resolve o pop-up de loja antes de qualquer busca
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded", timeout=60000)
                    
                    try:
                        # Tenta localizar o botão azul de confirmar
                        btn_confirmar = page.locator("button:has-text('Confirmar')")
                        if btn_confirmar.is_visible(timeout=10000):
                            btn_confirmar.click()
                            page.wait_for_timeout(3000)
                    except:
                        # Segue se o pop-up não aparecer (já salvo por cookie)
                        pass

                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # 2. BUSCA INDIVIDUAL
                            query = urllib.parse.quote(item)
                            url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                            page.goto(url_busca, wait_until="load", timeout=60000)
                            
                            # 3. SINCRONISMO: Espera o R$ aparecer para evitar o Timeout
                            page.wait_for_selector("text=R$", timeout=20000)
                            page.wait_for_timeout(3000)

                            # 4. EXTRAÇÃO POR ESCOPO (Isola o primeiro 'card' de produto)
                            # Indentação e fechamento revisados
                            item_data = page.evaluate("""
                                () => {
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 450);
                                    return cards.length > 0 ? cards[0].innerText : null;
                                }
                            """)

                            if item_data:
                                linhas = [l.strip() for l in item_data.split('\n') if l.strip()]
                                nome_encontrado, preco_encontrado = "Item Encontrado", None

                                for i, linha in enumerate(linhas):
                                    if 'R$' in linha and any(c.isdigit() for c in linha):
                                        preco_encontrado = linha
                                        # Busca o nome num raio de 4 linhas vizinhas
                                        indices_vizinhos = [i-1, i-2, i+1, i+2]
                                        for idx in indices_vizinhos:
                                            if 0 <= idx < len(linhas):
                                                cand = linhas[idx]
                                                lixo = ['oferta', 'off', '%', 'unidade', 'peso', 'adicionar', 'comprar', 'kg']
                                                if len(cand) > 3 and 'R$' not in cand and not any(w in cand.lower() for w in lixo):
                                                    nome_encontrado = cand.title()
                                                    break
                                        break

                                if preco_encontrado:
                                    # Limpeza de string e soma real do valor
                                    val_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_encontrado))
                                    total_geral += float(val_limpo.replace('.', '').replace(',', '.'))
                                    res.append({"Status": "✅", "Busca": item, "Produto": nome_encontrado, "Preço": preco_encontrado})
                                else:
                                    res.append({"Status": "⚠️", "Busca": item, "Produto": "Dados incompletos", "Preço": "-"})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado", "Preço": "-"})

                        except:
                            # Captura erros individuais por item sem travar o motor
                            res.append({"Status": "❌", "Busca": item, "Produto": "Erro/Timeout no Item", "Preço": "-"})

                    browser.close()
                    
                    # Exibição dos resultados finais
                    st.success(f"✅ Rancho Calculado: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Falha técnica no motor central: {e}")
