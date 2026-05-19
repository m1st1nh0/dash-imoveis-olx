import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from supabase import create_client

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from calcular_preco_m2 import calcular_preco_m2
from scraping import scrape


ESTADOS = [
    "ac", "al", "ap", "am", "ba", "ce", "df", "es", "go", "ma", "mt", "ms", "mg", "pa", "pb",
    "pr", "pe", "pi", "rj", "rn", "rs", "ro", "rr", "sc", "sp", "se", "to"
]


def _prepare_dataframe(df: pd.DataFrame, estado: str, coleta_ts: str) -> pd.DataFrame:
    df = calcular_preco_m2(df)
    df["estado"] = estado
    df["user_id"] = None
    df["criado_em"] = coleta_ts

    # Tipos numéricos coerentes com o banco
    df["m2"] = pd.to_numeric(df["m2"], errors="coerce").round(0).astype("Int64")
    df["preco_num"] = pd.to_numeric(df["preco_num"], errors="coerce")
    df["preco_m2"] = pd.to_numeric(df["preco_m2"], errors="coerce")

    # Remove NaN/Inf de forma confiável para JSON (compatível com pandas 3.x)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.astype(object)
    df = df.where(pd.notna(df), None)

    # Remove duplicatas no mesmo ciclo (mesmo link/fonte)
    df = df.drop_duplicates(subset=["link", "fonte"])

    return df


def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórios.")

    supabase = create_client(supabase_url, supabase_key)
    max_paginas = int(os.getenv("MAX_PAGES", "100"))

    coleta_ts = datetime.now(timezone.utc).isoformat()

    for estado in ESTADOS:
        print(f"Coletando dados de {estado.upper()}...")
        df = scrape(estado, max_paginas=max_paginas)

        if df is None or df.empty:
            print(f"Nenhum dado encontrado para {estado.upper()}.")
            continue

        df = _prepare_dataframe(df, estado, coleta_ts)

        # Snapshot atual (tabela imoveis)
        supabase.table("imoveis").delete().is_("user_id", "null").eq("estado", estado).execute()
        supabase.table("imoveis").insert(df.to_dict(orient="records")).execute()

        # Histórico completo
        supabase.table("imoveis_historico").insert(df.to_dict(orient="records")).execute()

        resumo_pesquisa = {
            "user_id": None,
            "estado": estado,
            "criado_em": coleta_ts,
            "qtd_anuncios": int(len(df)),
            "mediana_preco_m2": float(df["preco_m2"].median()) if "preco_m2" in df.columns else None,
            "mediana_preco_total": float(df["preco_num"].median()) if "preco_num" in df.columns else None,
        }
        supabase.table("pesquisas").insert(resumo_pesquisa).execute()

        time.sleep(2)


if __name__ == "__main__":
    main()
