from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client

from scraping import scrape
from calcular_preco_m2 import calcular_preco_m2

st.set_page_config(page_title="Dashboard", layout="wide")

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_ANON_KEY"]
)


def auth_screen():
    st.title("🔐 Login")
    tab_login, tab_signup = st.tabs(["Entrar", "Cadastrar"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state["user"] = res.user
                st.success("Login realizado!")
                st.rerun()
            except Exception:
                st.error("Erro ao realizar login")

    with tab_signup:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Senha", type="password", key="signup_pass")
        if st.button("Cadastrar"):
            try:
                supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                st.success("Conta criada! Realize o login.")
            except Exception:
                st.error("Erro ao cadastrar")


if "user" not in st.session_state:
    auth_screen()
    st.stop()

user = st.session_state["user"]

# título
st.title('📊 Dashboard Imobiliário OLX')

# Lateral
st.sidebar.header('Configurações da Coleta')

lista_estados = ["ac", "al", "ap", "am", "ba", "ce", "df", "es", "go", "ma", "mt", "ms", "mg", "pa", "pb", "pr", "pe",
                 "pi", "rj", "rn", "rs", "ro", "rr", "sc", "sp", "se", "to"]

# seleção e filtro de dados
estado_selecionado = st.sidebar.selectbox('Escolha o estado da coleta', lista_estados, index=15)

if st.sidebar.button(f'Buscar dados em {estado_selecionado.upper()}'):
    with st.status(f'Coletando dados de {estado_selecionado.upper()}(Até 100 páginas)', expanded=True) as status:
        st.write('Iniciando Scraping')

        df = scrape(estado_selecionado)

        if df is not None and not df.empty:
            st.write('Processando preços por m² ...')
            df = calcular_preco_m2(df)
            df['estado'] = estado_selecionado
            df['user_id'] = user.id
            df['criado_em'] = datetime.now(timezone.utc).isoformat()
            df = df.where(pd.notnull(df), None)

            try:
                supabase.table('imoveis').delete().eq('user_id', user.id).eq('estado', estado_selecionado).execute()
                supabase.table('imoveis').insert(df.to_dict(orient='records')).execute()
                status.update(label='Concluído!', state='complete', expanded=False)
                st.rerun()
            except Exception as e:
                status.update(label='Erro ao salvar no banco.', state='error')
                st.error(f'Erro ao salvar no Supabase: {e}')
        else:
            status.update(label="Erro ou nenhum dado encontrado.", state="error")

try:
    resposta = supabase.table('imoveis').select('*').eq('user_id', user.id).eq('estado', estado_selecionado).execute()
    dados = resposta.data or []
    if dados:
        tabela = pd.DataFrame(dados)
        st.subheader('Filtros da Análise')
        col_filtro1, col_filtro2 = st.columns(2)

        with col_filtro1:
            # filtro cidades
            cidades_no_arquivo = sorted(tabela['cidade'].unique().astype(str))
            filtro_cidade = st.multiselect('1. Selecione a cidade', cidades_no_arquivo)

            # aplicar filtro cidade
            if filtro_cidade:
                tabela_filtrada = tabela[tabela['cidade'].isin(filtro_cidade)]
            else:
                tabela_filtrada = tabela
        with col_filtro2:
            # filtro cidades
            bairros_diponiveis = sorted(tabela_filtrada['bairro'].unique().astype(str))
            filtro_bairros = st.multiselect('2. Comparar por bairros', bairros_diponiveis)

            # aplicar filtro bairros ou não
            if filtro_bairros:
                tabela_final = tabela_filtrada[tabela['bairro'].isin(filtro_bairros)]
                titulo_grafico = "Comparativo dos Bairros Selecionados"
            else:
                tabela_final = tabela_filtrada
                titulo_grafico = "Top 15 Bairros (Geral)"

        # KPIS
        st.divider()
        if not tabela_final.empty:
            col1, col2, col3 = st.columns(3)

            # total de imóveis
            col1.metric("Total de Imóveis", len(tabela_final))

            if 'preco_m2' in tabela_final.columns:
                media_selecao = tabela_final['preco_m2'].mean()
                col2.metric('Média Preço/m² (Seleção)', f'R$ {media_selecao:.2f}')
            # Graficos

            if 'preco_num' in tabela_final.columns:
                media_preco = tabela_final['preco_num'].mean()
                col3.metric("Preço Médio do Imóvel", f"R$ {media_preco:,.2f}")

            st.subheader('visualização Gráfica')
            tab1, tab2 = st.tabs(['📊 Gráficos', "📄 Dados Detalhados"])

            with tab1:
                st.caption(f'Exibindo {titulo_grafico}')
                dados_agrupados = tabela_final.groupby('bairro')['preco_m2'].mean().sort_values(ascending=False)

                if not filtro_bairros:
                    dados_grafico_exibir = dados_agrupados.head(15)
                else:
                    dados_grafico_exibir = dados_agrupados
                st.bar_chart(dados_grafico_exibir)

            with tab2:
                st.dataframe(tabela_final, use_container_width=True)

        else:
            st.warning("Nenhum dado encontrado para essa combinação de filtros.")
    else:
        st.info('👈 Selecione um estado na barra lateral e clique em "Buscar Dados" para começar.')
except Exception as e:
    st.error(f'Erro ao consultar dados no Supabase: {e}')

# 2 metricas
