
import pandas as pd
def calcular_preco_m2():
    pd.options.display.float_format = '{:,.2f}'.format

    df = pd.read_csv('dados.csv', sep= ';')

    df['preco_num'] = (
        df['preco']
            .str.replace('R$', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .astype(float)
    )
    df['preco_m2'] = df['preco_num'] / df['m2']
    df.to_csv('dados.csv', sep=';', encoding='utf-8', index=False)
