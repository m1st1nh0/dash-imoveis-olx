import cloudscraper
from bs4 import BeautifulSoup
import re
import pandas as pd
import math


def scrape(estado):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    scraper = cloudscraper.create_scraper()
    dic_produtos = {'nome': [], 'preco': [], 'm2': [], 'cidade': [], 'bairro': [], 'link': []}
    for i in range(1, 100):
        url = f'https://www.olx.com.br/imoveis/venda/estado-{estado}?lis=home_body_search_bar_1001&o={i}'






        try:
            response = scraper.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')

            produtos = soup.find_all('section', class_=re.compile('olx-adcard'))

            if not produtos:
                print(f"Fim das páginas encontradas na página {i - 1}.")
                break

            for produto in produtos:
                try:
                    #pegar nome

                    nome_tag = produto.find('h2', class_=re.compile('olx-adcard__title'))
                    if not nome_tag:
                        continue
                    nome = nome_tag.get_text().strip()

                    #pegar preço
                    preco_tag = (produto.find('h3', class_=re.compile('olx-adcard__price')))
                    if preco_tag:
                        preco = preco_tag.get_text().strip()
                    else:
                        preco = "0"

                    #pegar m²
                    m2_div = produto.find('div', attrs={'aria-label': re.compile('metros')})
                    if m2_div:
                        texto_m2 = m2_div.get('aria-label')
                        m2 = int(re.search(r'\d+', texto_m2).group())
                    else:
                        m2 = None

                    #pegar localização
                    localizacao_tag = (produto.find('p', class_=re.compile('location')))
                    localizacao = localizacao_tag.get_text().strip() if localizacao_tag else ""
                    if localizacao:
                        cidade_bairro = localizacao.split(',')
                        if len(cidade_bairro)>=2:
                            cidade = cidade_bairro[0]
                            bairro = cidade_bairro[1]
                        elif '-' in cidade_bairro:
                            partes = localizacao.split('-')
                            cidade = partes[0]
                            bairro = partes[1]
                        else:
                            cidade = localizacao
                            bairro = "Não Informado"
                    else:
                        cidade = "Não Informado"
                        bairro = "Não Informado"

                    #pegar link
                    link_tag = (produto.find('a',class_=re.compile('link')))
                    link = link_tag.get('href') if link_tag else ""

                    #adicionar a lista
                    dic_produtos['nome'].append(nome)
                    dic_produtos['preco'].append(preco)
                    dic_produtos['m2'].append(m2)
                    dic_produtos['cidade'].append(cidade)
                    dic_produtos['bairro'].append(bairro)
                    dic_produtos['link'].append(link)

                except Exception as e:
                    print(f"Erro ao ler o produto: {e}")
                    continue
        except Exception as e:
            print(f"Erro ao carregar página {i}: {e}")
            continue

    if len(dic_produtos['nome']) > 0:
        df = pd.DataFrame(dic_produtos)
        df.to_csv('dados.csv', encoding='utf-8', sep=';', index=False, quoting=1)
        return True

    return False















