from datetime import datetime, timezone

import numpy as np
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

# controle de fluxo para evitar múltiplos cliques
if "buscando_dados" not in st.session_state:
    st.session_state["buscando_dados"] = False
if "estado_busca" not in st.session_state:
    st.session_state["estado_busca"] = None

if st.sidebar.button(
    f'Buscar dados em {estado_selecionado.upper()}',
    disabled=st.session_state["buscando_dados"],
    help="Aguarde a coleta terminar para iniciar uma nova busca.",
):
    st.session_state["buscando_dados"] = True
    st.session_state["estado_busca"] = estado_selecionado

if st.session_state["buscando_dados"]:
    estado_busca = st.session_state["estado_busca"] or estado_selecionado
    st.info("🔄 Coleta em andamento. Aguarde a conclusão…")
    with st.spinner("Coletando e processando dados…"):
        with st.status(f'Coletando dados de {estado_busca.upper()}(Até 100 páginas)', expanded=True) as status:
            st.write('Iniciando Scraping')

            df = scrape(estado_busca)

            if df is not None and not df.empty:
                st.write('Processando preços por m² ...')
                df = calcular_preco_m2(df)
                df['estado'] = estado_busca
                df['user_id'] = user.id
                df['criado_em'] = datetime.now(timezone.utc).isoformat()

                # Tipos numéricos coerentes com o banco
                df['m2'] = pd.to_numeric(df['m2'], errors='coerce').round(0).astype('Int64')
                df['preco_num'] = pd.to_numeric(df['preco_num'], errors='coerce')
                df['preco_m2'] = pd.to_numeric(df['preco_m2'], errors='coerce')

                # Remove NaN/Inf de forma confiável para JSON (compatível com pandas 3.x)
                df = df.replace([np.inf, -np.inf], np.nan)
                df = df.astype(object)
                df = df.where(pd.notna(df), None)

                try:
                    supabase.table('imoveis').delete().eq('user_id', user.id).eq('estado', estado_busca).execute()
                    supabase.table('imoveis').insert(df.to_dict(orient='records')).execute()
                    status.update(label='Concluído!', state='complete', expanded=False)
                    st.session_state["buscando_dados"] = False
                    st.rerun()
                except Exception as e:
                    status.update(label='Erro ao salvar no banco.', state='error')
                    st.session_state["buscando_dados"] = False
                    st.error(f'Erro ao salvar no Supabase: {e}')
            else:
                status.update(label="Erro ou nenhum dado encontrado.", state="error")
                st.session_state["buscando_dados"] = False

