from scraping import scrape

df = scrape("pr", max_paginas=1)
print(df["fonte"].value_counts())
print(df.head(10).to_string())
