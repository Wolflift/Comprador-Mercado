import os
import streamlit as st
import urllib.parse
from playwright.sync_api import sync_playwright

# Instalação mandatória (Nota: Informação externa às fontes)
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema de Compras Pro", layout="wide")
st.title("🛒 Engine de Busca - Estabilidade Beltrame")

lista_txt = st.text_area("Sua Lista de Compras:", placeholder="Cebola\nArroz")

if st.button("Executar Busca 🚀"):
    # Normalização da lista: remove espaços e ignora linhas vazias [1]
    itens = [i.strip() for i in lista_txt.split('\n') if i.strip()]
    
    if itens:
        with st.spinner("Conectando ao mercado e capturando preços..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0"
                    )
                    page = context.new_page()

                    # Passo 1: Acesso inicial para validar cookies/pop-ups
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded", timeout=60000)
                    
                    try:
                        btn_confirmar = page.locator("button:has-text('Confirmar')")
                        if btn_confirmar.is_visible(timeout=5000):
                            btn_confirmar.click()
                    except:
                        pass

                    res, total_geral = [], 0.0

                    for item in itens:
                        try:
                            # Normalização da busca para evitar erros de digitação [1, 2]
                            item_busca = item.strip().lower()
                            query = urllib.parse.quote(item_busca)
                            url_busca = f"https://beltramesupermercados.com.br/busca?q={query}"
                            
                            page.goto(url_busca, wait_until="load", timeout=30000)
                            
                            # Espera flexível: busca por qualquer texto que contenha R$
                            page.wait_for_selector("text=R$", timeout=15000)

                            # Extração inteligente via JavaScript no navegador
                            item_data = page.evaluate("""
                                () => {
                                    // Busca elementos que pareçam cards de produto (contêm R$ e não são gigantes)
                                    const cards = Array.from(document.querySelectorAll('div, section, article'))
                                        .filter(el => el.innerText.includes('R$') && el.innerText.length < 500);
                                    return cards.length > 0 ? cards.innerText : null;
                                }
                            """)

                            if item_data:
                                # Transforma o texto do card em lista para processamento [3]
                                linhas = [l.strip() for l in item_data.split('\n') if l.strip()]
                                preco_encontrado = None
                                nome_encontrado = "Produto não identificado"

                                for i, linha in enumerate(linhas):
                                    # Identifica o preço de forma mais flexível [4]
                                    if 'R$' in linha:
                                        preco_encontrado = linha
                                        # Busca o nome com lógica de vizinhança flexível
                                        for offset in [-1, -2, 1, 2]:
                                            idx = i + offset
                                            if 0 <= idx < len(linhas):
                                                cand = linhas[idx]
                                                lixo = ['oferta', 'off', '%', 'unidade', 'adicionar', 'comprar', 'kg', 'g']
                                                # Verifica se não é preço e se não contém palavras de lixo [2]
                                                if len(cand) > 2 and 'R$' not in cand and not any(w in cand.lower() for w in lixo):
                                                    nome_encontrado = cand.title() # Formatação visual [2]
                                                    break
                                        break

                                if preco_encontrado:
                                    # Limpeza de caracteres não numéricos para conversão em float [5, 6]
                                    val_limpo = "".join(filter(lambda x: x.isdigit() or x in ",.", preco_encontrado))
                                    valor_float = float(val_limpo.replace('.', '').replace(',', '.'))
                                    total_geral += valor_float
                                    res.append({"Status": "✅", "Busca": item, "Produto": nome_encontrado, "Preço": preco_encontrado})
                                else:
                                    res.append({"Status": "⚠️", "Busca": item, "Produto": "Dados incompletos", "Preço": "-"})
                            else:
                                res.append({"Status": "❌", "Busca": item, "Produto": "Não encontrado no site", "Preço": "-"})

                        except Exception as e:
                            # Erros não passam silenciosamente; são reportados na tabela [7, 8]
                            res.append({"Status": "❌", "Busca": item, "Produto": f"Erro: {str(e)[:30]}...", "Preço": "-"})

                    browser.close()
                    
                    st.success(f"✅ Total Calculado: **R$ {total_geral:,.2f}**".replace('.', 'X').replace(',', '.').replace('X', ','))
                    st.table(res)

            except Exception as e:
                st.error(f"Falha técnica no motor central: {e}")
