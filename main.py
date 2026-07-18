from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Dashboard", layout="wide")


# ⚠️ Dois clients: um público (leitura) e um administrativo (escrita)
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])
supabase_admin = create_client(
    st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
)


# título
st.title("📊 Dashboard Imobiliário")
st.caption("Dados atualizados automaticamente de hora em hora via coleta agendada.")


# Lateral
st.sidebar.header("Configurações da Coleta")


lista_estados = [
    "ac",
    "al",
    "ap",
    "am",
    "ba",
    "ce",
    "df",
    "es",
    "go",
    "ma",
    "mt",
    "ms",
    "mg",
    "pa",
    "pb",
    "pr",
    "pe",
    "pi",
    "rj",
    "rn",
    "rs",
    "ro",
    "rr",
    "sc",
    "sp",
    "se",
    "to",
]


# seleção e filtro de dados
estado_selecionado = st.sidebar.selectbox(
    "Escolha o estado da coleta", lista_estados, index=15
)


def _base_query(table_name: str):
    return (
        supabase.table(table_name)
        .select("*")
        .is_("user_id", "null")
        .eq("estado", estado_selecionado)
    )


try:
    resposta = _base_query("imoveis").execute()
    dados = resposta.data or []
    if dados:
        tabela = pd.DataFrame(dados)
        st.subheader("Filtros da Análise")
        col_filtro1, col_filtro2 = st.columns(2)

        with col_filtro1:
            # filtro cidades
            contagem_cidades = tabela["cidade"].astype(str).value_counts()
            top_10_cidades = contagem_cidades.head(10).index.tolist()
            todas_cidades = sorted(tabela["cidade"].unique().astype(str))
            cidades_no_arquivo = top_10_cidades + todas_cidades
            filtro_cidade = st.multiselect("1. Selecione a cidade", cidades_no_arquivo)

            # aplicar filtro cidade
            if filtro_cidade:
                tabela_filtrada = tabela[tabela["cidade"].isin(filtro_cidade)]
            else:
                tabela_filtrada = tabela

            if "preco_num" in tabela_filtrada.columns:
                valores_preco = tabela_filtrada["preco_num"].dropna()
                if not valores_preco.empty:
                    minimo_preco = float(valores_preco.min())
                    maximo_preco = float(valores_preco.max())
                    if minimo_preco < maximo_preco:
                        faixa_preco = st.slider(
                            "Preço do imóvel (R$)",
                            min_value=minimo_preco,
                            max_value=maximo_preco,
                            value=(minimo_preco, maximo_preco),
                            step=max((maximo_preco - minimo_preco) / 100, 1.0),
                        )
                        tabela_filtrada = tabela_filtrada[
                            tabela_filtrada["preco_num"].between(
                                faixa_preco[0], faixa_preco[1]
                            )
                        ]

            if "preco_m2" in tabela_filtrada.columns:
                valores_m2 = tabela_filtrada["preco_m2"].dropna()
                if not valores_m2.empty:
                    minimo_m2 = float(valores_m2.min())
                    maximo_m2 = float(valores_m2.max())
                    if minimo_m2 < maximo_m2:
                        faixa_m2 = st.slider(
                            "Preço por m² (R$)",
                            min_value=minimo_m2,
                            max_value=maximo_m2,
                            value=(minimo_m2, maximo_m2),
                            step=max((maximo_m2 - minimo_m2) / 100, 1.0),
                        )
                        tabela_filtrada = tabela_filtrada[
                            tabela_filtrada["preco_m2"].between(
                                faixa_m2[0], faixa_m2[1]
                            )
                        ]
        with col_filtro2:
            # filtro bairros
            bairros_diponiveis = sorted(tabela_filtrada["bairro"].unique().astype(str))
            filtro_bairros = st.multiselect(
                "2. Comparar por bairros", bairros_diponiveis
            )

            # aplicar filtro bairros ou não
            if filtro_bairros:
                tabela_final = tabela_filtrada[
                    tabela_filtrada["bairro"].isin(filtro_bairros)
                ]
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

            if "preco_m2" in tabela_final.columns:
                mediana_selecao = tabela_final["preco_m2"].median()
                col2.metric("Mediana Preço/m² (Seleção)", f"R$ {mediana_selecao:.2f}")

            if "preco_num" in tabela_final.columns:
                mediana_preco = tabela_final["preco_num"].median()
                col3.metric("Preço Mediano do Imóvel", f"R$ {mediana_preco:,.2f}")

            st.subheader("Insights & Qualidade dos Dados")
            insight_tab1, insight_tab2, insight_tab3 = st.tabs(
                ["🏙️ Ranking", "💡 Oportunidades", "✅ Qualidade"]
            )

            with insight_tab1:
                col_rank1, col_rank2 = st.columns(2)

                with col_rank1:
                    st.caption("Top cidades por volume de anúncios")
                    ranking_cidades = (
                        tabela.groupby("cidade")
                        .size()
                        .sort_values(ascending=False)
                        .head(10)
                    )
                    st.bar_chart(ranking_cidades)

                with col_rank2:
                    st.caption("Cidades com maior preço mediano por m²")
                    ranking_preco_cidades = (
                        tabela.groupby("cidade")["preco_m2"]
                        .median()
                        .sort_values(ascending=False)
                        .head(10)
                    )
                    st.bar_chart(ranking_preco_cidades)

                st.caption("Bairros com maior volume (seleção atual)")
                ranking_bairros = (
                    tabela_final.groupby("bairro")
                    .size()
                    .sort_values(ascending=False)
                    .head(15)
                    .rename("anuncios")
                    .reset_index()
                )
                st.dataframe(ranking_bairros, use_container_width=True, hide_index=True)

            with insight_tab2:
                st.caption("Bairros com preço/m² abaixo da mediana da cidade")
                bairro_mediana = (
                    tabela.groupby(["cidade", "bairro"])["preco_m2"]
                    .median()
                    .reset_index()
                )
                cidade_mediana = (
                    tabela.groupby("cidade")["preco_m2"]
                    .median()
                    .rename("mediana_cidade")
                )
                oportunidades = bairro_mediana.merge(
                    cidade_mediana, on="cidade", how="left"
                )
                oportunidades["diff_percentual"] = (
                    (oportunidades["preco_m2"] - oportunidades["mediana_cidade"])
                    / oportunidades["mediana_cidade"]
                ) * 100
                oportunidades = oportunidades.sort_values("diff_percentual").head(15)
                oportunidades["diff_percentual"] = oportunidades[
                    "diff_percentual"
                ].round(2)
                st.dataframe(
                    oportunidades,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "cidade": st.column_config.TextColumn("Cidade"),
                        "bairro": st.column_config.TextColumn("Bairro"),
                        "preco_m2": st.column_config.NumberColumn(
                            "Mediana Bairro (R$/m²)", format="%.2f"
                        ),
                        "mediana_cidade": st.column_config.NumberColumn(
                            "Mediana Cidade (R$/m²)", format="%.2f"
                        ),
                        "diff_percentual": st.column_config.NumberColumn(
                            "Diferença %", format="%.2f"
                        ),
                    },
                )

            with insight_tab3:
                total_registros = len(tabela_final)
                if total_registros > 0:
                    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
                    faltando_m2 = (
                        tabela_final["m2"].isna().mean() * 100
                        if "m2" in tabela_final.columns
                        else 0
                    )
                    faltando_bairro = (
                        tabela_final["bairro"].isna().mean() * 100
                        if "bairro" in tabela_final.columns
                        else 0
                    )
                    faltando_cidade = (
                        tabela_final["cidade"].isna().mean() * 100
                        if "cidade" in tabela_final.columns
                        else 0
                    )
                    faltando_preco = (
                        tabela_final["preco_num"].isna().mean() * 100
                        if "preco_num" in tabela_final.columns
                        else 0
                    )
                    col_q1.metric("% sem m²", f"{faltando_m2:.1f}%")
                    col_q2.metric("% sem bairro", f"{faltando_bairro:.1f}%")
                    col_q3.metric("% sem cidade", f"{faltando_cidade:.1f}%")
                    col_q4.metric("% sem preço", f"{faltando_preco:.1f}%")

            st.subheader("Análises Avançadas")
            avanc_tab1, avanc_tab2, avanc_tab3 = st.tabs(
                ["🧩 Segmentação", "🚩 Anúncios suspeitos", "📈 Histórico"]
            )

            with avanc_tab1:
                st.caption("Segmentação simples por faixa de preço/m² (quantis)")
                tabela_segmento = tabela_final.copy()
                if "preco_m2" in tabela_segmento.columns:
                    valores_segmento = tabela_segmento["preco_m2"].dropna()
                    if valores_segmento.nunique() >= 3:
                        tabela_segmento["segmento"] = pd.qcut(
                            tabela_segmento["preco_m2"],
                            q=3,
                            labels=["Baixo", "Médio", "Alto"],
                        )
                        resumo_segmento = (
                            tabela_segmento.groupby("segmento")
                            .agg(
                                anuncios=("segmento", "size"),
                                mediana_m2=("preco_m2", "median"),
                                mediana_preco=("preco_num", "median"),
                            )
                            .reset_index()
                        )
                        st.dataframe(
                            resumo_segmento,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "segmento": st.column_config.TextColumn("Segmento"),
                                "anuncios": st.column_config.NumberColumn("Anúncios"),
                                "mediana_m2": st.column_config.NumberColumn(
                                    "Mediana R$/m²", format="%.2f"
                                ),
                                "mediana_preco": st.column_config.NumberColumn(
                                    "Mediana Preço (R$)", format="%.2f"
                                ),
                            },
                        )
                    else:
                        st.info("Pouca variação para segmentar os dados.")
                else:
                    st.info("Preço por m² indisponível para segmentação.")

            with avanc_tab2:
                st.caption("Detecção simples de outliers por quantis")
                suspeitos = tabela_final.copy()
                suspeitos["motivo"] = ""

                if "preco_m2" in suspeitos.columns:
                    p05_m2 = suspeitos["preco_m2"].quantile(0.05)
                    p95_m2 = suspeitos["preco_m2"].quantile(0.95)
                    suspeitos.loc[
                        suspeitos["preco_m2"] < p05_m2, "motivo"
                    ] += "Preço/m² muito baixo; "
                    suspeitos.loc[
                        suspeitos["preco_m2"] > p95_m2, "motivo"
                    ] += "Preço/m² muito alto; "

                if "preco_num" in suspeitos.columns:
                    p05_preco = suspeitos["preco_num"].quantile(0.05)
                    p95_preco = suspeitos["preco_num"].quantile(0.95)
                    suspeitos.loc[
                        suspeitos["preco_num"] < p05_preco, "motivo"
                    ] += "Preço total muito baixo; "
                    suspeitos.loc[
                        suspeitos["preco_num"] > p95_preco, "motivo"
                    ] += "Preço total muito alto; "

                if "m2" in suspeitos.columns:
                    p05_area = suspeitos["m2"].quantile(0.05)
                    p95_area = suspeitos["m2"].quantile(0.95)
                    suspeitos.loc[
                        suspeitos["m2"] < p05_area, "motivo"
                    ] += "Área muito baixa; "
                    suspeitos.loc[
                        suspeitos["m2"] > p95_area, "motivo"
                    ] += "Área muito alta; "

                suspeitos = suspeitos[suspeitos["motivo"].str.strip() != ""]
                suspeitos = suspeitos.head(20)

                if not suspeitos.empty:
                    st.dataframe(
                        suspeitos[
                            [
                                "nome",
                                "cidade",
                                "bairro",
                                "m2",
                                "preco_num",
                                "preco_m2",
                                "motivo",
                                "link",
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "nome": st.column_config.TextColumn("Imóvel"),
                            "cidade": st.column_config.TextColumn("Cidade"),
                            "bairro": st.column_config.TextColumn("Bairro"),
                            "m2": st.column_config.NumberColumn("m²", format="%d"),
                            "preco_num": st.column_config.NumberColumn(
                                "Preço (R$)", format="%.2f"
                            ),
                            "preco_m2": st.column_config.NumberColumn(
                                "Preço/m² (R$)", format="%.2f"
                            ),
                            "motivo": st.column_config.TextColumn("Motivo"),
                            "link": st.column_config.LinkColumn("Link"),
                        },
                    )
                else:
                    st.info(
                        "Nenhum anúncio suspeito identificado com os critérios atuais."
                    )

            with avanc_tab3:
                if "criado_em" in tabela.columns:
                    historico = tabela.copy()
                    historico["criado_em"] = pd.to_datetime(
                        historico["criado_em"], errors="coerce"
                    )
                    historico = historico.dropna(subset=["criado_em"])
                    historico["dia"] = historico["criado_em"].dt.date

                    if historico["dia"].nunique() > 1:
                        historico_agg = (
                            historico.groupby("dia")
                            .agg(
                                mediana_m2=("preco_m2", "median"),
                                mediana_preco=("preco_num", "median"),
                                anuncios=("dia", "size"),
                            )
                            .reset_index()
                        )
                        st.line_chart(
                            historico_agg.set_index("dia")[
                                ["mediana_m2", "mediana_preco"]
                            ]
                        )
                        st.dataframe(
                            historico_agg,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "dia": st.column_config.TextColumn("Dia"),
                                "mediana_m2": st.column_config.NumberColumn(
                                    "Mediana R$/m²", format="%.2f"
                                ),
                                "mediana_preco": st.column_config.NumberColumn(
                                    "Mediana Preço (R$)", format="%.2f"
                                ),
                                "anuncios": st.column_config.NumberColumn("Anúncios"),
                            },
                        )
                    else:
                        st.info(
                            "Histórico ainda não disponível. Faça coletas em dias diferentes para comparar."
                        )
                else:
                    st.info("Histórico indisponível: campo criado_em não encontrado.")

            st.subheader("Histórico Temporal (por região)")
            try:
                if "criado_em" in tabela.columns:
                    hoje = datetime.now().date()
                    data_inicio, data_fim = st.date_input(
                        "Período",
                        value=(hoje - timedelta(days=30), hoje),
                        help="Selecione o período para analisar a evolução temporal.",
                    )
                else:
                    data_inicio, data_fim = (None, None)

                fonte_disponivel = sorted(
                    tabela.get("fonte", pd.Series()).dropna().unique().tolist()
                )
                filtro_fonte = (
                    st.multiselect("Filtrar por fonte", fonte_disponivel)
                    if fonte_disponivel
                    else []
                )

                query_historico = (
                    supabase.table("imoveis_historico")
                    .select("*")
                    .is_("user_id", "null")
                    .eq("estado", estado_selecionado)
                )

                if data_inicio and data_fim:
                    query_historico = query_historico.gte(
                        "criado_em", f"{data_inicio}T00:00:00Z"
                    ).lte("criado_em", f"{data_fim}T23:59:59Z")

                if filtro_cidade:
                    query_historico = query_historico.in_("cidade", filtro_cidade)

                if filtro_bairros:
                    query_historico = query_historico.in_("bairro", filtro_bairros)

                if filtro_fonte:
                    query_historico = query_historico.in_("fonte", filtro_fonte)

                historico_resp = query_historico.execute()
                historico_dados = historico_resp.data or []

                if historico_dados:
                    historico_df = pd.DataFrame(historico_dados)
                    historico_df["criado_em"] = pd.to_datetime(
                        historico_df["criado_em"], errors="coerce"
                    )
                    historico_df = historico_df.dropna(subset=["criado_em"])
                    historico_df["dia"] = historico_df["criado_em"].dt.date

                    historico_agg = (
                        historico_df.groupby("dia")
                        .agg(
                            mediana_m2=("preco_m2", "median"),
                            mediana_preco=("preco_num", "median"),
                            anuncios=("dia", "size"),
                        )
                        .reset_index()
                        .sort_values("dia")
                    )

                    col_hist1, col_hist2 = st.columns(2)
                    with col_hist1:
                        st.caption("Evolução da mediana (R$/m²)")
                        st.line_chart(historico_agg.set_index("dia")[["mediana_m2"]])

                    with col_hist2:
                        st.caption("Quantidade de imóveis ao longo do tempo")
                        st.line_chart(historico_agg.set_index("dia")[["anuncios"]])
                else:
                    st.info(
                        "Sem dados históricos para o período e filtros selecionados."
                    )
            except Exception as historico_erro:
                st.info(f"Histórico temporal indisponível: {historico_erro}")

            st.subheader("Histórico de Pesquisas")
            try:
                historico_pesquisas = (
                    supabase.table("pesquisas")
                    .select("*")
                    .is_("user_id", "null")
                    .order("criado_em", desc=True)
                    .execute()
                )
                dados_pesquisas = historico_pesquisas.data or []
                if dados_pesquisas:
                    df_pesquisas = pd.DataFrame(dados_pesquisas)
                    df_pesquisas["criado_em"] = pd.to_datetime(
                        df_pesquisas["criado_em"], errors="coerce"
                    )
                    df_pesquisas = df_pesquisas.dropna(subset=["criado_em"])

                    if not df_pesquisas.empty:
                        df_grafico = df_pesquisas.sort_values("criado_em")
                        col_hist1, col_hist2 = st.columns(2)
                        with col_hist1:
                            st.caption("Evolução das medianas por pesquisa")
                            colunas_grafico = []
                            if "mediana_preco_m2" in df_grafico.columns:
                                colunas_grafico.append("mediana_preco_m2")
                            if "mediana_preco_total" in df_grafico.columns:
                                colunas_grafico.append("mediana_preco_total")
                            if colunas_grafico:
                                st.line_chart(
                                    df_grafico.set_index("criado_em")[colunas_grafico]
                                )

                        with col_hist2:
                            st.caption("Quantidade de anúncios por pesquisa")
                            if "qtd_anuncios" in df_grafico.columns:
                                st.line_chart(
                                    df_grafico.set_index("criado_em")[["qtd_anuncios"]]
                                )

                    st.dataframe(
                        df_pesquisas.sort_values("criado_em", ascending=False),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "criado_em": st.column_config.TextColumn("Data"),
                            "estado": st.column_config.TextColumn("Estado"),
                            "qtd_anuncios": st.column_config.NumberColumn(
                                "Anúncios", format="%d"
                            ),
                            "mediana_preco_m2": st.column_config.NumberColumn(
                                "Mediana R$/m²", format="%.2f"
                            ),
                            "mediana_preco_total": st.column_config.NumberColumn(
                                "Mediana Preço (R$)", format="%.2f"
                            ),
                        },
                    )
                else:
                    st.info("Ainda não há histórico de pesquisas para este usuário.")
            except Exception as historico_pesquisa_erro:
                st.info(
                    f"Histórico de pesquisas indisponível: {historico_pesquisa_erro}"
                )

            st.subheader("visualização Gráfica")
            tab1, tab2 = st.tabs(["📊 Gráficos", "📄 Dados Detalhados"])

            with tab1:
                st.caption(f"Exibindo {titulo_grafico}")
                dados_agrupados = (
                    tabela_final.groupby("bairro")["preco_m2"]
                    .median()
                    .sort_values(ascending=False)
                )

                if not filtro_bairros:
                    dados_grafico_exibir = dados_agrupados.head(15)
                else:
                    dados_grafico_exibir = dados_agrupados
                st.bar_chart(dados_grafico_exibir)

            with tab2:
                colunas_ocultar = {"id", "user_id", "criado_em"}
                colunas_exibir = [
                    col for col in tabela_final.columns if col not in colunas_ocultar
                ]
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
                        "fonte": st.column_config.TextColumn("Fonte"),
                        "link": st.column_config.LinkColumn("Link"),
                    },
                )

                csv_export = tabela_exibir.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Exportar CSV filtrado",
                    data=csv_export,
                    file_name="imoveis_filtrados.csv",
                    mime="text/csv",
                )

        else:
            st.warning("Nenhum dado encontrado para essa combinação de filtros.")
    else:
        st.info(
            "Ainda não há dados coletados para este estado. Aguarde a próxima coleta automática."
        )
