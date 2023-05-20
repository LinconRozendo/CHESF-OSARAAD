'''
Arquivo com rotinas de apoio para json2dash.py na etapa de leitura de arquivos,
bem como ordenação e filtro.

**Observação:**

Achei esse link para um pacote de conversão:
>https://github.com/okfn/dataconverters/tree/master/dataconverters

>Por se tratar de um conversor genérico, me pareceu bem mais complicado.
'''

from typing import Union
import pandas as pd
import geopandas as gpd
from shapely import wkt

GeoGenericoTypes = Union[gpd.GeoDataFrame, pd.DataFrame, str]


def __validate_geometry_label(df, geometry_label):

    if geometry_label not in df.columns:
        print('(format_converters.py: __validate_geometry_label) Aviso:')
        print('df supostamente geográfico sem coluna geometry_label.')
    else:
        try:
            df[geometry_label] = df[geometry_label].apply(wkt.loads)
            df = gpd.GeoDataFrame(df, geometry=geometry_label)
            if(df.crs is None):
                df.crs = {'init': 'epsg:4618', 'no_defs': True}
        except:
            print('(format_converters.py:__validate_geometry_label) Aviso:')
            print('Não foi possível criar a coluna geometry de df.')

    return df


def filter_and_sort_df(
        df,
        filter_df=[],
        sort_values=[],
        ascending=[]):
    """
    Filtra e/ou ordena um dataframe pandas a partir de um uma ou mais colunas 
    enviadas pelo usuário.

    Args:

    * df (DataFrame)

        DataFrame com os dados.

    * filter_df (list, optional, default([]))

        Lista de query's para filtrar o DataFrame.

    * sort_values (list, optional, default([]))

        Ordena a tabela lida de acordo com a hierarquia de colunas enviadas.

    * ascending (list, optional, default([]))

        Trabalha em conjunto com `sort_values`. 

        Deve ter uma lista de bool do mesmo tamanho que estabelece a ordem que
        deve ser usada para ordenar cada coluna hierarquicamente.

    Retorna:

    * O Dataframe após as operações solicitadas.
    """

    if type(sort_values) != list:
        sort_values = [sort_values]

    if type(ascending) != list:
        ascending = [ascending]

    if (sort_values != []):
        df = df.sort_values(by=sort_values, ascending=ascending)

    if type(filter_df) != list:
        filter_df = [filter_df]

    if(filter_df != []):
        # vai me ajudar na hr que eu quiser pegar as x primeiras ou ultimas
        # linhas do df organizado
        if 'number_of_rows' not in df.columns:
            df['number_of_rows'] = [x for x in range(1, len(df)+1)]

        if len(filter_df) > 1:
            for query in filter_df:
                df = df.query(query)
                # cria uma nova listagem para referência
                df['number_of_rows'] = [x for x in range(1, len(df)+1)]

        elif filter_df != ['']:
            df = df.query(filter_df[0])

    return df


