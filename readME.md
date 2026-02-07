
# 📊 Dashboard Imobiliário OLX

Um painel interativo para análise de mercado imobiliário, desenvolvido com **Python**, **Streamlit** e técnicas de **Web Scraping**. O projeto coleta dados de anúncios em tempo real e transforma informações brutas em insights visuais, permitindo comparar o preço do metro quadrado entre diferentes bairros e cidades.

![Status](https://img.shields.io/badge/Status-Concluído-green) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-red)

## 🎯 Objetivo
Facilitar a análise de preços de imóveis de forma automatizada. Em vez de navegar por dezenas de páginas manualmente, o usuário pode:
1.  **Coletar** dados de qualquer estado brasileiro automaticamente.
2.  **Filtrar** resultados por cidade e selecionar bairros específicos para comparação.
3.  **Visualizar** gráficos de preço médio por m², identificando rapidamente oportunidades e tendências de mercado.

## 🛠️ Tecnologias Utilizadas
O projeto integra extração, processamento e visualização de dados:

-   **Coleta de Dados (ETL):**
    -   `cloudscraper`: Para contornar proteções anti-bot e realizar requisições HTTP seguras.
    -   `BeautifulSoup`: Para navegar no HTML e extrair informações (preço, localização, m²).
-   **Análise e Limpeza:**
    -   `pandas`: Tratamento de strings, conversão de tipos de dados e cálculo de métricas.
-   **Frontend / Dashboard:**
    -   `Streamlit`: Interface interativa e responsiva.
    -   `Plotly`: Gráficos dinâmicos para comparação visual.

## 🚀 Como Executar o Projeto

### Pré-requisitos
Certifique-se de ter o **Python** instalado em sua máquina.

### Passo a Passo
1.  **Clone este repositório:**
    ```bash
    git clone  https://github.com/m1st1nh0/dash-imoveis-olx.git
    cd dash-imoveis-olx
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Execute a aplicação:**
    ```bash
    streamlit run main.py
    ```

4.  **Acesse o Dashboard:**
    O Streamlit abrirá automaticamente uma aba no seu navegador (geralmente em `http://localhost:8501`).

## 📊 Funcionalidades do Dashboard
-   **🔍 Seletor de Estado:** Escolha a UF (PR, SP, RJ...) e o scraper busca até 100 páginas de anúncios.
-   **📈 Comparador de Bairros:** Selecione bairros específicos para ver um gráfico lado a lado dos preços médios.
-   **💡 KPIs em Tempo Real:** Métricas como "Preço Médio da Seleção" se atualizam instantaneamente conforme você filtra.
-   **💾 Persistência de Dados:** Os dados coletados são salvos localmente (`dados.csv`), evitando a necessidade de rodar o scraping toda vez que abrir o app.

## 📂 Estrutura do Projeto
```
📂 /
├── 📄 main.py               # Arquivo principal (Interface Streamlit e Lógica de Filtros)
├── 📄 scraping.py           # Módulo responsável pela coleta de dados na OLX
├── 📄 calcular_preco_m2.py  # Script auxiliar de limpeza e cálculo de métricas
├── 📄 requirements.txt      # Lista de bibliotecas necessárias
└── 📄 README.md             # Documentação do projeto
```

## ⚠️ Aviso Legal
Este projeto foi desenvolvido para fins de **estudo e portfólio** em Ciência de Dados. O web scraping deve ser utilizado com responsabilidade, respeitando os termos de uso das plataformas e evitando sobrecarga nos servidores.

---
### 📬 Contato
Gostou do projeto? Vamos nos conectar!

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Perfil-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/lucas-schamposki/)
```
