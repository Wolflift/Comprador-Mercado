import os
import streamlit as st
import pandas as pd # Necessário para tratar a tabela conforme as fontes [4]
from playwright.sync_api import sync_playwright

os.system("playwright install chromium")

st.set_page_config(page_title="Beltrame Pro v13", page_icon="🛒", layout="wide")

# 1. MAPEAMENTO SEM A URL DE PROMOÇÕES (Conforme solicitado)
CATEGORIAS = {
    "Mercearia": "https://beltramesupermercados.com.br/categorias/mercearia",
    "Carnes e Aves": "https://beltramesupermercados.com.br/categorias/carnes-e-aves",
    "Hortifruti": "https://beltramesupermercados.com.br/categorias/hortifruti",
    "Bebidas Alcoólicas": "https://beltramesupermercados.com.br/categorias/bebidas-alcoolicas",
    "Bebidas": "https://beltramesupermercados.com.br/categorias/bebidas",
    "Laticínios e Frios": "https://beltramesupermercados.com.br/categorias/laticinios-e-frios",
    "Higiene e Beleza": "https://beltramesupermercados.com.br/categorias/higiene-e-beleza",
    "Limpeza": "https://beltramesupermercados.com.br/categorias/limpeza",
    "Peixes e Frutos do Mar": "https://beltramesupermercados.com.br/categorias/peixes-e-frutos-do-mar"
}

def limpar_valor(texto):
    try: return float(texto.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except: return 0.0

st.title("🛒 Engine Beltrame - Estabilidade Arrow")

if 'base_produtos' not in st.session_state:
    st.session_state.base_produtos = []

with st.sidebar:
    st.header("⚙️ Controle")
    if st.button("🚀 Iniciar Coleta"):
        with st.spinner("Extraindo e tratando dados de 9 seções..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    ctx = browser.new_context(user_agent="Mozilla/5.0")
                    page = ctx.new_page()

                    # Popup de Unidade
                    page.goto("https://beltramesupermercados.com.br", wait_until="domcontentloaded")
                    try:
                        btn = page.get_by_role("button", name="Confirmar", exact=False)
                        if btn.is_visible(timeout=5000): btn.click()
                    except: pass

                    base_temp = []
                    for nome_cat, url in CATEGORIAS.items():
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=40000)
                            for _ in range(5): 
                                page.mouse.wheel(0, 2000)
                                page.wait_for_timeout(1000)

                            page.wait_for_selector("text=R$", timeout=15000)
                            text_content = page.locator("body").inner_text()
                            lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                            
                            i = 0
                            while i < len(lines):
                                line = lines[i]
                                if 'R$' in line and any(c.isdigit() for c in line):
                                    if "kg" in line.lower() or "un" in line.lower():
                                        i += 1
                                        continue
                                    
                                    precos_detectados = [line]
                                    pula_proximo = False
                                    if i+1 < len(lines) and 'R$' in lines[i+1] and not any(x in lines[i+1].lower() for x in ["kg", "un"]):
                                        precos_detectados.append(lines[i+1])
                                        pula_proximo = True
                                    
                                    valores_num = [limpar_valor(p) for p in precos_detectados]
                                    
                                    if len(valores_num) >= 2:
                                        p_cheio = precos_detectados[valores_num.index(max(valores_num))]
                                        p_promo = precos_detectados[valores_num.index(min(valores_num))]
                                    else:
                                        p_cheio = precos_detectados
                                        p_promo = "-"

                                    nome_final = "Desconhecido"
                                    # Lista de ruído atualizada para ignorar palavras genéricas [Conversa]
                                    ruido = [
                                        'carrinho', 'adicionar', 'lista', 'indisponível', 'off', 'ver mais', 
                                        'comprar', 'oferta', '%', 'desconto', '360°', '360', 'unidade', 
                                        'kg', 'gramas', 'peso', 'mais', 'sucos', 'refrigerantes', 
                                        'bebidas', 'mercearia', 'carnes', 'aves', 'frutas', 'limpeza',
                                        'cafés, chás e achocolatados', 'açúcares e adoçantes', 'óleos', 
                                        'azeites', 'sopas instantâneas', 'cremes prontos', 'farináceos', 
                                        'massas', 'grãos, arrozes e feijões', 'snacks', 'bomboniere', 
                                        'salgadinhos', 'biscoitos', 'íntimos', 'banho', 'higiene' , 'Pratos Prontos'
                                    ]

                                    for j in range(i-1, i-9, -1):
                                        if j < 0: break
                                        txt = lines[j]
                                        txt_low = txt.lower()
                                        if any(c.isalpha() for c in txt) and 'R$' not in txt and len(txt) > 3:
                                            if not any(word == txt_low for word in ruido):
                                                nome_final = txt
                                                break
                                    
                                    if nome_final != "Desconhecido":
                                        base_temp.append({
                                            "Categoria": nome_cat,
                                            "Produto": nome_final.title(),
                                            "Preço Cheio": p_cheio,
                                            "Menor Valor": p_promo
                                        })
                                    
                                    if pula_proximo: i += 1 
                                i += 1
                        except:
                            i += 1
                            continue

                    st.session_state.base_produtos = base_temp
                    browser.close()
                    st.success(f"✅ Sucesso! {len(base_temp)} itens capturados.")
            except Exception as e:
                st.error(f"Erro na extração: {e}")

# 2. CORREÇÃO DO ERRO ARROW (Tratamento de Variáveis e Tabelas)
if st.session_state.base_produtos:
    st.divider()
    
    # Converte para DataFrame e força todos os tipos para string para evitar ArrowInvalid [3, 4]
    df = pd.DataFrame(st.session_state.base_produtos).astype(str)
    
    busca = st.text_input("🔍 Pesquisar na base:").strip().lower()
    if busca:
        res = df[df['Produto'].str.lower().str.contains(busca)]
        st.table(res) if not res.empty else st.warning("Não encontrado.")
    else:
        # Exibe o dataframe garantindo compatibilidade técnica
        st.dataframe(df, use_container_width=True)