def read_geo_generico(
        file_path,
        output_format,
        encoding='utf-8',
        index_col=0,
        usecols=None,
        filter_df=[],
        sort_values=[],
        ascending=[],
        geometry_label='geometry') -> GeoGenericoTypes:
    """
    Lê um dataframe pandas a partir de um arquivo csv, excel, shp e json sendo 
    possível aplicar o filtro solicitado e ordenar.

    Args:

    * filename (str)

        Caminho do arquivo com os dados.

    * output_format (str)

        Formato desejado para exportação dos dados do arquivo enviado.

    * encoding (str, optional, default('utf-8'))

        Codificação de caracteres utilizada no arquivo enviado. 

    * index_col (int, optional, default(0))

        Seta a coluna representada pelo valor enviado como índice. 

    * usecols ([type], optional, default(None))

        DataFrame com apenas as colunas enviadas. 

    * filter_df (list, optional, default([]))

        Uma lista de querys para filtrar o DataFrame.

    * sort_values (list, optional, default([]))

        Organiza os valores de acordo com a hierarquia de colunas enviadas.

    * ascending (list, optional, default([]))

        Trabalha em conjunto com `sort_values`. 

        Deve ter uma lista de bool do mesmo tamanho que estabelece a ordem que
        deve ser usada para ordenar cada coluna hierarquicamente.

    * geometry_label (str, optional, default('geometry'))

        Nome da coluna do dataframe que contem os polígonos. 

    Raises:

    * Exception: Extensão inesperada

        Permitidos: csv, xls, xlsx, shp, json, kml.

    * Exception: output_format

        Permitidos: pandas, geopandas ou geojson.

    Retorna:

    * Um DataFrame ou uma string JSON conforme "output_format" e após as 
      operações solicitadas.

    """

    # obtém geo-dataframe df
    if(file_path.endswith('.csv')):
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            index_col=index_col,
            usecols=usecols
        )
        df = __validate_geometry_label(df, geometry_label)

    elif(file_path.endswith('.xls') or file_path.endswith('.xlsx')):
        df = pd.read_excel(
            open(file_path, 'rb'),
            # encoding=encoding, # a função read_excel n recebe esse parametro
            index_col=index_col,
            usecols=usecols
        )
        df = __validate_geometry_label(df, geometry_label)

    elif(file_path.endswith('.shp') or file_path.endswith('.json')):
        df = gpd.read_file(file_path)

    elif(file_path.endswith('.kml')):
        gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
        # the KML driver has to be activated
        df = gpd.read_file(filename=file_path, driver='KML')

    else:
        raise Exception("Extensão inesperada: csv, xls, xlsx, shp, json, kml.")

    df = filter_and_sort_df(
        df,
        filter_df=filter_df,
        sort_values=sort_values,
        ascending=ascending
    )

    # converte geo-dataframe para o formato desejado
    if(output_format.lower() == 'pandas'):
        out = pd.DataFrame(df, copy=True)
    elif(output_format.lower() == 'geopandas'):
        out = df.copy()
    elif(output_format.lower() == 'geojson'):
        out = df.to_json()
    else:
        raise Exception("output_format: pandas, geopandas ou geojson.")

    return out


def read_data_generico(
        file_path,
        encoding='utf-8',
        index_col=0,
        usecols=[],
        filter_df=[],
        sort_values=[],
        ascending=[]):
    """
    Lê um dataframe pandas a partir de um arquivo feather, csv, excel e json 
    sendo possível aplicar o filtro solicitado e ordenar.

    Args:

    * filename (str)

        Caminho do arquivo com os dados.

    * encoding (str, optional, default('utf-8'))

        Codificação de caracteres utilizada no arquivo enviado. 

    * index_col (int, optional, default(0))

        Seta a coluna representada pelo valor enviado como índice. 

    * usecols ([type], optional, default(None))

        DataFrame com apenas as colunas enviadas. 

    * filter_df (list, optional, default([]))

        Uma lista de querys para filtrar o DataFrame.

    * sort_values (list, optional, default([]))

        Organiza os valores de acordo com a hierarquia de colunas enviadas.

    * ascending (list, optional, default([]))

        Trabalha em conjunto com `sort_values`. 

        Deve ter uma lista de bool do mesmo tamanho que estabelece a ordem que
        deve ser usada para ordenar cada coluna hierarquicamente.

    Raises:

    * Exception: Extensão inesperada

        Permitidos: feather, csv, txt, xls, xlsx, json, kml.

    Retorna:

    * Um DataFrame após as operações solicitadas.
    """

    if(file_path.endswith('.feather')):
        df = pd.read_feather(
            file_path,
            columns=usecols if len(usecols) > 0 else None
        )

    elif(file_path.endswith('.csv') or file_path.endswith('.txt')):
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            index_col=index_col,
            usecols=usecols if len(usecols) > 0 else None
        )

    elif(file_path.endswith('.xls') or file_path.endswith('.xlsx')):
        df = pd.read_excel(
            open(file_path, 'rb'),
            encoding=encoding,
            index_col=index_col,
            usecols=usecols if len(usecols) > 0 else None
        )

    elif(file_path.endswith('.shp') or file_path.endswith('.json')):
        df = pd.read_json(file_path, encoding=encoding)

    elif(file_path.endswith('.kml')):
        gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
        # the KML driver has to be activated
        df = gpd.read_file(filename=file_path, driver='KML')

    else:
        raise Exception(
            "Extensão inesperada: feather, csv, txt, xls, xlsx, json, kml.")

    df.columns = [x.strip() for x in df.columns]

    df = filter_and_sort_df(
        df,
        filter_df=filter_df,
        sort_values=sort_values,
        ascending=ascending
    )

    return df
