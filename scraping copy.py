import cloudscraper

dic_produtos = {'nome': [], 'preco': [], 'm2': [], 'cidade': [], 'bairro': [], 'link': []}

def scrape(estado):
    for i in range(1,100):
        url = f'https://www.chavesnamao.com.br/api/realestate/listing/items/?level1=imoveis-a-venda&level2={estado}&pg={i}&quebra=%5B2483404%5D&server=0&viewport=desktop'
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url)
        resp.raise_for_status()

        data = resp.json()

        # 2) Itens estão em data["items"]
        for item in data.get("items", []):
            # pula objetos que não são anúncio (ex.: {"pagination": true} ou {"banner": true})
            if not item.get("id"):
                continue

            nome = item.get("title", "")
            preco = item.get("prices", {}).get("rawPrice")
            m2 = item.get("area", {}).get("useful") or item.get("area", {}).get("total")
            cidade = item.get("location", {}).get("city", {}).get("name", "")
            bairro = item.get("location", {}).get("neighborhood", {}).get("name", "")
            link = "https://www.chavesnamao.com.br" + item.get("url", "")

            dic_produtos["nome"].append(nome)
            dic_produtos["preco"].append(preco)
            dic_produtos["m2"].append(m2)
            dic_produtos["cidade"].append(cidade)
            dic_produtos["bairro"].append(bairro)
            dic_produtos["link"].append(link)

        print(dic_produtos)