except Exception as e:
    st.error(f"Erro ao consultar dados no Supabase: {e}")


# SEÇÃO DE COLETA MANUAL
st.divider()
col_coleta1, col_coleta2, col_coleta3 = st.columns([2, 1, 1])

with col_coleta1:
    st.subheader("⚙️ Gerenciamento de Coleta")

with col_coleta2:
    if st.button("🔄 Coletar Agora", use_container_width=True, key="btn_coletar_agora"):
        with st.spinner("🔄 Coletando dados..."):
            try:
                from scraping import scrape
                import math

                df = scrape(estado_selecionado, max_paginas=30)

                if df is not None and not df.empty:
                    df["estado"] = estado_selecionado.upper()

                    df["preco_num"] = df["preco"].apply(
                        lambda x: (
                            float(
                                x.replace("R$", "")
                                .replace(".", "")
                                .replace(",", ".")
                                .strip()
                            )
                            if x and x != "R$ 0"
                            else None
                        )
                    )

                    def calc_preco_m2(row):
                        try:
                            preco = row.get("preco_num")
                            m2 = row.get("m2")

                            if preco is None or m2 is None:
                                return None
                            if m2 <= 0 or preco <= 0:
                                return None

                            resultado = preco / m2

                            if math.isnan(resultado) or math.isinf(resultado):
                                return None

                            return round(resultado, 2)
                        except Exception:
                            return None

                    df["preco_m2"] = df.apply(calc_preco_m2, axis=1)

                    df["criado_em"] = datetime.now(timezone.utc).isoformat()
                    df["user_id"] = None

                    df = df.drop_duplicates(subset=["link"], keep="first")

                    def clean_value(val):
                        if val is None:
                            return None
                        try:
                            if isinstance(val, float):
                                if math.isnan(val) or math.isinf(val):
                                    return None
                        except (TypeError, ValueError):
                            pass
                        return val

                    for col in df.columns:
                        if df[col].dtype in ["float64", "float32"]:
                            df[col] = df[col].apply(clean_value)

                    dados = df.to_dict("records")

                    dados_limpos = []
                    for record in dados:
                        record_limpo = {}
                        for k, v in record.items():
                            if isinstance(v, float):
                                if math.isnan(v) or math.isinf(v):
                                    record_limpo[k] = None
                                else:
                                    record_limpo[k] = v
                            else:
                                record_limpo[k] = v
                        dados_limpos.append(record_limpo)

                    # ⚠️ Usa o client administrativo (service_role) para escrita
                    supabase_admin.table("imoveis").insert(dados_limpos).execute()

                    st.success(f"✅ {len(df)} imóveis coletados e salvos!")
                    st.rerun()
                else:
                    st.warning("⚠️ Nenhum dado coletado")
            except Exception as e:
                st.error(f"❌ Erro na coleta: {str(e)}")

with col_coleta3:
    if st.button("🗑️ Limpar Dados", use_container_width=True, key="btn_limpar_dados"):
        if st.session_state.get("confirm_delete"):
            try:
                # ⚠️ Usa o client administrativo (service_role) para escrita
                supabase_admin.table("imoveis").delete().eq(
                    "estado", estado_selecionado.upper()
                ).execute()
                st.success("✅ Dados deletados!")
                st.session_state["confirm_delete"] = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao deletar: {e}")
        else:
            st.warning("⚠️ Clique novamente para confirmar")
            st.session_state["confirm_delete"] = True

st.divider()
