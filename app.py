import os
import streamlit as st
from playwright.sync_api import sync_playwright

# Instalação mandatória do navegador no servidor
os.system("playwright install chromium")

st.set_page_config(page_title="Sistema Pro Beltrame v6", page_icon="🛒", layout="wide")

CATEGORIAS = {
    "Promoções": "https://beltramesupermercados.com.br/promocoes",
    "Hortifruti": "https://beltramesupermercados.com.br/categorias/hortifruti",
    "Mercearia": "https://beltramesupermercados.com.br/categorias/mercearia",
    "Carnes e Aves": "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "Limpeza": "https://beltramesupermercados.com.br/categorias/limpeza"
}

st.title("🛒 Engine Beltrame - Regras de Validação de Dados")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

# Função auxiliar para converter string "R$ 10,50" em float 10.50
def limpar_preco(texto):
    try:
        return float(texto.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except:
        return 0.0

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🚀 Iniciar Varredura"):
        with st.spinner("O robô está aplicando as regras de filtragem..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent="Mozilla/5.0")
                    page = context.new_page()

                    # Resolver popup inicial
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        btn = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn.is_visible(timeout=5000):
                            btn.click()
                            page.wait_for_timeout(1500)
                    except: pass

                    base_temp = []
                    for nome_cat, url in CATEGORIAS.items():
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=40000)
                            for _ in range(5):
                                page.mouse.wheel(0, 2000)
                                page.wait_for_timeout(800)
                            
                            page.wait_for_selector("text=R$", timeout=10000)
                            text_content = page.locator("body").inner_text()
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            i = 0
                            while i < len(lines):
                                line = lines[i]
                                
                                # REGRA 1: Identificar se a linha é um preço
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    if "kg" in line.lower() or "un" in line.lower():
                                        i += 1
                                        continue
                                    
                                    # Captura o preço atual e verifica se o próximo também é preço (bloco de promoção)
                                    preco_a = line
                                    preco_b = None
                                    
                                    if i+1 < len(lines) and 'R$' in lines[i+1] and not ("kg" in lines[i+1].lower()):
                                        preco_b = lines[i+1]
                                        i += 1 # Avança o índice para não reprocessar o segundo preço como item novo
                                    
                                    # REGRA 2: Lógica de Maior/Menor para Preço Cheio vs Promo
                                    val_a = limpar_preco(preco_a)
                                    val_b = limpar_preco(preco_b) if preco_b else 0.0
                                    
                                    if val_b > 0:
                                        # Se temos dois valores, o maior é o cheio, o menor é a promo
                                        p_cheio = preco_a if val_a > val_b else preco_b
                                        p_promo = preco_b if val_a > val_b else preco_a
                                    else:
                                        # Se temos só um valor, ele é o preço cheio e não há promo
                                        p_cheio = preco_a
                                        p_promo = "-"

                                    # REGRA 3: O Nome deve conter letras e não ser preço
                                    nome_real = "Desconhecido"
                                    for j in range(i-1, i-8, -1):
                                        if j < 0: break
                                        txt = lines[j]
                                        # Verifica se a linha contém letras e NÃO contém "R$" (evita capturar preços no nome)
                                        if any(c.isalpha() for c in txt) and 'R$' not in txt and len(txt) > 3:
                                            # Filtro de ruído (títulos de categoria)
                                            ruido = ['carrinho', 'adicionar', 'lista', 'indisponível', 'off', 'ver mais', 'oferta', 'mercearia', 'limpeza', 'carnes']
                                            if not any(word in txt.lower() for word in ruido):
                                                nome_real = txt
                                                break
                                    
                                    if nome_real != "Desconhecido":
                                        base_temp.append({
                                            "Categoria": nome_cat,
                                            "Produto": nome_real.title(),
                                            "Preço Cheio": p_cheio,
                                            "Preço Promo": p_promo
                                        })
                                i += 1
                        except:
                            i += 1
                            continue

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success("✅ Base carregada com sucesso e regras aplicadas!")
            except Exception as e:
                st.error(f"Erro: {e}")

# INTERFACE DE BUSCA
if st.session_state.base_produtos:
    st.divider()
    busca = st.text_input("🔍 Pesquisar na base tratada:").strip().lower()
    
    if busca:
        resultados = [i for i in st.session_state.base_produtos if busca in i['Produto'].lower()]
        if resultados:
            st.table(resultados)
        else:
            st.warning("Produto não encontrado.")
    else:
        st.dataframe(st.session_state.base_produtos, use_container_width=True)