try:
    resposta = supabase.table('imoveis').select('*').eq('user_id', user.id).eq('estado', estado_selecionado).execute()
    dados = resposta.data or []
    if dados:
        tabela = pd.DataFrame(dados)
        st.subheader('Filtros da Análise')
        col_filtro1, col_filtro2 = st.columns(2)

        with col_filtro1:
            # filtro cidades
            contagem_cidades = tabela['cidade'].astype(str).value_counts()
            top_10_cidades = contagem_cidades.head(10).index.tolist()
            todas_cidades = sorted(tabela['cidade'].unique().astype(str))
            cidades_no_arquivo = top_10_cidades + todas_cidades
            filtro_cidade = st.multiselect('1. Selecione a cidade', cidades_no_arquivo)

            # aplicar filtro cidade
            if filtro_cidade:
                tabela_filtrada = tabela[tabela['cidade'].isin(filtro_cidade)]
            else:
                tabela_filtrada = tabela

            if 'preco_num' in tabela_filtrada.columns:
                valores_preco = tabela_filtrada['preco_num'].dropna()
                if not valores_preco.empty:
                    minimo_preco = float(valores_preco.min())
                    maximo_preco = float(valores_preco.max())
                    if minimo_preco < maximo_preco:
                        faixa_preco = st.slider(
                            'Preço do imóvel (R$)',
                            min_value=minimo_preco,
                            max_value=maximo_preco,
                            value=(minimo_preco, maximo_preco),
                            step=max((maximo_preco - minimo_preco) / 100, 1.0)
                        )
                        tabela_filtrada = tabela_filtrada[
                            tabela_filtrada['preco_num'].between(faixa_preco[0], faixa_preco[1])
                        ]

            if 'preco_m2' in tabela_filtrada.columns:
                valores_m2 = tabela_filtrada['preco_m2'].dropna()
                if not valores_m2.empty:
                    minimo_m2 = float(valores_m2.min())
                    maximo_m2 = float(valores_m2.max())
                    if minimo_m2 < maximo_m2:
                        faixa_m2 = st.slider(
                            'Preço por m² (R$)',
                            min_value=minimo_m2,
                            max_value=maximo_m2,
                            value=(minimo_m2, maximo_m2),
                            step=max((maximo_m2 - minimo_m2) / 100, 1.0)
                        )
                        tabela_filtrada = tabela_filtrada[
                            tabela_filtrada['preco_m2'].between(faixa_m2[0], faixa_m2[1])
                        ]
        with col_filtro2:
            # filtro cidades
            bairros_diponiveis = sorted(tabela_filtrada['bairro'].unique().astype(str))
            filtro_bairros = st.multiselect('2. Comparar por bairros', bairros_diponiveis)

            # aplicar filtro bairros ou não
            if filtro_bairros:
                tabela_final = tabela_filtrada[tabela_filtrada['bairro'].isin(filtro_bairros)]
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
                mediana_selecao = tabela_final['preco_m2'].median()
                col2.metric('Mediana Preço/m² (Seleção)', f'R$ {mediana_selecao:.2f}')
            # Graficos

            if 'preco_num' in tabela_final.columns:
                mediana_preco = tabela_final['preco_num'].median()
                col3.metric("Preço Mediano do Imóvel", f"R$ {mediana_preco:,.2f}")

            st.subheader('Insights & Qualidade dos Dados')
            insight_tab1, insight_tab2, insight_tab3 = st.tabs([
                '🏙️ Ranking',
                '💡 Oportunidades',
                '✅ Qualidade'
            ])

            with insight_tab1:
                col_rank1, col_rank2 = st.columns(2)

                with col_rank1:
                    st.caption('Top cidades por volume de anúncios')
                    ranking_cidades = (
                        tabela.groupby('cidade')
                        .size()
                        .sort_values(ascending=False)
                        .head(10)
                    )
                    st.bar_chart(ranking_cidades)

                with col_rank2:
                    st.caption('Cidades com maior preço mediano por m²')
                    ranking_preco_cidades = (
                        tabela.groupby('cidade')['preco_m2']
                        .median()
                        .sort_values(ascending=False)
                        .head(10)
                    )
                    st.bar_chart(ranking_preco_cidades)

                st.caption('Bairros com maior volume (seleção atual)')
                ranking_bairros = (
                    tabela_final.groupby('bairro')
                    .size()
                    .sort_values(ascending=False)
                    .head(15)
                    .rename('anuncios')
                    .reset_index()
                )
                st.dataframe(ranking_bairros, use_container_width=True, hide_index=True)

            with insight_tab2:
                st.caption('Bairros com preço/m² abaixo da mediana da cidade')
                bairro_mediana = tabela.groupby(['cidade', 'bairro'])['preco_m2'].median().reset_index()
                cidade_mediana = tabela.groupby('cidade')['preco_m2'].median().rename('mediana_cidade')
                oportunidades = bairro_mediana.merge(cidade_mediana, on='cidade', how='left')
                oportunidades['diff_percentual'] = (
                    (oportunidades['preco_m2'] - oportunidades['mediana_cidade'])
                    / oportunidades['mediana_cidade']
                ) * 100
                oportunidades = oportunidades.sort_values('diff_percentual').head(15)
                oportunidades['diff_percentual'] = oportunidades['diff_percentual'].round(2)
                st.dataframe(
                    oportunidades,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'cidade': st.column_config.TextColumn('Cidade'),
                        'bairro': st.column_config.TextColumn('Bairro'),
                        'preco_m2': st.column_config.NumberColumn('Mediana Bairro (R$/m²)', format='%.2f'),
                        'mediana_cidade': st.column_config.NumberColumn('Mediana Cidade (R$/m²)', format='%.2f'),
                        'diff_percentual': st.column_config.NumberColumn('Diferença %', format='%.2f'),
                    }
                )

            with insight_tab3:
                total_registros = len(tabela_final)
                if total_registros > 0:
                    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
                    faltando_m2 = tabela_final['m2'].isna().mean() * 100 if 'm2' in tabela_final.columns else 0
                    faltando_bairro = tabela_final['bairro'].isna().mean() * 100 if 'bairro' in tabela_final.columns else 0
                    faltando_cidade = tabela_final['cidade'].isna().mean() * 100 if 'cidade' in tabela_final.columns else 0
                    faltando_preco = tabela_final['preco_num'].isna().mean() * 100 if 'preco_num' in tabela_final.columns else 0
                    col_q1.metric('% sem m²', f'{faltando_m2:.1f}%')
                    col_q2.metric('% sem bairro', f'{faltando_bairro:.1f}%')
                    col_q3.metric('% sem cidade', f'{faltando_cidade:.1f}%')
                    col_q4.metric('% sem preço', f'{faltando_preco:.1f}%')

            st.subheader('Análises Avançadas')
            avanc_tab1, avanc_tab2, avanc_tab3 = st.tabs([
                '🧩 Segmentação',
                '🚩 Anúncios suspeitos',
                '📈 Histórico'
            ])

            with avanc_tab1:
                st.caption('Segmentação simples por faixa de preço/m² (quantis)')
                tabela_segmento = tabela_final.copy()
                if 'preco_m2' in tabela_segmento.columns:
                    valores_segmento = tabela_segmento['preco_m2'].dropna()
                    if valores_segmento.nunique() >= 3:
                        tabela_segmento['segmento'] = pd.qcut(
                            tabela_segmento['preco_m2'],
                            q=3,
                            labels=['Baixo', 'Médio', 'Alto']
                        )
                        resumo_segmento = (
                            tabela_segmento.groupby('segmento')
                            .agg(
                                anuncios=('segmento', 'size'),
                                mediana_m2=('preco_m2', 'median'),
                                mediana_preco=('preco_num', 'median')
                            )
                            .reset_index()
                        )
                        st.dataframe(
                            resumo_segmento,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'segmento': st.column_config.TextColumn('Segmento'),
                                'anuncios': st.column_config.NumberColumn('Anúncios'),
                                'mediana_m2': st.column_config.NumberColumn('Mediana R$/m²', format='%.2f'),
                                'mediana_preco': st.column_config.NumberColumn('Mediana Preço (R$)', format='%.2f'),
                            }
                        )
                    else:
                        st.info('Pouca variação para segmentar os dados.')
                else:
                    st.info('Preço por m² indisponível para segmentação.')

            with avanc_tab2:
                st.caption('Detecção simples de outliers por quantis')
                suspeitos = tabela_final.copy()
                suspeitos['motivo'] = ''

                if 'preco_m2' in suspeitos.columns:
                    p05_m2 = suspeitos['preco_m2'].quantile(0.05)
                    p95_m2 = suspeitos['preco_m2'].quantile(0.95)
                    suspeitos.loc[suspeitos['preco_m2'] < p05_m2, 'motivo'] += 'Preço/m² muito baixo; '
                    suspeitos.loc[suspeitos['preco_m2'] > p95_m2, 'motivo'] += 'Preço/m² muito alto; '

                if 'preco_num' in suspeitos.columns:
                    p05_preco = suspeitos['preco_num'].quantile(0.05)
                    p95_preco = suspeitos['preco_num'].quantile(0.95)
                    suspeitos.loc[suspeitos['preco_num'] < p05_preco, 'motivo'] += 'Preço total muito baixo; '
                    suspeitos.loc[suspeitos['preco_num'] > p95_preco, 'motivo'] += 'Preço total muito alto; '

                if 'm2' in suspeitos.columns:
                    p05_area = suspeitos['m2'].quantile(0.05)
                    p95_area = suspeitos['m2'].quantile(0.95)
                    suspeitos.loc[suspeitos['m2'] < p05_area, 'motivo'] += 'Área muito baixa; '
                    suspeitos.loc[suspeitos['m2'] > p95_area, 'motivo'] += 'Área muito alta; '

                suspeitos = suspeitos[suspeitos['motivo'].str.strip() != '']
                suspeitos = suspeitos.head(20)

                if not suspeitos.empty:
                    st.dataframe(
                        suspeitos[[
                            'nome',
                            'cidade',
                            'bairro',
                            'm2',
                            'preco_num',
                            'preco_m2',
                            'motivo',
                            'link'
                        ]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'nome': st.column_config.TextColumn('Imóvel'),
                            'cidade': st.column_config.TextColumn('Cidade'),
                            'bairro': st.column_config.TextColumn('Bairro'),
                            'm2': st.column_config.NumberColumn('m²', format='%d'),
                            'preco_num': st.column_config.NumberColumn('Preço (R$)', format='%.2f'),
                            'preco_m2': st.column_config.NumberColumn('Preço/m² (R$)', format='%.2f'),
                            'motivo': st.column_config.TextColumn('Motivo'),
                            'link': st.column_config.LinkColumn('Link'),
                        }
                    )
                else:
                    st.info('Nenhum anúncio suspeito identificado com os critérios atuais.')

            with avanc_tab3:
                if 'criado_em' in tabela.columns:
                    historico = tabela.copy()
                    historico['criado_em'] = pd.to_datetime(historico['criado_em'], errors='coerce')
                    historico = historico.dropna(subset=['criado_em'])
                    historico['dia'] = historico['criado_em'].dt.date

                    if historico['dia'].nunique() > 1:
                        historico_agg = (
                            historico.groupby('dia')
                            .agg(
                                mediana_m2=('preco_m2', 'median'),
                                mediana_preco=('preco_num', 'median'),
                                anuncios=('dia', 'size')
                            )
                            .reset_index()
                        )
                        st.line_chart(
                            historico_agg.set_index('dia')[['mediana_m2', 'mediana_preco']]
                        )
                        st.dataframe(
                            historico_agg,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'dia': st.column_config.TextColumn('Dia'),
                                'mediana_m2': st.column_config.NumberColumn('Mediana R$/m²', format='%.2f'),
                                'mediana_preco': st.column_config.NumberColumn('Mediana Preço (R$)', format='%.2f'),
                                'anuncios': st.column_config.NumberColumn('Anúncios'),
                            }
                        )
                    else:
                        st.info('Histórico ainda não disponível. Faça coletas em dias diferentes para comparar.')
                else:
                    st.info('Histórico indisponível: campo criado_em não encontrado.')

            st.subheader('visualização Gráfica')
            tab1, tab2 = st.tabs(['📊 Gráficos', "📄 Dados Detalhados"])

            with tab1:
                st.caption(f'Exibindo {titulo_grafico}')
                dados_agrupados = tabela_final.groupby('bairro')['preco_m2'].median().sort_values(ascending=False)

                if not filtro_bairros:
                    dados_grafico_exibir = dados_agrupados.head(15)
                else:
                    dados_grafico_exibir = dados_agrupados
                st.bar_chart(dados_grafico_exibir)

            with tab2:
                colunas_ocultar = {"id", "user_id", "criado_em"}
                colunas_exibir = [col for col in tabela_final.columns if col not in colunas_ocultar]
                tabela_exibir = tabela_final[colunas_exibir].copy()

                if "preco_num" in tabela_exibir.columns:
                    tabela_exibir["preco_num"] = tabela_exibir["preco_num"].apply(
                        lambda valor: f"R$ {valor:,.2f}" if pd.notna(valor) else ""
                    )
                if "preco_m2" in tabela_exibir.columns:
                    tabela_exibir["preco_m2"] = tabela_exibir["preco_m2"].apply(
                        lambda valor: f"R$ {valor:,.2f}" if pd.notna(valor) else ""
                    )

                st.dataframe(
                    tabela_exibir,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "nome": st.column_config.TextColumn("Imóvel"),
                        "preco": st.column_config.TextColumn("Preço"),
                        "preco_num": st.column_config.TextColumn("Preço Num."),
                        "preco_m2": st.column_config.TextColumn("Preço/m²"),
                        "m2": st.column_config.NumberColumn("m²", format="%d"),
                        "cidade": st.column_config.TextColumn("Cidade"),
                        "bairro": st.column_config.TextColumn("Bairro"),
                        "estado": st.column_config.TextColumn("UF"),
                        "link": st.column_config.LinkColumn("Link"),
                    },
                )

                csv_export = tabela_exibir.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label='⬇️ Baixar CSV filtrado',
                    data=csv_export,
                    file_name='imoveis_filtrados.csv',
                    mime='text/csv'
                )

        else:
            st.warning("Nenhum dado encontrado para essa combinação de filtros.")
    else:
        if not st.session_state.get("buscando_dados"):
            st.info('👈 Selecione um estado na barra lateral e clique em "Buscar Dados" para começar.')
except Exception as e:
    st.error(f'Erro ao consultar dados no Supabase: {e}')

# 2 metricas
