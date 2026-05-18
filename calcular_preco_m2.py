import pandas as pd


def calcular_preco_m2(df: pd.DataFrame) -> pd.DataFrame:
    pd.options.display.float_format = '{:,.2f}'.format

    df = df.copy()
    df['preco_num'] = (
        df['preco']
            .astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .astype(float)
    )
    df['preco_m2'] = df['preco_num'] / df['m2']
    return df
