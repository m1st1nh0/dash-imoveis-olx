# 📊 Dashboard Imobiliário OLX

Um painel interativo para análise de mercado imobiliário, desenvolvido com **Python**, **Streamlit** e técnicas de **Web Scraping**. O projeto coleta dados de anúncios em tempo real diretamente da OLX, armazena no **Supabase** e transforma informações brutas em insights visuais — permitindo comparar o preço do metro quadrado entre diferentes bairros e cidades de forma automatizada.

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-red) ![Supabase](https://img.shields.io/badge/Supabase-Database-green)

---

## 🎯 Objetivo

Facilitar a análise de preços de imóveis de forma automatizada. Em vez de navegar por dezenas de páginas manualmente, o usuário pode:

1. **Coletar** dados de qualquer estado brasileiro automaticamente.
2. **Agendar** scraping periódico com o scheduler integrado.
3. **Filtrar** resultados por cidade e selecionar bairros específicos para comparação.
4. **Visualizar** gráficos de preço médio por m², identificando rapidamente oportunidades e tendências de mercado.
5. **Persistir** os dados coletados no Supabase para histórico e análises futuras.

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia | Função |
|---|---|---|
| Coleta | `cloudscraper` | Contorna proteções anti-bot e realiza requisições HTTP |
| Parsing | `BeautifulSoup4` | Extrai preço, localização e m² do HTML |
| Análise | `pandas` | Limpeza, conversão de tipos e cálculo de métricas |
| Banco de Dados | `supabase` | Armazenamento persistente dos anúncios coletados |
| Frontend | `Streamlit` | Interface interativa e responsiva |
| Gráficos | `Plotly` | Gráficos dinâmicos e comparativos |
| Agendamento | `scraping_scheduler.py` | Automação periódica do scraping |

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

- **Python 3.9+** instalado
- Conta no **Supabase** (gratuita) com uma tabela configurada para os imóveis

### Passo a Passo

1. **Clone este repositório:**
   ```bash
   git clone https://github.com/m1st1nh0/dash-imoveis-olx.git
   cd dash-imoveis-olx
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente do Supabase:**

   Crie um arquivo `.env` na raiz do projeto (ou configure no Streamlit Secrets):
   ```env
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua-anon-key
   ```

4. **Execute a aplicação:**
   ```bash
   streamlit run main.py
   ```

5. **Acesse o Dashboard:**

   O Streamlit abrirá automaticamente uma aba no seu navegador em `http://localhost:8501`.

### Executar o Scraping Agendado (opcional)

Para rodar o scraping de forma automática e periódica, execute:
```bash
python scraping_scheduler.py
```

---

## 📊 Funcionalidades do Dashboard

- **🔍 Seletor de Estado:** Escolha a UF (PR, SP, RJ...) e o scraper busca até 100 páginas de anúncios.
- **📈 Comparador de Bairros:** Selecione bairros específicos para ver um gráfico lado a lado dos preços médios por m².
- **💡 KPIs em Tempo Real:** Métricas como "Preço Médio da Seleção" se atualizam instantaneamente conforme você filtra.
- **💾 Persistência de Dados:** Os dados são salvos localmente em `dados.csv` e enviados ao Supabase, evitando scraping redundante.
- **🕐 Agendamento Automático:** O scheduler permite coletar dados em intervalos regulares sem intervenção manual.

---

## 📂 Estrutura do Projeto

```
📂 dash-imoveis-olx/
├── 📄 main.py                   # Interface Streamlit, lógica de filtros e visualizações
├── 📄 scraping.py               # Módulo principal de coleta de dados na OLX
├── 📄 scraping_scheduler.py     # Agendador de scraping automático e periódico
├── 📄 calcular_preco_m2.py      # Script auxiliar de limpeza e cálculo de métricas
├── 📄 dados.csv                 # Cache local dos últimos dados coletados
├── 📄 requirements.txt          # Dependências do projeto
└── 📄 readME.md                 # Documentação do projeto
```

---

## ⚙️ Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `SUPABASE_URL` | URL do seu projeto no Supabase |
| `SUPABASE_KEY` | Chave anon/public do Supabase |

---

## ⚠️ Aviso Legal

Este projeto foi desenvolvido para fins de **estudo e portfólio** em Ciência de Dados e Desenvolvimento Web. O web scraping deve ser utilizado com responsabilidade, respeitando os termos de uso das plataformas e evitando sobrecarga nos servidores.

---

## 📬 Contato

Gostou do projeto? Vamos nos conectar!

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Lucas%20Schamposki-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/lucas-schamposki/)
[![GitHub](https://img.shields.io/badge/GitHub-m1st1nh0-black?style=flat&logo=github)](https://github.com/m1st1nh0)
