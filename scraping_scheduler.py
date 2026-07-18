import os
import sys
from datetime import datetime, timezone, timedelta
import pandas as pd
from supabase import create_client
from scraping import scrape

# Configurar credenciais do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Credenciais Supabase não configuradas!")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Lista de estados para coletar
ESTADOS = [
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


def processar_dados(df, estado):
    """Processa e prepara dados para o Supabase"""
    if df is None or df.empty:
        return None

    df["estado"] = estado.upper()
    df["preco_num"] = df["preco"].apply(lambda x: extrair_numero_preco(x))
    df["preco_m2"] = df.apply(lambda row: calcular_preco_m2(row), axis=1)
    df["criado_em"] = datetime.now(timezone.utc).isoformat()
    df["user_id"] = None  # Dados públicos
    df["fonte"] = df["fonte"].str.lower()

    # Remover duplicatas
    df = df.drop_duplicates(subset=["link"], keep="first")

    return df


def extrair_numero_preco(preco_texto):
    """Extrai número do texto de preço"""
    if not preco_texto or preco_texto == "R$ 0":
        return None
    try:
        numero = float(
            preco_texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
        )
        return numero if numero > 0 else None
    except:
        return None


def calcular_preco_m2(row):
    """Calcula preço por m²"""
    preco = row.get("preco_num")
    m2 = row.get("m2")

    if preco and m2 and m2 > 0:
        return round(preco / m2, 2)
    return None


def salvar_no_supabase(df, estado):
    """Salva dados no Supabase"""
    try:
        # ✅ CORREÇÃO: substituir NaN por None antes de serializar para JSON
        df = df.where(pd.notnull(df), None)

        # Converter para dicionários
        dados = df.to_dict("records")

        # Inserir dados
        resposta = supabase.table("imoveis").insert(dados).execute()

        # Registrar na tabela de pesquisas
        registro_pesquisa = {
            "estado": estado.upper(),
            "qtd_anuncios": len(df),
            # ✅ CORREÇÃO: protege .median() contra NaN
            "mediana_preco_m2": (
                float(df["preco_m2"].median())
                if "preco_m2" in df.columns and df["preco_m2"].notna().any()
                else None
            ),
            "mediana_preco_total": (
                float(df["preco_num"].median())
                if "preco_num" in df.columns and df["preco_num"].notna().any()
                else None
            ),
            "criado_em": datetime.now(timezone.utc).isoformat(),
            "user_id": None,
            "fonte": df["fonte"].unique().tolist() if "fonte" in df.columns else [],
        }
        supabase.table("pesquisas").insert([registro_pesquisa]).execute()

        return True
    except Exception as e:
        print(f"❌ Erro ao salvar dados para {estado}: {e}")
        return False


def coletar_estado(estado):
    """Coleta dados de um estado específico"""
    try:
        print(f"🔄 Coletando dados para {estado.upper()}...")
        df = scrape(estado, max_paginas=50)  # Reduzido para não sobrecarregar

        if df is None or df.empty:
            print(f"⚠️  Nenhum dado coletado para {estado.upper()}")
            return False

        print(f"✅ {len(df)} imóveis coletados para {estado.upper()}")

        # Processar dados
        df = processar_dados(df, estado)

        # Salvar no Supabase
        if salvar_no_supabase(df, estado):
            print(f"✅ Dados salvos no Supabase para {estado.upper()}")
            return True

        return False
    except Exception as e:
        print(f"❌ Erro ao coletar dados para {estado}: {e}")
        return False


def main():
    """Função principal"""
    print("=" * 50)
    print(f"🚀 Iniciando coleta automática - {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    sucesso_count = 0
    erro_count = 0

    # Coletar dados de cada estado
    for estado in ESTADOS:
        if coletar_estado(estado):
            sucesso_count += 1
        else:
            erro_count += 1

        # Pequeno delay entre requisições para não sobrecarregar
        import time

        time.sleep(2)

    print("=" * 50)
    print(f"✅ Coleta finalizada!")
    print(f"   Sucesso: {sucesso_count}")
    print(f"   Erros: {erro_count}")
    print("=" * 50)


if __name__ == "__main__":
    main()
