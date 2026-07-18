import os
import sys
import re
import hashlib
from datetime import datetime, timezone
import pandas as pd
from supabase import create_client
from scraping import scrape

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Credenciais Supabase não configuradas!")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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


def safe_none(value):
    if pd.isna(value):
        return None
    return value


def extrair_numero_preco(preco_texto):
    if not preco_texto or preco_texto == "R$ 0":
        return None
    try:
        numero = float(
            preco_texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
        )
        return numero if numero > 0 else None
    except Exception:
        return None


def calcular_preco_m2(row):
    preco = row.get("preco_num")
    m2 = row.get("m2")

    if preco is not None and m2 is not None and m2 > 0:
        return round(preco / m2, 2)
    return None


def gerar_anuncio_uid(row):
    fonte = str(row.get("fonte") or "").strip().lower()
    link = str(row.get("link") or "").strip()

    if link:
        match = re.search(r"([0-9]{6,})", link)
        if match:
            return f"{fonte}_{match.group(1)}"

    base = f"{fonte}|{link}|{row.get('nome','')}|{row.get('cidade','')}|{row.get('bairro','')}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def processar_dados(df, estado):
    if df is None or df.empty:
        return None

    df = df.copy()

    df["estado"] = estado.upper()
    df["fonte"] = df["fonte"].astype(str).str.lower().str.strip()
    df["cidade"] = df["cidade"].fillna("Não Informado")
    df["bairro"] = df["bairro"].fillna("Não Informado")
    df["preco_num"] = df["preco"].apply(extrair_numero_preco)
    df["preco_m2"] = df.apply(calcular_preco_m2, axis=1)
    df["anuncio_uid"] = df.apply(gerar_anuncio_uid, axis=1)
    df["criado_em"] = datetime.now(timezone.utc).isoformat()

    df = df.drop_duplicates(subset=["anuncio_uid"], keep="first")
    df = df.where(pd.notnull(df), None)

    return df


def criar_coleta(estado, fonte, total_anuncios):
    payload = {
        "estado": estado.upper(),
        "fonte": fonte,
        "coletado_em": datetime.now(timezone.utc).isoformat(),
        "total_anuncios": int(total_anuncios),
        "observacao": "Coleta automática",
    }

    resposta = supabase.table("coletas").insert(payload).execute()
    return resposta.data[0]["id"]


def upsert_imoveis(df):
    registros = []

    for _, row in df.iterrows():
        registros.append(
            {
                "anuncio_uid": safe_none(row.get("anuncio_uid")),
                "titulo": safe_none(row.get("nome")),
                "cidade": safe_none(row.get("cidade")),
                "bairro": safe_none(row.get("bairro")),
                "estado": safe_none(row.get("estado")),
                "link": safe_none(row.get("link")),
                "fonte": safe_none(row.get("fonte")),
            }
        )

    supabase.table("imoveis").upsert(registros, on_conflict="anuncio_uid").execute()


def buscar_imoveis_por_uid(uids):
    resposta = (
        supabase.table("imoveis")
        .select("id, anuncio_uid")
        .in_("anuncio_uid", uids)
        .execute()
    )
    return {item["anuncio_uid"]: item["id"] for item in resposta.data}


def inserir_historico(df, coleta_id, mapa_ids):
    historico = []

    for _, row in df.iterrows():
        anuncio_uid = row.get("anuncio_uid")
        imovel_id = mapa_ids.get(anuncio_uid)

        if not imovel_id:
            continue

        historico.append(
            {
                "imovel_id": imovel_id,
                "coleta_id": coleta_id,
                "preco_texto": safe_none(row.get("preco")),
                "preco_num": safe_none(row.get("preco_num")),
                "m2": safe_none(row.get("m2")),
                "preco_m2": safe_none(row.get("preco_m2")),
                "cidade": safe_none(row.get("cidade")),
                "bairro": safe_none(row.get("bairro")),
                "estado": safe_none(row.get("estado")),
                "fonte": safe_none(row.get("fonte")),
                "criado_em": datetime.now(timezone.utc).isoformat(),
            }
        )

    if historico:
        supabase.table("historico_precos").upsert(
            historico, on_conflict="imovel_id,coleta_id"
        ).execute()


def coletar_estado(estado):
    try:
        print(f"🔄 Coletando dados para {estado.upper()}...")
        df = scrape(estado, max_paginas=50)

        if df is None or df.empty:
            print(f"⚠️ Nenhum dado coletado para {estado.upper()}")
            return False

        df = processar_dados(df, estado)

        if df is None or df.empty:
            print(f"⚠️ Dados processados vazios para {estado.upper()}")
            return False

        print(f"✅ {len(df)} imóveis processados para {estado.upper()}")

        fontes = (
            ",".join(sorted(df["fonte"].dropna().unique().tolist()))
            if "fonte" in df.columns
            else "desconhecida"
        )
        coleta_id = criar_coleta(estado, fontes, len(df))

        upsert_imoveis(df)

        mapa_ids = buscar_imoveis_por_uid(df["anuncio_uid"].dropna().unique().tolist())

        inserir_historico(df, coleta_id, mapa_ids)

        print(f"✅ Coleta {coleta_id} salva com histórico para {estado.upper()}")
        return True

    except Exception as e:
        print(f"❌ Erro ao coletar dados para {estado.upper()}: {e}")
        return False


def main():
    print("=" * 50)
    print(f"🚀 Iniciando coleta automática - {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    sucesso_count = 0
    erro_count = 0

    for estado in ESTADOS:
        if coletar_estado(estado):
            sucesso_count += 1
        else:
            erro_count += 1

        import time

        time.sleep(2)

    print("=" * 50)
    print("✅ Coleta finalizada!")
    print(f"   Sucesso: {sucesso_count}")
    print(f"   Erros: {erro_count}")
    print("=" * 50)


if __name__ == "__main__":
    main()
