from scraping import scrape_olx

df = scrape_olx("pr", max_paginas=1)

if df is None:
    print("OLX retornou None")
else:
    print("Total de linhas:", len(df))
    print(df.head(10).to_string())
    print(df["fonte"].value_counts(dropna=False))
