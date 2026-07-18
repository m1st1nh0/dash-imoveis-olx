import cloudscraper
from bs4 import BeautifulSoup
import re
import pandas as pd
import random
import time


def _format_brl(value):
    try:
        valor = float(value)
    except Exception:
        return "R$ 0"
    if valor <= 0:
        return "R$ 0"
    # Formata para pt-BR: 1.234.567,89
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _parse_m2(area_value):
    if area_value is None:
        return None
    try:
        area = float(str(area_value).replace(".", "").replace(",", "."))
        return area if area > 0 else None
    except Exception:
        return None


def _normalize_preco_text(preco_texto: str) -> str:
    if not preco_texto:
        return "R$ 0"
    texto = preco_texto.strip()
    if "confira" in texto.lower() or "sob consulta" in texto.lower():
        return "R$ 0"
    return texto


def scrape_olx(estado, max_paginas=100):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }

    scraper = cloudscraper.create_scraper()
    dic_produtos = {
        "nome": [],
        "preco": [],
        "m2": [],
        "cidade": [],
        "bairro": [],
        "link": [],
        "fonte": [],
    }

    for i in range(1, max_paginas + 1):
        url = f"https://www.olx.com.br/imoveis/venda/estado-{estado}?lis=home_body_search_bar_1001&o={i}"
        pagina_carregada = False
        tentativas = 0

        while not pagina_carregada and tentativas < 3:
            tentativas += 1
            try:
                response = scraper.get(url, headers=headers, timeout=20)

                if response.status_code != 200:
                    time.sleep(0.6 + random.random())
                    continue

                soup = BeautifulSoup(response.content, "html.parser")
                produtos = soup.select("section.olx-adcard")

                if not produtos:
                    time.sleep(0.6 + random.random())
                    continue

                pagina_carregada = True

                for produto in produtos:
                    try:
                        nome_tag = produto.select_one("h2.olx-adcard__title")
                        if not nome_tag:
                            continue
                        nome = nome_tag.get_text(" ", strip=True)

                        preco_tag = produto.select_one("h3.olx-adcard__price")
                        preco = (
                            preco_tag.get_text(" ", strip=True) if preco_tag else "R$ 0"
                        )
                        preco = _normalize_preco_text(preco)

                        area_tag = produto.select_one(
                            "div.olx-adcard__detail[aria-label*='metros']"
                        )
                        m2 = None
                        if area_tag:
                            area_label = area_tag.get("aria-label", "")
                            match = re.search(r"(\d+[.,]?\d*)", area_label)
                            if match:
                                try:
                                    m2 = float(match.group(1).replace(",", "."))
                                except Exception:
                                    m2 = None

                        localizacao_tag = produto.select_one("p.olx-adcard__location")
                        localizacao = (
                            localizacao_tag.get_text(" ", strip=True)
                            if localizacao_tag
                            else ""
                        )

                        cidade = "Não Informado"
                        bairro = "Não Informado"

                        if localizacao:
                            if "," in localizacao:
                                partes = [p.strip() for p in localizacao.split(",", 1)]
                                cidade = (
                                    partes[0] if len(partes) > 0 else "Não Informado"
                                )
                                bairro = (
                                    partes[1] if len(partes) > 1 else "Não Informado"
                                )
                            elif "-" in localizacao:
                                partes = [p.strip() for p in localizacao.split("-", 1)]
                                cidade = (
                                    partes[0] if len(partes) > 0 else "Não Informado"
                                )
                                bairro = (
                                    partes[1] if len(partes) > 1 else "Não Informado"
                                )
                            else:
                                cidade = localizacao.strip()

                        link_tag = produto.select_one("a.olx-adcard__link[href]")
                        link = link_tag.get("href", "").strip() if link_tag else ""

                        dic_produtos["nome"].append(nome)
                        dic_produtos["preco"].append(preco)
                        dic_produtos["m2"].append(m2)
                        dic_produtos["cidade"].append(cidade)
                        dic_produtos["bairro"].append(bairro)
                        dic_produtos["link"].append(link)
                        dic_produtos["fonte"].append("olx")

                    except Exception as e:
                        print(f"Erro ao ler produto OLX: {e}")
                        continue

            except Exception as e:
                print(f"Erro ao carregar página OLX {i}: {e}")
                time.sleep(0.6 + random.random())
                continue

        if not pagina_carregada:
            print(f"Fim das páginas OLX na página {i - 1}.")
            break

        time.sleep(0.4 + random.random() * 1.0)

    if len(dic_produtos["nome"]) > 0:
        return pd.DataFrame(dic_produtos)

    return None


def scrape_chaves(estado, max_paginas=100):
    scraper = cloudscraper.create_scraper()
    dic_produtos = {
        "nome": [],
        "preco": [],
        "m2": [],
        "cidade": [],
        "bairro": [],
        "link": [],
        "fonte": [],
    }

    pagina = 1
    total_paginas = None

    while True:
        url = (
            "https://www.chavesnamao.com.br/api/realestate/listing/items/"
            f"?level1=imoveis-a-venda&level2={estado}&pg={pagina}&server=0&viewport=desktop"
        )

        tentativas = 0
        sucesso = False
        while tentativas < 3 and not sucesso:
            tentativas += 1
            try:
                resp = scraper.get(url, timeout=20)
                if resp.status_code != 200:
                    time.sleep(0.6 + random.random())
                    continue
                data = resp.json()
                sucesso = True
            except Exception:
                time.sleep(0.6 + random.random())

        if not sucesso:
            break

        if total_paginas is None:
            total_paginas = data.get("metadata", {}).get("totalPages", max_paginas)
            total_paginas = min(total_paginas, max_paginas)

        itens = data.get("items", [])
        if not any(item.get("id") for item in itens):
            break

        for item in itens:
            if not item.get("id"):
                continue

            nome = item.get("title", "")
            raw_preco = item.get("prices", {}).get("rawPrice")
            preco = _format_brl(raw_preco)

            area = item.get("area", {})
            m2 = _parse_m2(area.get("useful") or area.get("total"))

            cidade = item.get("location", {}).get("city", {}).get("name", "")
            bairro = item.get("location", {}).get("neighborhood", {}).get("name", "")
            link = "https://www.chavesnamao.com.br" + item.get("url", "")

            dic_produtos["nome"].append(nome)
            dic_produtos["preco"].append(preco)
            dic_produtos["m2"].append(m2)
            dic_produtos["cidade"].append(cidade)
            dic_produtos["bairro"].append(bairro)
            dic_produtos["link"].append(link)
            dic_produtos["fonte"].append("chaves")

        pagina += 1
        if total_paginas is not None and pagina > total_paginas:
            break

        time.sleep(0.4 + random.random())

    if len(dic_produtos["nome"]) > 0:
        return pd.DataFrame(dic_produtos)

    return None


def scrape(estado, max_paginas=2):
    df_olx = scrape_olx(estado, max_paginas=max_paginas)
    df_chaves = scrape_chaves(estado, max_paginas=max_paginas)

    print("OLX linhas:", 0 if df_olx is None else len(df_olx))
    print("CHAVES linhas:", 0 if df_chaves is None else len(df_chaves))

    frames = []
    if df_olx is not None and not df_olx.empty:
        frames.append(df_olx)
    if df_chaves is not None and not df_chaves.empty:
        frames.append(df_chaves)

    if frames:
        return pd.concat(frames, ignore_index=True)

    return None
